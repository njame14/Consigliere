import discord
from discord.ext.commands import Cog
from discord.ext import commands
from gtts import gTTS 
import os

class TTSCog(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tts(self, ctx):
        message = ctx.message.content[5:]
        tts = gTTS(message)
        tts.save("tts.mp3")
        #Check if author is in a voice channel
        if(ctx.author.voice.channel is None):
            await ctx.send("❌ You are not connected to a voice channel.")
            return
        #Check if bot is in a voice channel
        if(ctx.voice_client is None):
            #Join
            await ctx.author.voice.channel.connect()
        else:
            #Move
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        ctx.voice_client.play(discord.FFmpegPCMAudio("tts.mp3"))
        #await ctx.voice_client.disconnect()

    @Cog.listener()
    async def on_ready(self):
        print("TTSCog loaded successfully.")

async def setup(bot):
   await bot.add_cog(TTSCog(bot))