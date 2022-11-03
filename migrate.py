import aiosqlite
import asyncio
from runner import readIni

async def tableGen(databasefile):
	async with aiosqlite.connect(databasefile) as db:
		await db.execute('''
			CREATE TABLE verify (
				name TEXT,
				nation TEXT,
				token TEXT
			);
		''')
		await db.execute('''
			CREATE TABLE regionframe (
				name TEXT,
				time TIMESTAMP,
				nations MEDIUMTEXT
			);
		''')
		await db.execute('''
			CREATE TABLE telegramtemplate (
				name TEXT,
				sign TEXT,
				head TEXT
			);
		''')

if __name__ == "__main__":
	ini = readIni(open("openNS-discord.ini","r"))
	asyncio.run(tableGen(ini.database))
