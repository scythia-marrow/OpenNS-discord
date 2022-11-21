import discord

from discord.ext import commands
from discord import Embed

# Helper functions
def createLink(signlambda, user):
	# For the token, sign the username with the private key
	token = signlambda(f'{user}')
	urlbase = "https://www.nationstates.net/page=verify_login"
	urltoken = f"?token={token}"
	url = urlbase + urltoken
	embed = Embed(url=url,title="Verify")
	return token, embed

class Verify(commands.Cog):
	verifyTemplate = '''
		To verify your Nation States nation, reply to this message with the code found at this personalized link.
	'''
	def __init__(self, bot):
		self.bot = bot

	def isreply(self, message, rid):
		ret = False
		if not message.reference is None and message.reference.resolved:
			ret = rid == message.reference.message_id
		return ret

	async def processCode(self, author, nation, token, code):
		api = self.bot.api.nation(nation)
		call = api.verify(checksum=code,token=token)
		if call["data"].strip() == "1":
			await self.store(author, nation, token)
			return "Verification success! Whoo ^-^"
		self.bot.log.warn("Verification data " + str(call))
		return "Verification error, sorry T-T"

	async def sanitizeArgs(self, ctx, args):
		# Check that the nation argument is present
		if not len(args) == 1:
			await ctx.send("Usage: verify <nation_name>")
			return False,"",[]
		# Check that the author and nation are already verified
		author, nation = ctx.author, args[0]
		verified = await self.bot.isVerified(author, nation)
		if verified:
			self.bot.log.info(f"{author} already verified")
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
		token, embed = createLink(self.bot.signlambda, author)
		sentid = await ctx.send(self.verifyTemplate, embed=embed)
		checkL = lambda x: self.isreply(x,rid=sentid.id)
		codemessage = await self.bot.wait_for('message',check=checkL)
		code = codemessage.content
		process = await self.processCode(author, nation, token, code)
		await ctx.send(process)

