import hexchat
import os
import time
import json
import requests
import threading
import traceback
import twitch.api, twitch.emotes, twitch.normalize, twitch.logger
import twitch.settings
from twitch.exceptions import NetworkFailure
from twitch import irc
log = twitch.logger.get()

# map channel user modes to user attributes
user_mode_attrs = {
	"o": "mod",
}

# what fields from Twitch API JSON to copy to what attributes of user
twitchattrs = {
	"display_name": "displayName",
	"created_at":   "createdAt",
	"updated_at":   "updatedAt",
	"logo":         "logo",
	"bio":          "bio",
}

# where to store our cache files
cachedir = os.path.join(
	hexchat.get_info("configdir"), "addons", "twitch", "cache", "users")

# map message types to highlight versions
msg_hilight_types = {
	'Channel Message': 'Channel Msg Hilight',
	'Channel Action':  'Channel Action Hilight',
}


# represents a user in Twitch IRC
class user(object):
	def __init__(self, nick):
		nick = twitch.normalize.nick(nick)
		
		# global attributes
		self.nick        = nick
		self.displayName = nick
		self.color       = None
		self.irc_color   = irc.colors['grey']
		self.emoteSet    = None
		self.createdAt   = None
		self.updatedAt   = None
		self.logo        = None
		self.bio         = None
		self.attributes  = {
			"turbo":      False,
			"global_mod": False,
			"staff":      False,
			"admin":      False,
			"bot":        False, # not set by Twitch; we set this automatically
			# for some known bots, and user can set it as well.
		}
		self.chanAttrs = {} # per-channel attributes
		self.lookup() # get info from API or cache
		
	
	def __str__(self):
		return "twitch.user(%s)" % self.nick
		
	
	# Look up more info about this user.
	def lookup(self):
		data = None
		path = os.path.join(cachedir, self.nick)
		try:
			with open(path) as f:
				# log.debug("%s.lookup cache hit" % str(self))
				data = json.load(f)
				for k, v in data.items(): #merge this into ourself
					setattr(self, k, v)		
		except FileNotFoundError:
			log.debug("%s.lookup cache miss" % str(self))
			self.lookupAPI()
			
	
	# Look up this user in Twitch API (in a separate thread).
	def lookupAPI(self):
		here = str(self) + ".lookupAPI.thread"
		def thread():
			log.debug("%s: started" % here)
			while True: # repeat until success
				try:
					data = twitch.api.getUser(self.nick)
					log.debug("%s: data: %s" % (here, data))
					for src, dst in twitchattrs.items(): # merge into self
						if src in data:
							setattr(self, dst, data[src])
					log.debug("%s: Set attrs OK" % here)
					self.save()
					log.debug("%s: done" % here)
					return
				except NetworkFailure:
					log.debug("%s: network error; retrying" % here)
					time.sleep(60) # wait and try again.
				except:
					log.exception("Unhandled exception in %s" % here)
					return
		# end of thread()

		t = threading.Thread(
			target = thread,
			args   = (),
			name   = "%s.lookup" % self,
			daemon = True)
		t.start()
	# end of lookupAPI()
	
	
	# Dump this user to a local JSON file so we don't have to look them up
	# again next time we run hexchat.
	def save(self):
		#stack  = traceback.extract_stack()
		#frames = []
		## (filename, line number, function name, text) 
		#frames.extend(map(lambda f: "{0}:{1}: in '{2}': {3}".format(*f), stack))
		#log.debug("%s.save called from:\n\t%s" %
		#	(str(self), "\n\t".join(frames)))
		path = os.path.join(cachedir, self.nick)
		#log.debug("%s.save(%s)" % (self, path))
		with open(path, 'w') as f:
			json.dump(self.__dict__, f)
		log.debug("%s.save OK" % self)
		
			
	# Set RGB nick colour (from USERCOLOR message).
	# Will map to the closest matching IRC colour.
	def setColor(self, col):
		if col != self.color:
			self.color     = col
			self.irc_color = irc.mapColor(col)
			self.save()
			
			
	# Get a dict of the user's types, with settings for that type as value
	def getTypes(self, chan):
		types     = {}
		attrs     = self.getChanAttrs(chan)
		usertypes = twitch.settings.get('usertypes')
		
		# iterate attrs where value == True
		for attr in filter(lambda v: attrs[v], attrs):
			types[attr] = usertypes.get(attr, {})
		
		return types
		
	
	# Get a list of name badges this user should have
	def getNameBadges(self, chan):
		badges = []
		for name, utype in self.getTypes(chan).items():
			if 'badge' in utype:
				badges.append(irc.format(utype['badge']))
		return badges
		
		
	# Get the actual message type we should use for a message from this user
	def getMsgType(self, chan, msgtype):
		if msgtype in msg_hilight_types: # if this msgtype can be hilighted
			for name, utype in self.getTypes(chan).items():
				log.debug("User '%s' channel '%s' type '%s'" %
					(self.nick, chan.name, name))
				if utype.get('hilight', False):
					tp = msg_hilight_types[msgtype]
					log.debug("User '%s' channel '%s' msgtype '%s' -> '%s'" %
						(self.nick, chan.name, msgtype, tp))
					return tp
		return msgtype
		
		
	# Get formatted nick for displaying in given channel.
	# Includes badges and colours.
	def getPrettyNick(self, chan):
		badges = self.getNameBadges(chan)
		return "".join(badges + [irc.color(self.irc_color), self.displayName])
		
		
	# Format message text for displaying in given channel.
	def formatMessageText(self, chan, text):
		text = twitch.emotes.insert(text)
		for name, utype in self.getTypes(chan).items():
			if 'format' in utype:
				text = irc.format(utype['format'].format(text))
		return text
		
		
	# Print user's chat message in channel.
	def printMessage(self, chan, text, msgtype):
		chan      = twitch.channel.get(chan)
		text      = self.formatMessageText(chan, text)
		usertypes = twitch.settings.get('usertypes')
		msgtype   = self.getMsgType(chan, msgtype)
		chan.emit_print(msgtype, self.getPrettyNick(chan), text)
		
		
	# Add user to a channel if they aren't there already.
	def joinChannel(self, chan):
		chan = twitch.channel.get(chan)
		if not chan.name in self.chanAttrs:
			self.chanAttrs[chan.name] = {
				"broadcaster": False,
				"subscriber":  False,
				"mod":         False,
			}
		chan.addUser(self)
		
		
	# Remove user from a channel if they're there
	def leaveChannel(self, chan):
		chan = twitch.channel.get(chan)
		if chan.name in self.chanAttrs:
			del self.chanAttrs[chan.name]
		chan.removeUser(self)
		
	
	# Set a channel attribute for this user.
	def setChanAttr(self, chan, attr, val):
		chan = twitch.channel.get(chan)
		self.joinChannel(chan)
		
		if self.chanAttrs[chan.name].get(attr) != val:
			self.chanAttrs[chan.name][attr] = val
			self.save() # avoid excessive saving
			
			
	# Get channel attributes for this user.
	def getChanAttrs(self, chan):
		chan = twitch.channel.get(chan).name
		
		# create entry for this channel if not existing
		if chan not in self.chanAttrs:
			self.chanAttrs[chan] = {}
		
		attrs = self.attributes.copy()
		attrs.update(self.chanAttrs[chan]) # merge
		return attrs
		
		
	# Set an IRC channel mode for this user.
	def setChannelMode(self, chan, mode, val):
		if mode in user_mode_attrs:
			attr = user_mode_attrs[mode]
			self.setChanAttr(chan, attr, val)
		else:
			log.warn("Unrecognized user mode '%s'" % mode)
			
			
	# Set single global attribute.
	def setAttr(self, attr, val):
		if self.attributes.get(attr) != val:
			self.attributes[attr] = val
			self.save()
		
	
	# Set global attributes.
	def setAttrs(self, attrs):
		changed = False
		for k, v in attrs.items():
			if self.attributes.get(k) != v:
				self.attributes[k] = v
				changed = True
		if changed:
			self.save()
		
# users we know about (nick => obj)
users = {}

# look up user by nick; create if not existing
def get(nick):
	if type(nick) is user:
		return nick
	nick = twitch.normalize.nick(nick)
	if nick not in users:
		u = user(nick)
		users[nick] = u
	return users[nick]
