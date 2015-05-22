import hexchat
import threading
import locale
import time
import json
import twitch.api, twitch.normalize, twitch.logger, twitch.topic
from twitch.exceptions import NetworkFailure
from twitch import irc
log = twitch.logger.get()

# represents a channel on Twitch
class channel(object):
	def __init__(self, name):
		name = twitch.normalize.channel(name)
		log.debug("Create channel '%s'", name)
		self.name        = name
		self.displayName = name
		self.online      = False
		self.game        = "<unknown>"
		self.viewers     = 0
		self.followers   = 0
		self.views       = 0
		self.title       = "<no title>" # Twitch calls title "status"
		self.mature      = False
		self.language    = "<unknown>"
		self.createdAt   = None
		self.delay       = 0  # presumably the broadcaster-imposed stream delay
		self.users       = {} # map of nick => chat user
		self.slowMode    = 0  # chat slow mode delay timer
		self.subsMode    = False # chat subscriber only mode
		self.topic       = None  # most recently set topic string
		self.updating    = False # are we currently updating?
		self.areWeBanned = False # did we receive a "you are banned" message?
		# (only for temp bans, to notify when time expires)
		self.histEndRecvd= False # did we receive HISTORYEND msg yet?
		self.lookup()
	
	def __str__(self):
		return "twitch.channel(%s)" % self.name
		
	# Internal method to set our attributes from Twitch API response.
	def setAttrsFromAPI(self, data):
		if not data.get('streams'): # missing or empty
			self.online = False
			return
		stream  = data['streams'][0]
		channel = stream['channel']
		self.online      = True
		self.displayName = channel.get('display_name', self.name)
		self.game        = stream .get('game',         '<unknown>')
		self.viewers     = stream .get('viewers',      0)
		self.followers   = channel.get('followers',    0)
		self.views       = channel.get('views',        0)
		self.title       = channel.get('status',       '<no title>')
		self.mature      = channel.get('mature',       False)
		self.language    = channel.get('language',     '<unknown>')
		self.createdAt   = channel.get('created_at',   None)
		self.delay       = channel.get('delay',        0)
		
	# Look up info about this channel when first joining.
	# We don't bother to cache channels, because we don't need to look them
	# up terribly often, nor look up very many of them, unlike chat users.
	def lookup(self):
		here = str(self) + ".lookup.thread"
		self.updating = True
		def thread():
			log.debug("%s: started" % here)
			while True: # repeat until success
				try:
					data = twitch.api.getChannel(self.name)
					#log.debug("%s: data: %s" % (here,
					#	json.dumps(data, sort_keys=True, indent=4)))
					self.setAttrsFromAPI(data)
					
					log.debug("%s: update topic" % here)
					self.makeTopic()
					twitch.topic.update_channel(self)
					
					log.debug("%s: done" % here)
					self.updating = False
					return
				except NetworkFailure:
					log.debug("%s: network error; retrying" % here)
					time.sleep(60) # wait and try again.
				except:
					log.exception("Unhandled exception in %s" % here)
					self.updating = False
					return
		# end of thread()

		t = threading.Thread(
			target = thread,
			args   = (),
			name   = "%s.lookup" % self,
			daemon = True)
		t.start()
	# end of lookup()
	
	# Refresh some info such as viewer count.
	# Return True if successful, False if failed (e.g. network error)
	# This is similar to lookup(), but blocking (no separate thread) and does
	# not retry if the request fails due to network error.
	# It's called periodically from a thread to update the channel "topic".
	def update(self):
		if self.updating: # avoid stacking a bunch of updates
			return False
		self.updating = True
		try:
			log.debug("%s.update(): starting", self)
			data = twitch.api.getChannel(self.name)
			log.debug("%s.update(): got data: %s", self, data)
			self.setAttrsFromAPI(data)
			log.debug("%s.update(): OK", self)
			return True
		except NetworkFailure:
			log.debug("%s.update: network error", self)
			return False
		finally:
			self.updating = False
			
	# Get hexchat context for this channel.
	def getContext(self):
		ctxt = hexchat.find_context(channel='#' + self.name)
		# XXX check server too
		# (does it expect partial hostname, full hostname, etc for server?)
		return ctxt
			
	# Make IRC topic string.
	# returns None if it's the same as last time.
	def makeTopic(self):
		attrs = {}
		for k, v in self.__dict__.items():
			#log.debug("attrs[%s] = %s", k, v)
			attrs[k] = v
		
		if self.online:
			attrs['online'] = '%C(green)[LIVE]'
		else:
			attrs['online'] = '%C(red)[OFFLINE]'
			
		if self.mature:
			attrs['mature'] = " %C(red)🔞%R"
		else:
			attrs['mature'] = ""
			
		#attrs['displayName'] = irc.color('yellow', attrs['displayName'])
		#attrs['game']        = irc.color('yellow', attrs['game'])
		
		# add commas to numbers
		log.debug("viewers = %s (%s)", attrs['viewers'], type(attrs['viewers']))
		attrs['viewers']  =locale.format('%d',attrs['viewers'],   grouping=True)
		attrs['followers']=locale.format('%d',attrs['followers'], grouping=True)
		attrs['views']    =locale.format('%d',attrs['views'],     grouping=True)
		
		topic = \
			"%B{online}%R{mature} 👤{viewers} ♥{followers} 👁{views} | " + \
			"{title} | %C(yellow){displayName}%R playing %C(yellow){game}%R"
		topic = irc.format(topic.format(**attrs))
		
		if topic == self.topic:
			log.debug("%s.makeTopic(): topic not changed", self)
			return None
		
		self.topic = topic
		return topic
		
	# Add user to this channel if they aren't there already.
	def addUser(self, user):
		self.users[user.nick] = user
		
	# Remove user from this channel if they're here.
	def removeUser(self, user):
		if user.nick in self.users:
			del self.users[user.nick]
			
	# Emit a message in this channel's context.
	# Would be named print, but that's a reserved word in Python.
	def emit_print(self, msgtype, *args):
		irc.emit_print(self, msgtype, *args)
	
# channels we know about (name => obj)
channels = {}

# look up channel by name or context; create if not existing
# if given a channel object, just returns it. so use this to ensure
# you have a channel object.
def get(name):
	if type(name) is channel:
		return name
	#elif type(name) is hexchat.Context:
	elif "<hexchat.Context object" in str(name): #HACK XXX
		c = name.get_info('channel')
		return get(c)
	else:
		name = twitch.normalize.channel(name)
		if name not in channels:
			chan = channel(name)
			channels[name] = chan
		return channels[name]
