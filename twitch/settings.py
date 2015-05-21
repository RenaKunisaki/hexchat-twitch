import os
import json
import copy
import hexchat
import twitch.logger
log = twitch.logger.get()

# the default settings
defaults = {
	# attributes for each user type
	"usertypes": {
		"global_mod": {
			# note we don't need %R in badge if we only set a colour,
			# because the nick will set another colour anyway
			# (XXX what if we set a background colour?)
			"badge": "%C(green)⛏", # pickaxe (IIRC what Twitch uses)
		},
		"admin": {
			"badge": "%C(yellow)📛", # literal badge (similar to Twitch icon)
		},
		"broadcaster": {
			"badge": "%C(red)📺", # TV (no good camera symbols)
			"hilight": True, # highlight this user's messages (by changing
				# their message type e.g.
				# 'Channel Message' -> 'Channel Msg Hilight')
		},
		"mod": {
			"badge": "%C(green)🔪", # knife (Twitch uses sword/lightning bolt)
		},
		"staff": {
			"badge": "%C(pink)🔧", # wrench (what Twitch uses)
		},
		"turbo": {
			"badge": "%C(purple)🗲", # lightning (similar to Twitch icon)
		},
		"subscriber": {
			"badge": "%C(yellow)♥", # heart (each channel has its own icon)
		},
		"bot": {
			# this isn't one of the user types used by Twitch, but the user
			# can set it locally (and the script sets a few).
			"badge": "%C(lime)🖭", # tape (looks like a robot face)
		},
	},
	
	# various text colours and formats
	"textfmts": {
		# format for server text, because for some reason doing
		# hexchat.emit_print('Server Text', "blah") (or using a context)
		# doesn't apply the normal Server Text formatting.
		# This is used for messages from 'jtv' and 'twitchnotify' such as
		# "This room is in slow mode" or "Joe just subscribed".
		# {} represents the message.
		"server": "%C(orange){}"
	},
	
	# Twitch-related settings
	"twitch": {
		# What to do when you send a message beginning with a period:
		# "mydotmsg": "eat", # eat it silently like Twitch does
		"mydotmsg": "warn", # eat it and emit a warning
		# "mydotmsg": "space", # add a space in front
		# "mydotmsg": "normal", # just send it anyway
		
		# when chat is cleared by a moderator, should we actually clear it?
		"honorclear": False,
	},
	
	# Channel topic handler settings
	"topic": {
		# How often to refresh channel info, in seconds
		"refreshinterval": 60,
	},
}

# the current settings
settings = copy.deepcopy(defaults)

# default path for settings file
default_path = os.path.join(hexchat.get_info("configdir"),
	"addons", "twitch", "settings.json")

	
# load settings from file
def load(path=None):
	global settings
	if path is None: path = default_path
	log.debug('Loading settings from file "%s"' % path)
	
	with open(path) as f:
		settings = json.load(f)
	log.info('Loaded settings from file "%s"' % path)
	
	return settings


# save settings to file
def save(path=None):
	global settings
	if path is None: path = default_path
	log.debug('Saving settings to file "%s"' % path)
	
	with open(path, 'wt', encoding='UTF-8') as f:
		json.dump(settings, f, skipkeys=True, ensure_ascii=False, indent=4,
			sort_keys=True)
	log.info('Saved settings to file "%s"' % path)
	
	
# retrieve a setting
def get(key):
	global settings
	key = key.split('.')
	obj = settings
	for k in key:
		obj = obj[k]
	return obj
	
	
# change a setting
def set(key, val):
	global settings
	key  = key.split('.')
	obj  = settings
	last = key.pop()
	
	for k in key:
		obj = obj[k]
	
	obj[last] = val
	save()
