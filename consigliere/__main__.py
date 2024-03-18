from bots.bot import Bot
import asyncio

VERSION = "0.1"
bot = Bot() #Creates an instance of the bot class
asyncio.run(bot.start(VERSION))