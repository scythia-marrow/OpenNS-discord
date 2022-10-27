# Library imports
import asyncio
import discord
import binascii

# Module imports
from openNS.discordbot import initbot, addcogs
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class OpenNSClient(discord.Client):
	async def on_ready(self):
		print("Logged on as", self.user)
	async def on_message(self, message):
		if message.author == self.user:
			return
		if message.content == 'ping':
			await message.channel.send('pong')

# As an entrypoint, all we do is pass the database location and discord token
# to the bot package.
class iniVariables:
	def __init__(self,args):
		print(args)
		if "token" in args and "database" in args:
			self.valid = True
			tokenline = open(args["token"],"r").readline()
			print(tokenline)
			user = tokenline.split(":")[0].strip()
			token = tokenline.split(":")[1].strip()
			self.user = user
			self.token = token
			self.database = args["database"]
			self.cryptokey = args["cryptokey"]
		else:
			self.valid = False
	def isValid(self):
		return self.valid

# TODO: more proper initialization
def readIni(inifile):
	# Args is just a dictionary of arguments to items
	args = {}
	# Basically the initialization is the:
	for line in inifile:
		if line.strip()[0] == '#' or not "=" in line: continue
		parts = line.strip().split("=")
		if len(parts) > 2: raise Exception("Initialization exception.")
		args[parts[0]] = parts[1]
	# discord bot token
	# sqlite3 database location
	return iniVariables(args)

# A lambda to sign a message with the private key, used for authentication
# purposes
def sign(private_key, message, size = -1):
	signature = private_key.sign(
		bytes(message,'utf-8'),
		padding.PSS(
			mgf=padding.MGF1(hashes.SHA256()),
			salt_length=padding.PSS.MAX_LENGTH
		),
		hashes.SHA256()
	)
	return binascii.hexlify(signature)[:size]

# The main bot entrypoint
import sys
if __name__ == "__main__":
	inifile = open("openNS-discord.ini","r")
	inivars = readIni(inifile)
	if not inivars.valid: sys.exit(1)
	token = inivars.token
	user = inivars.user
	database = inivars.database
	prvdat = open(inivars.cryptokey,"rb").read()
	pubdat = open(inivars.cryptokey+".pub","rb").read()
	prvkey = serialization.load_pem_private_key(prvdat,None)
	pubkey = serialization.load_pem_public_key(pubdat,None)
	# This is the only place sign should be called from
	signlambda = lambda x: sign(prvkey,x,10)
	bot = initbot(database,signlambda)
	asyncio.run(addcogs(bot))
	bot.run(token)
	#import openNS.commands
