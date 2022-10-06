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
                                                                  host="127.0.0.1",
                                                                  port=2333,
                                                                  password="admin",
                                                                  )
        self.node = node
        print(f"[dismusic] INFO - Created node: {node.identifier}")


bot = MyBot(command_prefix="^^",
            intents=intents,
            test_guilds=[262289366041362432, 439415430998786061, 634712809518923787],
            sync_commands=True)

bot.load_extension("cogs.music")
bot.run(Config.TOKEN)