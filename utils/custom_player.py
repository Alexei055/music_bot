import asyncio
import time
import async_timeout
import disnake
import wavelink
from disnake.ext import tasks, commands

from utils import PlayerControls, CONTROLLER_BUTTON, ControllerEmoji, SECONDS_FOR_UPDATE_PLAYER_MESSAGE, \
    TRACK_POSITION_EMBED_EMOJI, TRACK_LEFT_EMOJI, URL_REG, MUSIC_EMBED_GIF, PLAYER_TIMEOUT, Config


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.inter: disnake.MessageInteraction | disnake.Message = kwargs.get('inter', None)
        self.dj: disnake.Member | disnake.Role = kwargs.get('dj', None)
        self.bot: commands.Bot = kwargs.get('bot', None)
        self.message_controller: disnake.Message | None = None
        self.message_controller_id: int = 0
        self.queue = asyncio.Queue()

        self.waiting = False
        self.loop_mode = False
        self.looped_track = None

    async def destroy(self) -> None:
        self.queue = None
        self.loop_mode = False
        self.update_embed.cancel()
        await self.stop()
        await self.disconnect()
        await self.message_controller.edit(components=[])

    async def do_next(self) -> None:
        if self.is_playing() or self.waiting:
            return
        try:
            self.waiting = True
            with async_timeout.timeout(PLAYER_TIMEOUT):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            return await self.destroy()

        await self.play(track)
        self.waiting = False
        await self.invoke_controller()

    async def invoke_controller(self):
        qsize = self.queue.qsize()

        components = CONTROLLER_BUTTON
        components[0].custom_id = PlayerControls.PAUSE
        components[0].emoji = ControllerEmoji.PAUSE_EMOJI

        content = '```Список очереди:\n' + '\n'.join(
            [f'{ind + 1}. {tr.title} ● {tr.requester.display_name}' for ind, tr in
             tuple(enumerate(self.queue._queue))[:15]]) + '```' if qsize > 0 else None

        try:
            message = await self.inter.channel.fetch_message(self.message_controller_id)
            await self.message_controller.edit(content=content,
                                               embed=self.build_embed())
            self.message_controller = message
        except:
            if Config.MUSIC_CHANNEL:
                channel = self.bot.get_channel(Config.MUSIC_CHANNEL)
                self.message_controller = await channel.send(content=content,
                                                             embed=self.build_embed(),
                                                             components=components)

            else:
                if isinstance(self.inter, disnake.Message):
                    self.message_controller = await self.inter.channel.send(content=content,
                                                                            embed=self.build_embed(),
                                                                            components=components)
                else:
                    self.message_controller = await self.inter.edit_original_message(content=content,
                                                                                     embed=self.build_embed(),
                                                                                     components=components)
            self.message_controller_id = self.message_controller.id

        if not self.update_embed.is_running():
            self.update_embed.start()

    async def set_paused(self) -> None:
        components = CONTROLLER_BUTTON
        if self.is_paused():
            components[0].custom_id = PlayerControls.PAUSE
            components[0].emoji = ControllerEmoji.PAUSE_EMOJI
            await self.resume()
        else:
            components[0].custom_id = PlayerControls.PLAY
            components[0].emoji = ControllerEmoji.PLAY_EMOJI
            await self.pause()
        await self.message_controller.edit(components=components)

    # TODO:
    #   [x] настройка громкости
    #   [ ] воспроизведение музыки с других площадок помимо ютуба
    #   [x] функция на удаление определенного трека
    #   [x] перемотка на определенный таймер песни
    #   [x] смена канала по команде
    #   [ ] фильтры музыки
    #   [ ] кастом плейлисты

    async def add_tracks(self, inter: disnake.CommandInteraction | disnake.Message, search: str):
        search = search.strip('<>')
        if not URL_REG.match(search):
            search = f'ytsearch:{search}'

        try:
            tracks = await self.node.get_tracks(cls=wavelink.YouTubeTrack, query=search)
        except:
            tracks = await self.node.get_playlist(cls=wavelink.YouTubePlaylist, identifier=search)

        if not tracks:
            if isinstance(self.inter, disnake.Message):
                await self.inter.channel.send("Не найдено песен по вашему запросу")
            else:
                await self.inter.edit_original_message("Не найдено песен по вашему запросу")
            return

        if isinstance(tracks, wavelink.YouTubePlaylist):
            for track in tracks.tracks:
                if isinstance(self.inter, disnake.Message):
                    track.requester = self.inter.author
                else:
                    track.requester = self.inter.user
                await self.queue.put(track)
            embed = disnake.Embed(
                description=f'\nПлейлист **[{tracks.name}]({search})** добавлен в очередь\n'
                            f'Количество песен: {len(tracks.tracks)}\n')
            if isinstance(self.inter, disnake.Message):
                await self.inter.channel.send(embed=embed)
            else:
                await self.inter.edit_original_message(embed=embed)

        else:
            track = tracks[0]
            if isinstance(self.inter, disnake.Message):
                track.requester = self.inter.author
            else:
                track.requester = self.inter.user
            embed = disnake.Embed(
                description=f"**[{track.title}]({track.uri})** добавлена в очередь • {track.requester.mention}")
            if isinstance(self.inter, disnake.Message):
                await self.inter.channel.send(embed=embed)
            else:
                await self.inter.edit_original_message(embed=embed)
            await self.queue.put(track)

        self.inter = inter

        if not self.is_playing():
            await self.do_next()

    @tasks.loop(seconds=SECONDS_FOR_UPDATE_PLAYER_MESSAGE)
    async def update_embed(self):
        await self.message_controller.edit(embed=self.build_embed())

    def build_embed(self) -> disnake.Embed | None:
        track = self.track
        if not track:
            return
        qsize = self.queue.qsize()
        embed = disnake.Embed(title=f"{track.title}", url=track.uri, colour=0xff3f00)
        embed.set_author(name=track.author, url=track.uri, icon_url=MUSIC_EMBED_GIF)
        embed.set_thumbnail(track.thumb)
        embed.set_footer(text=f"Запросил: {track.requester.name} | В очереди: {qsize}")
        t_cur = self.position
        t_max = track.length
        pos = int(t_cur // (t_max / 20))

        if track.is_stream():
            embed.description = f"\n[∞:∞] {TRACK_POSITION_EMBED_EMOJI * 20} [∞:∞]"
        else:
            embed.description = f"\n\n[{time.strftime('%M:%S', time.gmtime(t_cur))}] {TRACK_POSITION_EMBED_EMOJI * pos}" \
                                f"{TRACK_LEFT_EMOJI * (20 - pos)} [{time.strftime('%M:%S', time.gmtime(t_max))}]"
        return embed
