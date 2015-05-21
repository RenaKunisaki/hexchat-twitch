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
			# Text to prepend to their nick in chat.
			# Note we don't need %R in badge if we only set a colour,
			# because the nick will set another colour anyway
			# (XXX what if we set a background colour?)
			# We'll also bold their nick.
			"badge": "%C(green)⛏%B", # pickaxe (IIRC what Twitch uses)
			
			# Custom formatting to use for their text. {} is replaced with the
			# message text; IRC formatting codes (from irc.py) such as %B can
			# be used. So this default just bolds the text.
			"format": "%B{}",
		},
		"admin": {
			"badge": "%C(yellow)📛%B", # literal badge (similar to Twitch icon)
			"format": "%B{}",
		},
		"broadcaster": {
			"badge": "%C(red)📺%B", # TV (no good camera symbols)
			
			# Highlight this user's messages (by changing the hexchat message
			# type e.g. 'Channel Message' -> 'Channel Msg Hilight')
			# Uses the same spelling of hilight as hexchat does.
			"hilight": True,
		},
		"mod": {
			"badge": "%C(green)🔪", # knife (Twitch uses sword/lightning bolt)
			"format": "%B{}"
		},
		"staff": {
			"badge": "%C(pink)🔧%B", # wrench (what Twitch uses)
			"format": "%B{}",
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
		"Server_Text": "%C(orange){}"
	},
	
	# Twitch-related settings
	"twitch": {
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
	
	try:
		with open(path) as f:
			settings = json.load(f)
		log.info('Loaded settings from file "%s"' % path)
	except FileNotFoundError:
		log.warning('File "%s" not found' % path)
	
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
	try:
		for k in key:
			obj = obj[k]
		return obj
	except KeyError:
		return None
	
	
# change a setting
def set(key, val):
	global settings
	key  = key.split('.')
	obj  = settings
	last = key.pop()
	
	for k in key:
		if k not in obj:
			obj[k] = {}
		obj = obj[k]
	
	obj[last] = val
	save()
