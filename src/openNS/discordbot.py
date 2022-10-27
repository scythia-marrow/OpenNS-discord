# Main imports
import logging
import logging.handlers
import asyncpg
import os

# Discord imports
import discord
import aiosqlite
from aiosqlite import Connection
from discord.ext import commands

# Following the guide from:
# https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py

class OpenNSDiscord(commands.Bot):
	def __init__(self, dbfile, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.log = logging.getLogger('discord')
		self.dbfile = dbfile

	async def setup_hook(self):
		self.db = await aiosqlite.connect(self.dbfile)
		self.log.info("Connected to Database...")
		

class Ping(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx, *, member: discord.Member = None):
		await ctx.send("pong")

class Verify(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx, *, member: discord.Member = None):
		self.bot.log.error("Called ping...")
		await ctx.send("pong")

async def addcogs(bot):
	await bot.add_cog(Ping(bot))
	bot.log.info("Added cog...")

def initbot(database):
	handler = logging.handlers.RotatingFileHandler(
		filename='openNS.log',
		encoding='utf-8',
		maxBytes= 32 * 1024 * 1024, # 32 MiB
	)
	dt_fmt = '%Y-%m-%d %H:%M:%S'
	formatter = logging.Formatter(
		'[{asctime}] [{levelname:<8}] {name}: {message}',
		dt_fmt,
		style="{")
	handler.setFormatter(formatter)
	discord.utils.setup_logging(handler = handler, root = False)

	# The intents for openNS are simple
	intents = discord.Intents.default()
	intents.message_content = True
	intents.reactions = True

	# Discord changed recently to not need command prefixes
	bot = OpenNSDiscord(
		dbfile=database,
		command_prefix="",
		intents = intents,
		log_handler=handler)
	return bot
