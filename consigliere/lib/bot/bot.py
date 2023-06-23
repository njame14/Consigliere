#Consigliere
import os
import discord
from dotenv import load_dotenv
from glob import glob
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound
from consigliere.data.db.database import ApplicationDatabase

PREFIX = "$"
OWNER_IDS = [145989557484126209, 145984332568199169]

#Bot is based on discord.ext.commands.Bot(BotBase) to add additional functionality
#super() refers to BotBase
class Bot(BotBase):
    def __init__(self):
        print('Initializing...')
        self.PREFIX = PREFIX
        self.ready = False

        #database.autosave(self.scheduler)
        super().__init__(
            intents = discord.Intents.all(),
            command_prefix=PREFIX, 
            owner_ids=OWNER_IDS)
        
        self.database = ApplicationDatabase(self.guilds)
        self.database.create_tables()
        

    async def cog_setup(self):
        for cog in COGS:
            try:
                await self.load_extension(f"lib.cogs.{cog}")
                print(f"{cog} cog loaded.")
            except Exception as e:
                print(f'Failed to load extension: {e}')
        try:
            bot.get_cog('MusicCog').database = lambda: self.database
        except Exception as e:
            print(f'Failed to pass database context to music logic: {e}')
            
        
    async def run(self, version):
        self.VERSION = version
        print('Loading cogs...')
        await self.cog_setup()

        print("Fetching token...")
        load_dotenv()
        self.TOKEN = os.getenv('DISCORD_TOKEN')

        print("Initialization Completed. Bot running...")
        await super().start(self.TOKEN, reconnect=True)

    async def on_connect(self):
        print("Bot connected")

    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_error(self,err,*args,**kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
        await self.ctx("An error occured.")
        raise

    async def on_command_error(self, ctx, exc):
        if isinstance(exc, CommandNotFound):
            await ctx.send("Command not found.")
        elif hasattr(exc,"original"):
            raise exc.original
        else:
            raise exc
    
    async def on_ready(self):
        if not self.ready:
            self.ready = True
            print('Bot is ready!')

        else:
            print("Bot reconnected")
            

COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]
 
bot = Bot() #Creates an instance of the bot class
