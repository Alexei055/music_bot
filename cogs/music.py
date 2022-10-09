import asyncio
import random

from disnake import SelectOption

from main import MyBot
from utils import *
from disnake.ext import commands


class TrackNotFound(commands.CommandError):
    """Не найдена песня"""
    pass


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.user_timer = {}
        self.user_all_time = {}

    async def cog_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception) -> None:
        if isinstance(error, TrackNotFound):
            return await inter.send(f"{inter.author.mention} не найден трек по вашему запросу")

        await super().cog_slash_command_error(inter, error)
        raise error

    async def timeout_check(self, channel_id, guild_id):
        await asyncio.sleep(PLAYER_TIMEOUT)
        guild = self.bot.get_guild(guild_id)
        if player := self.bot.node.get_player(guild):
            channel = self.bot.get_channel(channel_id)
            if len(channel.members) == 1:
                await player.destroy()

    @commands.Cog.listener("on_button_click")
    async def on_player_button(self, interaction: disnake.MessageInteraction):
        if not interaction.data.custom_id.startswith("musicplayer_"):
            return

        await self.player_controller(interaction, interaction.data.custom_id)

    @commands.Cog.listener()
    async def on_voice_state_update(self,
                                    member: disnake.Member,
                                    before: disnake.VoiceState,
                                    after: disnake.VoiceState):
        if before.channel == after.channel:
            return
        if player := self.bot.node.get_player(member.guild):
            if member.id == self.bot.user.id and after.channel is None:
                await player.destroy()
                return

            channel = self.bot.get_channel(player.channel.id)

            if len(channel.members) == 1:
                await self.timeout_check(player.channel.id, member.guild.id)
                return

            if member == player.dj and after.channel is None:
                for mem in channel.members:
                    if not mem.bot:
                        player.dj = mem
                        return

    @commands.Cog.listener("on_message")
    async def on_music_channel(self, message: disnake.Message):
        if message.channel.id == Config.MUSIC_CHANNEL and not message.author.bot:
            player: Player = self.bot.node.get_player(message.guild)
            if player is None or not player.is_connected():
                player = await self.connect(message, message.author)
            await message.delete()
            await player.add_tracks(message, message.content)

    @commands.Cog.listener("on_wavelink_track_exception")
    @commands.Cog.listener("on_wavelink_track_end")
    @commands.Cog.listener("on_wavelink_track_stuck")
    async def on_player_stop(self, player: Player, *args, **kwargs):
        if player.loop_mode:
            await player.play(player.looped_track)
            return
        player.update_embed.cancel()
        await player.do_next()

    @commands.Cog.listener("on_dropdown")
    async def on_dropdown_player(self, inter: disnake.MessageInteraction):
        player: Player = self.bot.node.get_player(inter.guild)
        selected_value = int(inter.values[0])
        await inter.response.edit_message(f"`{player.queue._queue[selected_value].title}` удален из очереди",
                                          components=[])
        del player.queue._queue[selected_value]
        await player.invoke_controller()

    async def player_controller(self, interaction: disnake.MessageInteraction, control: str):
        player: Player = self.bot.node.get_player(interaction.guild)
        await interaction.response.defer()
        if player:
            if interaction.message.id == player.message_controller.id:
                if player and (interaction.user.id == player.dj.id or player.dj in interaction.user.roles):
                    match control:

                        case PlayerControls.PLAY:
                            await player.set_paused()

                        case PlayerControls.PAUSE:
                            await player.set_paused()

                        case PlayerControls.STOP:
                            await player.destroy()
                            await interaction.edit_original_message(components=[])

                        case PlayerControls.SKIP:
                            await player.stop()

                        case PlayerControls.SHUFFLE:
                            if player.queue.qsize() < 3:
                                return await interaction.channel.send("Мало песен в очереди для перемешивания")
                            random.shuffle(player.queue._queue)
                            await interaction.channel.send("Очередь была перемешана")

                        case PlayerControls.LOOP_MODE:
                            if player.loop_mode:
                                player.loop_mode = False
                                await interaction.channel.send("Режим повтора выключен")
                            else:
                                player.loop_mode = True
                                player.looped_track = player.track
                                await interaction.channel.send("Режим повтора включен")

    async def connect(self,
                      inter: disnake.CommandInteraction | disnake.Message,
                      user: disnake.Member,
                      channel: disnake.VoiceChannel = None):
        dj = inter.guild.get_role(Config.DJ_ROLE_ID) if Config.DJ_ROLE_ID else user
        player = Player(inter=inter, dj=dj)

        channel = getattr(user.voice, 'channel', channel)

        if channel is None:
            await inter.channel.send(f"{user} вы должны находиться в голосовом канале")
        else:
            await channel.connect(cls=player)
            return player

    @commands.slash_command(name="play", )
    async def play(self,
                   inter: disnake.CommandInteraction,
                   search: str = commands.Param(description="URL или название трека", )):
        player: Player = self.bot.node.get_player(inter.guild)
        if player is None or not player.is_connected():
            player = await self.connect(inter, inter.user)
        await player.add_tracks(inter, search)

    @commands.slash_command(name="setup",
                            description="Привязывает плеер к каналу",
                            default_member_permissions=8, )
    async def setup_channel(self,
                            inter: disnake.CommandInteraction,
                            channel: disnake.TextChannel = commands.Param(name="канал",
                                                                          description="Выберите канал для привязки плеера")):
        await inter.response.defer()
        Config.MUSIC_CHANNEL = channel.id
        with open('config.json', 'r') as f:
            config = json.load(f)
        with open('config.json', 'w') as f:
            config["MUSIC_CHANNEL"] = channel.id
            json.dump(config, f)
        await inter.send(f"Теперь канал {channel.mention} выступает в качестве плеера, "
                         f"туда можно писать название треков и кидать ссылки на них, и бот будет их воспроизводить. "
                         f"Слеш команды работают в обычном режиме")

    @commands.slash_command(name="set_dj_role",
                            description="Устанавливает роль dj",
                            default_member_permissions=8, )
    async def set_dj_role(self, inter: disnake.CommandInteraction, role: disnake.Role):
        await inter.response.defer()
        Config.DJ_ROLE_ID = role.id
        with open('config.json', 'r') as f:
            config = json.load(f)
        with open('config.json', 'w') as f:
            config["DJ_ROLE_ID"] = role.id
            json.dump(config, f)
        await inter.send(f"{role.mention} установлена в качестве DJ роли")

    @commands.slash_command(name="seek",
                            description="перемотать трек на определенное место")
    async def seek(self,
                   inter: disnake.CommandInteraction,
                   minutes: commands.Range[1, ...] = commands.Param(name="минута",
                                                                    description="На какую минуту перемотать",
                                                                    default=None),
                   seconds: commands.Range[0, 60] = commands.Param(name="секунда",
                                                                   description="На какую секунду перемотать", )):
        player: Player = self.bot.node.get_player(inter.guild)
        minutes: int
        seconds: int
        if player and player.is_playing():
            position = seconds + (minutes * 60000) if minutes else seconds * 1000
            human_position = seconds + (minutes * 60) if minutes else seconds
            if position > (player.track.length * 60000):
                await inter.response.send_message(f"Трек столько не длится", delete_after=15)
                return
            await player.seek(position)
            await inter.response.send_message(
                f"Трек перемотан на {time.strftime('%M:%S', time.gmtime(human_position))}")
        else:
            await inter.response.send_message(f"Музыка сейчас не играет", delete_after=15)

    @commands.slash_command(name="volume",
                            description="Настройка громкости")
    async def set_volume(self,
                         inter: disnake.CommandInteraction,
                         volume: commands.Range[0, 100] = commands.Param(name="громкость",
                                                                         description="На сколько процентов установить громкость воспроизведения")):
        player: Player = self.bot.node.get_player(inter.guild)
        volume: int
        if player and player.is_playing():
            await player.set_volume(volume)
            await inter.response.send_message(f"Громкость плеера установлена на {volume}%")
        else:
            await inter.response.send_message(f"Музыка сейчас не играет", delete_after=15)

    @commands.slash_command(name="remove",
                            description="Удалить определенный трек из очереди")
    async def remove_track(self, inter: disnake.CommandInteraction):
        player: Player = self.bot.node.get_player(inter.guild)
        if player and player.is_playing():
            qsize = player.queue.qsize()
            if qsize > 0:
                select_menu = disnake.ui.Select(
                    placeholder=f"Всего треков: {qsize}    Отображается с 1 по {qsize}",
                    options=[SelectOption(emoji="🎵",
                                          label=f"{ind + 1} - {tr.title[:95]}",
                                          value=f"{ind}",
                                          description=f"{time.strftime('%M:%S', time.gmtime(tr.length))}") for ind, tr
                             in tuple(enumerate(player.queue._queue))[:25]
                             ])
                await inter.response.send_message("Выберите какой трек хотите удалить", components=[select_menu])
            else:
                await inter.response.send_message("Очередь пуста")
        else:
            await inter.response.send_message(f"Музыка сейчас не играет", delete_after=15)

    @commands.slash_command(name="move",
                            description="Переместить бота в другой голосовой канал")
    async def move_bot(self, inter: disnake.CommandInteraction, channel: disnake.VoiceChannel):
        player: Player = self.bot.node.get_player(inter.guild)
        if player:
            if inter.author.id == player.dj.id or player.dj in inter.author.roles:
                await player.move_to(channel)
                await inter.response.send_message(f"Я переместился в {channel.mention}")
            else:
                await inter.response.send_message(f"Вы не являетесь диджеем этого бота")
        else:
            await inter.response.send_message(f"Я сейчас не играю музыку")

    @commands.slash_command(name="qclear",
                            description="Очищает очередь")
    async def clear_queue(self, inter: disnake.CommandInteraction):
        player: Player = self.bot.node.get_player(inter.guild)
        if player:
            if inter.author.id == player.dj.id or player.dj in inter.author.roles:
                player.queue = asyncio.Queue()
                await inter.response.send_message(f"Очередь была очищена")
            else:
                await inter.response.send_message(f"Вы не являетесь диджеем этого бота")
        else:
            await inter.response.send_message(f"Я сейчас не играю музыку")


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
