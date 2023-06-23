import discord
from discord.ext.commands import Cog
from discord.ext import commands
import utils.musicUtils
import asyncio
import requests
import time

# # Dictionary to store server-specific voice channels and queues
# voice_channels = {}
# voice_queues = {}

class MusicCog(Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        
    #Checks if user is in a voice channel when requesting bot to play music 
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                #raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.author.voice.channel.connect()

    # @commands.command()
    # async def play(self, ctx, url):
    #     voice_channel = ctx.message.author.voice.channel

    #     if not voice_channel:
    #         await ctx.send("You are not connected to a voice channel.")
    #         return

    #     if voice_channel.guild.id in voice_channels:
    #         if voice_channels[voice_channel.guild.id].is_playing():
    #             voice_queues[voice_channel.guild.id].append(url)
    #             await ctx.send("Added to queue.")
    #             return
    #     else:
    #         voice_channels[voice_channel.guild.id] = await voice_channel.connect()
    #         voice_queues[voice_channel.guild.id] = []

    #     voice_channels[voice_channel.guild.id].play(discord.FFmpegPCMAudio(url))
    #     await ctx.send("Playing...")

    # @ensure_voice
    # async def play(self, ctx, url):
    #     server_id = str(ctx.guild.id)
    #     requester = str(ctx.message.author)
    #     voice_channel = ctx.message.author.voice.channel
    #     db = self.db

    #     #Voice check ensured by @ensure-voice

    #     db
    #     c.execute("SELECT voice_channel_id, queue FROM server_data WHERE server_id=?", (server_id,))
    #     row = c.fetchone()

    #     if row and row[0] and bot.get_channel(int(row[0])):
    #         if bot.get_channel(int(row[0])).guild.voice_client.is_playing():
    #             new_queue = row[1] + ',' + url if row[1] else url
    #             c.execute("UPDATE server_data SET queue=? WHERE server_id=?", (new_queue, server_id))
    #             await ctx.send("Added to queue.")
    #             return
    #     else:
    #         voice_channel_id = str(voice_channel.id)
    #         queue = url
    #         c.execute("INSERT OR REPLACE INTO server_data (server_id, voice_channel_id, queue) VALUES (?, ?, ?)",
    #                 (server_id, voice_channel_id, queue))
    #         c.commit()

    #     voice_client = await voice_channel.connect()
    #     voice_client.play(discord.FFmpegPCMAudio(url))
    #     await ctx.send("Playing...")

    # @commands.command()
    # async def stop(self, ctx):
    #     voice_channel = ctx.message.author.voice.channel

    #     if voice_channel.guild.id in voice_channels:
    #         voice_channels[voice_channel.guild.id].stop()
    #         voice_queues[voice_channel.guild.id] = []
    #         await voice_channels[voice_channel.guild.id].disconnect()
    #         del voice_channels[voice_channel.guild.id]
    #         await ctx.send("Stopped and disconnected.")
    #     else:
    #         await ctx.send("The bot is not connected to a voice channel in this server.")

    # @commands.command()
    # async def queue(self, ctx, url):
    #     voice_channel = ctx.message.author.voice.channel

    #     if voice_channel.guild.id in voice_channels:
    #         voice_queues[voice_channel.guild.id].append(url)
    #         await ctx.send("Added to queue.")
    #     else:
    #         await ctx.send("The bot is not connected to a voice channel in this server.")

    # @commands.command()
    # async def skip(self, ctx):
    #     voice_channel = ctx.message.author.voice.channel

    #     if voice_channel.guild.id in voice_channels:
    #         if voice_channels[voice_channel.guild.id].is_playing():
    #             voice_channels[voice_channel.guild.id].stop()
    #             if len(voice_queues[voice_channel.guild.id]) > 0:
    #                 next_url = voice_queues[voice_channel.guild.id].pop(0)
    #                 voice_channels[voice_channel.guild.id].play(discord.FFmpegPCMAudio(next_url))
    #                 await ctx.send("Skipping to the next track...")
    #             else:
    #                 await ctx.send("No more tracks in the queue.")
    #         else:
    #             await ctx.send("No track is currently playing.")
    #     else:
    #         await ctx.send("The bot is not connected to a voice channel in this server.")

    @Cog.listener()
    async def on_ready(self):
        print("MusicCog loaded successfully.")

async def setup(bot):
   await bot.add_cog(MusicCog(bot))
   