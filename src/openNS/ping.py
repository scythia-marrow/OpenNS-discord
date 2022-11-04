import discord

from discord import Embed
from discord.ext import commands

class Ping(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx, *, member: discord.Member = None):
		self.bot.log.info("Called ping...")
		message = Embed(
			url="https://scythiamarrow.org",
			title="clicktest")
		sign = self.bot.signlambda("Sign test")
		await ctx.send(f'Hi there! Sign is {sign}',embed=message)
