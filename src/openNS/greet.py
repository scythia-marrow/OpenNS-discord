import discord
import asyncio

from discord.ext import commands, tasks

# Helper functions
def getHappening(api, region):
	region = api.region(region)
	events = region.get_happenings()['happenings']['event']
	return [(x['timestamp'],x['text']) for x in events]

def filterArrival(happening):
	arriveL = lambda x: "arrived" in x
	nameL = lambda x: (x[0],x[1].split()[0].strip('@'))
	arrival = [nameL(x) for x in happening if arriveL(x[1])]
	return arrival

def filterDeparture(happening):
	leftL = lambda x: "departed" in x[1] or "ceased" in x[1]
	nameL = lambda x: (x[0],x[1].split()[0].strip('@'))
	departure = [nameL(x) for x in happening if leftL(x)]
	return departure

def filterTimestamp(happening, timestamp):
	timeL = lambda x: x > timestamp
	return [x for x in happening if timeL(int(x[0]))]

# TODO: small bug here where people returning after leaving will be filtered
def filterGreeting(happening):
	arrived = filterArrival(happening)
	left = filterDeparture(happening)
	stayed = []
	for arrive in arrived:
		depart = next(((ts,n) for ts,n in left if n==arrive[1]), None)
		if depart == None or depart[0] < arrive[0]:
			stayed.append(arrive)
	return stayed

class Greet(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.region = set([])
		self.channel = {}
		self.greetcache = set([])
		self.reactionlisten = {}
		self.timestamp = 0
		# Start the task to monitor reactions to this message
		self.pollArrival.start()
		self.storeFrame.start()
		self.reactiontask.start()

	async def cog_load(self):
		# Read in the registered channels into the cog state
		cursor = await self.bot.db.execute('''
			SELECT * FROM regionregister;
		''')
		for region,channel in await cursor.fetchall():
			print(region,channel)
			self.region |= set([region])
			if not region in self.channel:
				self.channel[region] = [channel]
			else:
				self.channel[region].append(channel)

	def cog_unload(self):
        	self.checknations.cancel()

	# Check for new arrivals every second
	@tasks.loop(seconds = 10.0)
	async def pollArrival(self):
		# TODO: EFFICIENCY. Allow for more than one region at a time
		for region in self.region:
			# Get the nations in the current database frame
			nationcursor = await self.bot.db.execute('''
				SELECT nation FROM regionframe
				ORDER BY time DESC
			''')
			nation = await nationcursor.fetchone()
			if not nation == None:
				nation = nation[0].split("|")
			else: nation = ""
			# Get the happenings from this region
			happening = getHappening(self.bot.api,region)
			time = filterTimestamp(happening, self.timestamp)
			greet = filterGreeting(time)
			# If there is a greeting message we haven't sent
			for time, name in greet:
				if name in self.greetcache or name in nation:
					continue
				self.greetcache |= set([name])
				self.bot.log.info(f"New arrival to {region}")
				for channel in self.channel[region]:
					asyncio.create_task(
						self.notifyarrival(
							channel,
							region,
							name)
					)
					self.bot.log.info(f"Notified {channel}")
		self.bot.log.info(f"CHECKED REGIONS! {self.region}")

	@pollArrival.before_loop
	async def before_pollArrival(self):
		self.bot.log.info("Awaiting in pollArrival...")
		# And we are done!
		await self.bot.wait_until_ready()

	def getRegionFrame(self, region):
		timestamp = self.bot.timestamp()
		api = self.bot.api.region(region)
		nation = "|".join([x.nation_name for x in api.nations])
		return timestamp, region, nation

	# Store full region frames every hour
	@tasks.loop(seconds = 3601)
	async def storeFrame(self):
		self.bot.log.info("Storing region frames...")
		# Don't store a frame within an hour of the previous
		timecursor = await self.bot.db.execute(f'''
			SELECT time FROM regionframe
			ORDER BY time DESC
		''')
		time = await timecursor.fetchone()
		if not time == None and self.bot.timestamp() - time[0] < 3000:
			self.bot.log.warn("Not storing new frame, overlap...")
			return
		# Otherwise store a new frame
		for region in self.region:
			timestamp, region, nation = self.getRegionFrame(region)
			await self.bot.db.execute(f'''
				INSERT INTO regionframe (time, name, nation)
				VALUES ({timestamp},'{region}','{nation}')
			''')
		await self.bot.db.commit()
	
	@storeFrame.before_loop
	async def before_storeFrame(self):
		self.bot.log.info("Awaiting in storeFrame...")
		await self.bot.wait_until_ready()

	async def sanitizeArgs(self, ctx, args):
		subcom = ["register <region>"]
		helptext = "Usage: greet <command>\nCommands:"
		for sub in subcom: helptext += "\n\tregister <region>"
		if not len(args) == 2 and not args[0] == "register":
			await ctx.send(helptext)
			return False, "", ""
		region = args[1]
		channel = ctx.channel.id
		duplicatetext = f"This channel already greets {region}"
		if region in self.region and channel in self.channel[region]:
			await ctx.send(duplicatetext)
			return False, region, channel
		if not region in self.channel:
			self.channel[region] = []
		return True, region, channel

	# Place the channel into the database
	async def register(self, region, channel):
		query = f'''
			INSERT INTO regionregister (name, channel)
			VALUES ('{region}',{channel})
		'''
		await self.bot.db.execute(query)
		await self.bot.db.commit()
		
	# Register the channel this command is called in to the greeting
	@commands.command(subcom='str',nation='str')
	async def greet(self, ctx, *args):
		self.bot.log.info("Greeting dispatch...")
		valid,region,channel = await self.sanitizeArgs(ctx, args)
		if not valid: return
		self.bot.log.info("Valid registration, registering channel...")
		self.channel[region].append(channel)
		self.region |= set([region])
		await self.register(region, channel)
		self.bot.log.info("Registered the region...")
		await ctx.send("Registration successful...")

	async def notifyarrival(self,channelid,region,toname):
		self.bot.log.info(f"Notifying the arrival of {toname}...")
		channel = self.bot.get_channel(channelid)
		greet = f'''
{toname} has arrived in {region}. \
Send them a welcome! \
If you want to use a stored personalized template react ✉ to this message!
'''
		embed = self.bot.telegramEmbed(toname)
		msg = await channel.send(greet, embed = embed)
		envelope = '✉'
		await msg.add_reaction(envelope)
		# Register a listener to this message reactions
		endtime = self.bot.timestamp() + 3600*48
		self.reactionlisten[msg.id] = (toname,endtime)

	@tasks.loop(seconds=60)
	async def reactcleantask(self):
		for messageid in self.reactionlisten:
			tonation, time = self.reactionlisten[messageid]
			if self.bot.timestamp() > time:
				del self.reactionlisten[messageid]

	@tasks.loop()
	async def reactiontask(self):
		def check(reaction, user):
			mess = reaction.message.id in self.reactionlisten
			async def asyncverify(ctx):
				verified = await self.bot.isVerified(user)
				return verified
			return commands.check(asyncverify) and mess
		reaction,user = await self.bot.wait_for(
			"reaction_add",
			timeout = 360.0,
			check=check)
		# Get the to of this message
		tonation,_ = self.reactionlisten[reaction.message.id]
		# Send the telegram template to the user
		slide = await user.create_dm()
		dm = "Here is a personalized telegram link!"
		embed = await self.bot.templateEmbed(user, tonation)
		await slide.send(dm, embed=embed)
