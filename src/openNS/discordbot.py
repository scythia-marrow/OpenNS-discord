# Main imports
import logging
import logging.handlers
import asyncpg
import os
import urllib
import time

# Discord imports
import discord
import aiosqlite
from aiosqlite import Connection
from discord.ext import commands, tasks
from discord import Embed

# Nationstates imports
import nationstates

# Internal imports
from openNS.ping import Ping
from openNS.verify import Verify
from openNS.greet import Greet
from openNS.telegram import Telegram

class OpenNSDiscord(commands.Bot):
	def __init__(self, dbfile, signlambda, useragent, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.log = logging.getLogger('discord')
		self.signlambda = signlambda
		self.dbfile = dbfile
		self.api = nationstates.Nationstates(useragent)
	
	# Helper functions for components
	def timestamp(self): return int(time.time())

	def telegramEmbed(self, tonation, template = None):
		urlbase = "https://www.nationstates.net/page=compose_telegram"
		urlto = f"?tgto={tonation}"
		url = urlbase + urlto
		if not template == None: url = url + "&" + template
		return Embed(url = url, title = "Send Telegram")

	# Async helper functions for components
	async def templateEmbed(self, author, tonation):
		# Get the template from the database
		query = f'''
			SELECT head,sign FROM telegramtemplate
			WHERE name='{author}'
		'''
		cursor = await self.db.execute(query)
		result = await cursor.fetchone()
		# URLify the template
		head, sign = "",""
		if not result == None:
			head, sign = [urllib.parse.quote(x) for x in result]
		# Add a few newlines between the header and signature
		template = head + "%0A%0A%0A" + sign
		urltemplate = f"message={template}"
		embed = self.telegramEmbed(tonation, template=urltemplate)
		# Return the result
		return embed

	async def isVerified(self, author, nation=None):
		qpre = "SELECT * FROM verify"
		qnat = f" AND nation='{nation}'" if not nation == None else ""
		query = qpre + f" WHERE name='{author}'" + qnat
		verified = await self.db.execute(query)
		rows = await verified.fetchall()
		if len(rows) > 0: return True
		return False

	# Basic bot maintainence tasks
	async def setup_hook(self):
		# Connect to the database
		self.db = await aiosqlite.connect(self.dbfile)
		self.log.info("Connected to Database...")
		# Add cogs
		await addcogs(self)
		self.log.info("Added cogs...")
		
	#TODO: EFFICIENCY. Execute database queries every 60 seconds by default
	# @tasks.loop(seconds = 60.0)

# Helper function to add all cogs to a bot TODO: FUNCTION. Add options.
async def addcogs(bot):
	await bot.add_cog(Ping(bot))
	await bot.add_cog(Verify(bot))
	await bot.add_cog(Greet(bot))
	await bot.add_cog(Telegram(bot))

def initbot(database, signlambda, useragent):
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
	
	# Ensure the command prefix is actually the bot mention
	async def prefix(bot, message):
		return bot.user.mention
	
	# Do the thingy
	bot = OpenNSDiscord(
		dbfile=database,
		signlambda=signlambda,
		useragent=useragent,
		command_prefix = prefix,
		strip_after_prefix = True,
		intents = intents,
		log_handler=handler)
	return bot
