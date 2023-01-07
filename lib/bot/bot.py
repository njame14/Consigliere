#Consigliere
import os
from dotenv import load_dotenv
from glob import glob
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound
from discord.ext import commands

from ..db import db


PREFIX = "$"
OWNER_IDS = [145989557484126209, 145984332568199169]

#Bot is based on discord.ext.commands.Bot(BotBase) to add additional functionality
#super() refers to BotBase
class Bot(BotBase):
    def __init__(self):
        print('Initializing...')
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()
        
        db.autosave(self.scheduler)
        super().__init__(
            intents = discord.Intents.all(),
            command_prefix=PREFIX, 
            owner_ids=OWNER_IDS)

    async def setup(self):
        for cog in COGS:
            try:
                await self.load_extension(f"lib.cogs.{cog}")
                print(f"{cog} cog loaded.")
            except Exception as e:
                print(f'Failed to load extension: {e}')
            
        
    async def run(self, version):
        self.VERSION = version

        print('Loading cogs...')
        await self.setup()

        print("Fetching token...")
        load_dotenv()
        self.TOKEN = os.getenv('DISCORD_TOKEN')

        print("Bot running...")
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
            self.get_guild(948281049018957864)
            self.scheduler.start()
            print('Bot is ready!')

        else:
            print("Bot reconnected")
            

COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]
 
bot = Bot() #Creates an instance of the bot class
