import hexchat
import json
import sys
import os
import twitch.irc, twitch.logger
log = twitch.logger.get()

emotes = {} # emote defs loaded from file
parsed_emotes = {} # emote defs with IRC formatting applied

# default path for emotes file
default_path = os.path.join(hexchat.get_info("configdir"),
	"addons", "twitch", "emotes.json")

# load emotes
def load(path=None):
	global emotes, parsed_emotes
	emotes = {}
	parsed_emotes = {}
	
	if path is None: path = default_path
	log.debug('Loading emotes from file "%s"' % path)
	
	key = None
	try:
		with open(path) as f:
			emotes = json.load(f)
		log.info('Loaded %d emotes from file "%s"' % (len(emotes), path))
		
		for key in emotes:
			log.debug("'%s' => '%s'" % (key, emotes[key]))
			parsed_emotes[key] = twitch.irc.format(emotes[key])
	except ValueError as ex:
		if key is None:
			print("* Error loading emotes: %s" % ex)
		else:
			print("* Error loading emotes: %s: %s" % (key, ex))
		(emotes, parsed_emotes) = ({}, {})
	except NameError:
		# seems to be a bug in JSON module that throws this?
		print("* Error loading emotes: malformed JSON")
		(emotes, parsed_emotes) = ({}, {})
	
	return (emotes, parsed_emotes)
	
	
# save emote defs
def save(path=None):
	global emotes
	
	if path is None: path = default_path
	log.debug('Saving emotes to file "%s"' % path)
	
	with open(path, 'wt', encoding='UTF-8') as f:
		json.dump(emotes, f, skipkeys=True, ensure_ascii=False, indent=4,
			sort_keys=True)
	log.info('Saved %d emotes to file "%s"' % (len(emotes), path))
	
	
# define an emote, replacing any existing definition.
def set(text, repl):
	global emotes, parsed_emotes
	emotes[text] = repl
	parsed_emotes[text] = twitch.irc.format(repl)
	
	
# delete an emote
def delete(name):
	global emotes, parsed_emotes
	del emotes[name]
	del parsed_emotes[name]
	log.info("Deleted emote '%s'" % name)
	

# substitute emotes into text
def insert(text):
	global emotes, parsed_emotes
	for key in parsed_emotes:
		text = text.replace(key, parsed_emotes[key])
	return text
