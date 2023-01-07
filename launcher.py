from lib.bot import bot
import asyncio

VERSION = "0.1"
asyncio.run(bot.bot.run(VERSION))