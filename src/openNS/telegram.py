import discord
import urllib

from discord.ext import commands

class Telegram(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		subcommand = [
			"head \"<Header text>\"",
			"sign \"<Signature text>\""
		]
		helptxt = "Usage: template <subcommand>\nSubcommands:"
		for sub in subcommand: helptxt += "\n\t" + sub
		self.helptxt = helptxt

	@commands.group(invoke_without_command=True)
	async def template(self, ctx, *args):
		await ctx.send(self.helptxt)
	
	# Sanitize the subcommand args to ensure only one template string
	async def sanitizeArgs(self, ctx, args):
		if not len(args) == 1:
			await ctx.send(self.helptxt)
			return False, "", ctx.author
		return True, args[0], ctx.author

	async def readtemplate(self, author):
		cursor = await self.bot.db.execute(f'''
			SELECT head,sign FROM telegramtemplate
			WHERE name='{author}'
		''')
		template = await cursor.fetchone()
		head, sign = "",""
		if template == None:
			await self.bot.db.execute(f'''
			INSERT INTO telegramtemplate (name,head,sign)
			VALUES ('{author}','{head}','{sign}')
		''')
		else: head, sign = template[0]
		return head, sign

	async def storetemplate(self, author, head, sign):
		await self.bot.db.execute(f'''
			UPDATE telegramtemplate
			SET head='{head}', sign='{sign}'
			WHERE name='{author}'
		''')
		await self.bot.db.commit()

	@template.command(template='str')
	async def head(self, ctx, *args):
		valid, head, author = await self.sanitizeArgs(ctx, args)
		if not valid: return
		# Replace header on the template if needed
		_,sign = await self.readtemplate(author)
		await self.storetemplate(author, head, sign)
		await ctx.send("Updated header template")

	@template.command(template='str')
	async def sign(self, ctx, *args):
		valid, sign, author = await self.sanitizeArgs(ctx, args)
		if not valid: return
		# Replace signature on the template if needed
		head,_ =  await self.readtemplate(author)
		await self.storetemplate(author, head, sign)
		await ctx.send("Updated signature template")
