import aiosqlite
import asyncio
from runner import readIni

async def tableGen(databasefile):
	async with aiosqlite.connect(databasefile) as db:
		await db.execute('''
			CREATE TABLE IF NOT EXISTS verify (
				name TEXT,
				nation TEXT,
				token TEXT
			);
		''')
		await db.execute('''
			CREATE TABLE IF NOT EXISTS regionframe (
				name TEXT,
				time BIGINT,
				nation MEDIUMTEXT
			);
		''')
		await db.execute('''
			CREATE TABLE IF NOT EXISTS regionregister (
				name TEXT,
				channel BIGINT
			);
		'''
		)
		await db.execute('''
			CREATE TABLE IF NOT EXISTS telegramtemplate (
				time BIGINT,
				name TEXT,
				sign TEXT,
				head TEXT
			);
		''')

if __name__ == "__main__":
	ini = readIni(open("openNS-discord.ini","r"))
	asyncio.run(tableGen(ini.database))
