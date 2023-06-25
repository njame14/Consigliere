from lib.bot.bot import bot
import asyncio

VERSION = "0.1"
asyncio.run(bot.start(VERSION))