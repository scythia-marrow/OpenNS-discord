# Main imports
import logging
import logging.handlers
import asyncpg
import os

# Discord imports
import discord
from discord.ext import commands
from typing import List, Optional
from aiohttp import ClientSession

# Following the guide from:
# https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py

class OpenNSBot(commands.Bot):
	def __init__(
		self,
		*args,
		initial_extensions: List[str],
		db_pool: asyncpg.Pool,
		web_client: ClientSession,
		**kwargs
	):
		super().__init__(*args, **kwargs)
		self.db_pool = db_pool
		self.web_client = web_client
		self.initial_extensions = initial_extensions
	
	async def setup_hook(self) -> None:
		for extension in self.initial_extensions:
			await self.load_extension(extension)

async def runbot(token):
	logger = logging.getLogger('discord')
	logger.setLevel(logging.INFO)
	
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
	logger.addHandler(handler)
	
	async with ClientSession() as client, asyncpg.create_pool(
		user='scythia',
		command_timeout=30) as pool:
		extension = ['general']
		async with OpenNSBot(
			commands.when_mentioned,
			db_pool=pool,
			initial_extensions=extension) as bot:
			await bot.start(token)
