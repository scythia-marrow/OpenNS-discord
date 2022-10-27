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
from discord import Embed

# Following the guide from:
# https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py

class OpenNSDiscord(commands.Bot):
	def __init__(self, dbfile, signlambda, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.log = logging.getLogger('discord')
		self.signlambda = signlambda
		self.dbfile = dbfile

	async def setup_hook(self):
		self.db = await aiosqlite.connect(self.dbfile)
		self.log.info("Connected to Database...")
		

class Ping(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx, *, member: discord.Member = None):
		self.bot.log.info("Called ping...")
		message = Embed(
			url="https://scythiamarrow.org",
			title="clicktest")
		sign = str(self.bot.signlambda("Sign test"),'utf-8')
		await ctx.send(f'Hi there! Sign is {sign}',embed=message)

class Verify(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def verify(self, ctx, *, member: discord.Member = None):
		self.bot.log.info(f'Called verify by {ctx.author}...')
		# First, check if the author is already verified
		author = ctx.author
		is_verified = await self.bot.db.execute(
			f"SELECT * FROM openNSverify WHERE name=\'{author}\';")
		print(is_verified)
		await ctx.send("pong")

async def addcogs(bot):
	await bot.add_cog(Ping(bot))
	await bot.add_cog(Verify(bot))
	bot.log.info("Added cogs...")

def initbot(database, signlambda):
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
		signlambda=signlambda,
		command_prefix="",
		intents = intents,
		log_handler=handler)
	return bot
