# Main imports
import logging
import logging.handlers
import asyncpg
import os

# Discord imports
import discord
import aiosqlite
from aiosqlite import Connection
from discord.ext import commands, tasks
from discord import Embed, Message

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
		await addcogs(self)
		self.log.info("Added cogs...")
		
async def addcogs(bot):
	await bot.add_cog(Ping(bot))
	await bot.add_cog(Verify(bot))
	await bot.add_cog(Greeting(bot))

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

class Greeting(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.index = 0
		self.checknations.start()

	def cog_unload(self):
        	self.checknations.cancel()

	# Check for new arrivals every second
	@tasks.loop(seconds = 1.0)
	async def checknations(self):
		self.index += 1
		self.bot.log.info(f"CHECKED NATIONS! {self.index}")
	
	@checknations.before_loop
	async def before_checknations(self):
		self.bot.log.info("Awaiting in Greeting Cog...")
		await self.bot.wait_until_ready()
	

class Verify(commands.Cog):
	verifyTemplate = '''
		To verify your Nation States account, reply to this message
		with the code found at this personalized link.
	'''
	def __init__(self, bot):
		self.bot = bot

	def isreply(self, message, rid):
		print("Checking...", message.id, rid, message.reference)
		ret = False
		if not message.reference is None and message.reference.resolved:
			print("Refid", message.reference.message_id)
			ret = rid == message.reference.message_id
		print("Checked...",ret)
		return ret

	def createLink(self, user):
		# For the token, sign the username with the private key
		token = self.bot.signlambda(f'{user}')
		print("TOKEN:",token)
		embed = Embed(url="https://scythiamarrow.org",title="Verify")
		return token, embed

	def processCode(self, user, token, code):
		print("PROCESS!", user, token, code)
		return "Verification error, sorry T-T"

	@commands.command()
	async def verify(self, ctx, *, member: discord.Member = None):
		self.bot.log.info(f'Called verify by {ctx.author}...')
		# First, check if the author is already verified
		author = ctx.author
		is_verified = await self.bot.db.execute(
			f"SELECT * FROM verify WHERE name=\'{author}\';")
		print(is_verified)
		token, embed = self.createLink(author)
		sentid = await ctx.send(self.verifyTemplate, embed=embed)
		checkL = lambda x: self.isreply(x,rid=sentid.id)
		codemessage = await self.bot.wait_for('message',check=checkL)
		code = codemessage.content
		await ctx.send(self.processCode(author, token, code))

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
