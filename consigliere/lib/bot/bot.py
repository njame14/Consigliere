#Consigliere
import os
import discord
from dotenv import load_dotenv
from glob import glob
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound
from consigliere.data.db.database import ApplicationDatabase

PREFIX = "$"
OWNER_IDS = [145989557484126209]
COGS = [path.split("\\")[-1][:-3] for path in glob("consigliere/lib/cogs/*.py")]
COGS.remove("__init__")

#Bot is based on discord.ext.commands.Bot(BotBase) to add additional functionality
#super() refers to BotBase
class Bot(BotBase):
    def __init__(self):
        print('Initializing Bot...')

        # Initialize the database
        try:
            self.database = ApplicationDatabase()
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise e  # or handle it as you see fit

        self.PREFIX = PREFIX
        self.ready = False
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix=PREFIX, 
            owner_ids=OWNER_IDS
        )
        
    async def cog_setup(self):
        for cog in COGS:
            try:
                await self.load_extension(f"lib.cogs.{cog}")
            except Exception as e:
                print(f'Failed to load extension: {e}')
        
    async def start(self, version):
        self.VERSION = version
        print('Loading cogs...')
        await self.cog_setup()

        print("Fetching token...")
        load_dotenv()
        self.TOKEN = os.getenv('DISCORD_TOKEN')

        await super().start(self.TOKEN, reconnect=True)

    async def on_connect(self):
        print("Bot connected")

    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_error(self,err,*args,**kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
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
            print('Populating server table')
            try:
                self.add_guilds(self.guilds)
            except Exception as e:
                print('Failed to populate server table')
                raise SystemExit
            self.ready = True
            print("Initialization Completed.")
            print('Bot is command ready!')

        else:
            print("Bot reconnected")

    def add_guilds(self, guilds):
            session = self.database.Session()
            context = self.database.context
            servers = session.query(context.Server)
            guilds_list = list(guilds)

            # Update existing guild names
            #If the server is already in the database, update it's name
            serversToUpdate = servers.filter(any(context.Server.id == key for key in guilds)).all()
            for server in serversToUpdate:
                if server.name != guilds[server.id].name:
                    server.name = guilds[server.id].name

            #Delete guilds that are no longer connected to bot
            servers.filter(context.Server.id not in guilds_list).delete()

            #Mark all existing guilds as inactive
            servers.update({context.Server.is_voiceActive: 0})

            #Get the guild IDs that don't exist in servers
            existing_guild_ids = set([server.id for server in servers])
            guildsToAdd = [guild_id for guild_id in guilds_list if guild_id not in existing_guild_ids]
            # Add new guilds
            newServers = []
            for guild in guildsToAdd:
                # Example: Create a new Server object and add it to the session
                newServers.append(context.Server(id=guild.id, name=guild.name, is_voiceActive=0))    
            
            session.add_all(newServers)
            session.commit()
 
bot = Bot() #Creates an instance of the bot class
