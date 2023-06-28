from consigliere.lib.cogs.utils import musicUtils
from discord.ext.commands import Cog
from discord.ext.commands.context import Context
from discord.voice_client import VoiceClient
import discord.ext.commands as commands

class MusicCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.database
        self.context = bot.database.context

        session = self.db.Session()
        session.query(self.context.MusicData).delete()
        session.commit()
        
    #Checks if user is in a voice channel when requesting bot to play music 
    async def ensure_voice(self, ctx : Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise
            return
        elif ctx.voice_client.channel == ctx.author.voice.channel:
            return
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.author.voice.channel.connect()
            return

    @commands.command()
    async def play(self, ctx : Context, url):
        await self.ensure_voice(ctx)
        server_id = ctx.guild.id
        requester = ctx.message.author
        voice_channel = ctx.message.author.voice.channel
        session = self.db.Session()

        if musicUtils.is_valid_url(url) is False:
            return await ctx.send("That is not a valid URL.")
        
        try:
            queue = session.query(self.context.MusicData).filter(self.context.MusicData.server_id == server_id).order_by(self.context.MusicData.queue_pos).all()
            positon = 0
            new_song = self.context.MusicData
            if len(queue) == 0:
                new_song = self.context.MusicData(
                    server_id=server_id, 
                    requester_id=requester.id,
                    url=url,
                    queue_pos=1)
            else:
                #Find Queue Position
                positon = max(queue, key=lambda obj: obj.queue_pos).queue_pos + 1
                new_song = self.context.MusicData(
                    server_id=server_id, 
                    requester_id=requester.id,
                    url=url,
                    queue_pos=positon)
            session.add(new_song)
            session.commit()
        except Exception as e:
            print(e)
        
        queue = session.query(self.context.MusicData).filter(self.context.MusicData.server_id == server_id).all()
        if(ctx.voice_client is None):
            raise
        if(ctx.voice_client is not None and ctx.voice_client.is_playing()):
            await ctx.send(f'Added to queue. {positon}/{len(queue)}.')
            return
        player = await musicUtils.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: self.play_next(ctx, new_song))   # Set the callback function for when the player finishes
        await ctx.send(f"Now Playing {ctx.voice_client.source.title}.")

        #Logic to retrieve the next song from the music table and play it
        async def play_next(self, ctx: Context, new_song: self.context.MusicData):
            await ctx.send(f"Entered AutoPlay: Now Playing {ctx.voice_client.source.title}.")
            server_id = ctx.guild.id
            session = self.db.Session()
            try:
                session.delete(new_song)
                next_song_url = session.query(self.context.MusicData).filter(self.context.MusicData.server_id == server_id).order_by(self.context.MusicData.queue_pos).first().url
                if next_song_url:
                    player = await musicUtils.YTDLSource.from_url(next_song_url, loop=self.bot.loop, stream=True)
                    if(ctx.voice_client.is_playing() is False):
                        ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))  # Set the callback function for when the player finishes
                        await ctx.send("Playing next song...")
                    return
                else:
                    # No more songs in the queue, do something (e.g., stop playback, send a message, etc.)
                    await ctx.send("No more songs in the queue.")
            except Exception as e:
                print(e)


    # @commands.before_invoke(ensure_voice)
    # @commands.command()
    # async def stop(self, ctx):
    #     voice_channel = ctx.message.author.voice.channel

    #     result = self.db.Session().query(self.context.Server).filter(self.context.Server.id == ctx.guild.id).first()
        
    #     if result is None:
    #         raise Exception("Server not found.")
        
    #     if voice_channel.guild.id in voice_channels:
    #         voice_channels[voice_channel.guild.id].stop()
    #         voice_queues[voice_channel.guild.id] = []
    #         await voice_channels[voice_channel.guild.id].disconnect()
    #         del voice_channels[voice_channel.guild.id]
    #         await ctx.send("Stopped and disconnected.")
    #     else:
    #         await ctx.send("The bot is not connected to a voice channel in this server.")
    @commands.command()
    async def stop(self, ctx : Context):
        await self.ensure_voice(ctx)
        if ctx.voice_client and ctx.voice_client.is_playing():
            session = self.db.Session()
            #Remove all music data related to server in ctx
            session.query(self.context.MusicData).filter(self.context.MusicData.server_id == ctx.guild.id).delete()
            session.commit()
            await ctx.voice_client.disconnect()
            await ctx.send("Cya bozo!")
            

    @commands.before_invoke(ensure_voice)
    @commands.command()
    async def skip(self, ctx : Context):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await self.play_next(ctx)
            await ctx.send("Skipped to the next song.")
        else:
            await ctx.send("No song is currently playing.")
    

    # @commands.command()
    # async def queue(self, ctx, url):
    #     voice_channel = ctx.message.author.voice.channel

    #     if voice_channel.guild.id in voice_channels:
    #         voice_queues[voice_channel.guild.id].append(url)
    #         await ctx.send("Added to queue.")
    #     else:
    #         await ctx.send("The bot is not connected to a voice channel in this server.")


    @Cog.listener()
    async def on_ready(self):
        print("MusicCog loaded successfully.")

async def setup(bot):
   await bot.add_cog(MusicCog(bot))
   