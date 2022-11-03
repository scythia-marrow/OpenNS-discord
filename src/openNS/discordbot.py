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

# Nationstates imports
import nationstates

class OpenNSDiscord(commands.Bot):
	def __init__(self, dbfile, signlambda, useragent, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.log = logging.getLogger('discord')
		self.signlambda = signlambda
		self.dbfile = dbfile
		self.api = nationstates.Nationstates(useragent)

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
		To verify your Nation States nation, reply to this message with the code found at this personalized link.
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
		urlbase = "https://www.nationstates.net/page=verify_login"
		urltoken = f"?token={token}"
		url = urlbase + urltoken
		embed = Embed(url=url,title="Verify")
		self.bot.log.info(f"Verifying at url {url}")
		return token, embed

	async def processCode(self, author, nation, token, code):
		api = self.bot.api.nation(nation)
		call = api.verify(checksum=code,token=token)
		if call["data"].strip() == "1":
			await self.store(author, nation, token)
			return "Verification success! Whoo ^-^"
		return "Verification error, sorry T-T"

	async def sanitizeArgs(self, ctx, args):
		# Check that the nation argument is present
		if not len(args) == 1:
			await ctx.send("Usage: verify <nation_name>")
			return False,"",[]
		# Check that the author and nation are already verified
		author, nation = ctx.author, args[0]
		qpre = "SELECT * FROM verify"
		query = qpre + f" WHERE name='{author}' AND nation='{nation}'"
		verified = await self.bot.db.execute(query)
		rows = await verified.fetchall()
		if len(rows) > 0:
			self.bot.log.warn(f"{rows} already verified...")
			await ctx.send(f"You are already verified to {nation}")
			return False, author, args[0]
		else:
			self.bot.log.info(f"{nation} not verified...")
		return True, author, args[0]

	async def store(self, discorduser, nation, token):
		table = f"(name, nation, token)"
		store = f"('{discorduser}', '{nation}', '{token}')"
		full = f"INSERT INTO verify {table} VALUES {store}"
		await self.bot.db.execute(full)
		await self.bot.db.commit()

	@commands.command(nation='str')
	async def verify(self, ctx, *args, member: discord.Member = None):
		valid, author, nation = await self.sanitizeArgs(ctx, args)
		if not valid: return
		self.bot.log.info(f'Valid verify call by {ctx.author}...')
		token, embed = self.createLink(author)
		sentid = await ctx.send(self.verifyTemplate, embed=embed)
		checkL = lambda x: self.isreply(x,rid=sentid.id)
		codemessage = await self.bot.wait_for('message',check=checkL)
		code = codemessage.content
		process = await self.processCode(author, nation, token, code)
		await ctx.send(process)

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

	# Discord changed recently to not need command prefixes
	bot = OpenNSDiscord(
		dbfile=database,
		signlambda=signlambda,
		useragent=useragent,
		command_prefix="",
		intents = intents,
		log_handler=handler)
	return bot
