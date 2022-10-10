import disnake
import wavelink
from disnake.ext import commands
from utils import Config

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

        node: wavelink.Node = await wavelink.NodePool.create_node(bot=self,
                                                                  host=Config.LAVA_HOST,
                                                                  port=Config.LAVA_PORT,
                                                                  password=Config.LAVA_PASS,
                                                                  )
        self.node = node
        print(f"[dismusic] INFO - Created node: {node.identifier}")


bot = MyBot(command_prefix="^^",
            intents=intents,
            test_guilds=Config.GUILD_IDS,
            sync_commands=True)

bot.load_extension("cogs.music")
bot.run(Config.TOKEN)
