import discord
from discord.ext.commands import Cog
from discord.ext import commands
import youtube_dl
import asyncio
import requests

class InvalidURL(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(self, cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a youtube playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


class MusicCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playlists = {}
        self.players = {}

    @commands.command()
    async def join(self, ctx):
        channel = ctx.author.voice.channel

        if(ctx.voice_client is None):
            await ctx.author.voice.channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

    @commands.command()
    async def move(self, ctx):
        channel = ctx.author.voice.channel

        if(ctx.voice_client is None):
            await ctx.author.voice.channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

    @commands.command()
    async def nowplaying(self,ctx):
        if ctx.voice_client is None:
            await ctx.send("❌ No player is running on this server")
            return
        
        await ctx.send (f"Current Song: {self.players[ctx.message.guild.id].title}")

    @commands.before_invoke(ensure_voice)
    @commands.command()
    async def play(self, ctx, url):
        try:
            await self.check_url(url)
        except InvalidURL as e:
            await ctx.send(f"❌ {e.message} ")
            return
        
        server = ctx.message.guild.id
        player = await YTDLSource.from_url(url, loop=self.bot.loop,  stream=True)
        self.players[server] = player
        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else self.bot.loop.create_task(self.play_next(ctx)))
        if server in self.playlists: #lists return false if empty
            if self.playlists[server] > 1: 
                await ctx.send(f"1/{len(self.playlists[server])} ▶️ Now Playing: {player.title}")
                return
        await ctx.send(f"▶️ Now Playing: {player.title}")

    @commands.command()
    async def pause(self, ctx):
        server = ctx.message.guild.id
        if server in self.players:
            ctx.voice_client.pause()
            await ctx.send("⏸ Player paused")
        else:
            await ctx.send("❌ No player is running on this server")

    @commands.command()
    async def resume(self, ctx):
        server = ctx.message.guild.id
        if server in self.players:
            ctx.voice_client.resume()
            await ctx.send("▶️ Player resumed")
        else:
            await ctx.send("❌ No player is running on this server")

    @commands.command()
    async def stop(self, ctx):
        server = ctx.message.guild.id
        if server in self.players:
            ctx.voice_client.stop()
            await ctx.send("🛑  Player stopped")
            self.players[server] = None
            self.playlists[server] = None
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("❌ No player is running on this server")

    @commands.command()
    async def skip(self, ctx):
        server = ctx.message.guild.id
        if server in self.players:
            ctx.voice_client.stop()
            await ctx.send("➡️ Skipping current song")
            self.bot.loop.create_task(self.play_next(ctx))
        else:
            await ctx.send("❌ No player is running on this server")

    @commands.command()
    async def queue(self, ctx, url):
        server = ctx.message.guild.id
        if server not in self.playlists:
            self.playlists[server] = []
        self.playlists[server].append(url)
        await ctx.send(f"✅ Added to queue! Position in queue {len(self.playlists[server])}")
    
    @commands.before_invoke(ensure_voice)
    async def play_next(self, ctx):
        server = ctx.guild.id
        if server in self.players:
            if self.playlists[server]:
                url = self.playlists[server][0]
                self.playlists[server].pop(0)
                player = await YTDLSource.from_url(url, loop=self.bot.loop,  stream=True)
                self.players[server] = player
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else self.bot.loop.create_task(self.play_next_song(server),ctx))
                if len(self.playlists[server]) > 1: #lists return false if empty
                    await ctx.send(f"1/{len(self.playlists[server])} ▶️ Now Playing: {player.title}")
                    return
                await ctx.send(f"▶️ Now Playing: {player.title}")

    
    async def check_url(self, url):
        try:
            

		    #Get Url
            get = requests.get(url)
            
            # if the request succeeds 
            if get.status_code == 200:
                if "Video unavailable" in get.text:
                    raise InvalidURL("No video media found.")
                return True
            else:
                raise InvalidURL("URL could not be reached.")

        #Exception
        except requests.exceptions.RequestException as e:
            # print URL with Errs
            raise InvalidURL("Invalid URL")

    @Cog.listener()
    async def on_ready(self):
        print("MusicCog ready.")

async def setup(bot):
   await bot.add_cog(MusicCog(bot))
   