import disnake
import wavelink
from disnake.ext import commands
from utils import Config
from wavelink.ext import spotify

intents = disnake.Intents.all()


class MyBot(commands.Bot):
    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.node: wavelink.Node = None
        self.loop.create_task(self.start_nodes())

    async def on_ready(self):
        print("я хуею")

    async def start_nodes(self) -> None:
        """Подключение и инициализация узлов лавалинк"""
        await self.wait_until_ready()

        nodes = {"bot": self,
                 "host": Config.LAVA_HOST,
                 "port": Config.LAVA_PORT,
                 "password": Config.LAVA_PASS,
                 }

        if Config.SPOTIFY_CLIENT_ID:
            nodes["spotify_client"] = spotify.SpotifyClient(client_id=Config.SPOTIFY_CLIENT_ID,
                                                            client_secret=Config.SPOTIFY_SECRET)

        node: wavelink.Node = await wavelink.NodePool.create_node(**nodes)
        self.node = node
        print(f"[dismusic] INFO - Created node: {node.identifier}")


bot = MyBot(command_prefix="^^",
            intents=intents,
            test_guilds=Config.GUILD_IDS,
            sync_commands=True)

bot.load_extension("cogs.music")
bot.run(Config.TOKEN)
