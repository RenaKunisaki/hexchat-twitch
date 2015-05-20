import hexchat
import re
import sys
import twitch.hook, twitch.jtvmsghandler, twitch.user, twitch.channel
import twitch.normalize, twitch.commands, twitch.exceptions, twitch.topic
import twitch.logger
from twitch import irc
log = twitch.logger.get()

# regex for extracting time from ban message
ban_msg_regex = re.compile(r"for (\d+) more seconds")


# XXX why do we have to colour the server texts? Why do they not
# already appear in the "server text" colour?
# XXX make this something like log.server or twitch.serverText?
# or twitch.prnt(type, text)?
def _serverText(ctxt, text):
	ctxt.emit_print('Server Text', irc.color('orange', text))
	return hexchat.EAT_ALL


# Identify ourselves as Twitch IRC client to get user info
def endofmotd_cb(word, word_eol, userdata):
	hexchat.command('QUOTE TWITCHCLIENT 3')

	
# Ignore various "unknown command" errors
unknowncommands = ('WHO', 'WHOIS')
def servererr_cb(word, word_eol, userdata):
	if word[3] in unknowncommands:
		return hexchat.EAT_ALL
	return hexchat.EAT_NONE
	

# PRIVMSG hook to handle various notification messages from Twitch.
def privmsg_cb(word, word_eol, msgtype):
	try:
		nick = twitch.normalize.nick((word[0][1:].split('!')[0]))
		chan = word[2]
		text = word_eol[3]
		if nick == 'jtv':
			if chan[0] != '#':
				return _serverText(hexchat, text[1:])
			elif "You are banned" in text:
				if not chan.areWeBanned:
					chan.areWeBanned = True
					match = ban_msg_regex.search(text)
					time  = int(match.group(1))

					def clear_ban(userdata):
						chan.areWeBanned = False
						_serverText(chan.getContext(),
							"You are (hopefully) no longer banned")
					hexchat.hook_timer(time * 1000, clear_ban)
			else:
				action = word[3][1:]
				param  = word[4:]
				if action[0] != '_' and hasattr(twitch.jtvmsghandler, action):
					return getattr(twitch.jtvmsghandler, action)(chan, param)
				else:
					#log.warning("Unhandled JTV message: %s" % str(word))
					ctxt = twitch.channel.get(chan).getContext()
					return _serverText(ctxt, text[1:])
		elif nick == 'twitchnotify':
			return _serverText(hexchat, text[1:])
		else:
			return hexchat.EAT_NONE
	except:
		log.exception("Unhandled exception in twitch.privmsg_cb")
		return hexchat.EAT_NONE


# message hook to format user messages nicely.
message_cb_recurse = False
def message_cb(word, word_eol, msgtype):
	# avoid infinite loop
	global message_cb_recurse
	if message_cb_recurse:
		return
	message_cb_recurse = True
	try:
		if len(word) < 1:
			return hexchat.EAT_NONE
		nick = word[0]
		text = word_eol[1]
		user = twitch.user.get(nick)
		chan = twitch.channel.get(hexchat.get_context())
		user.joinChannel(chan)
		user.printMessage(chan, text, msgtype)
		return hexchat.EAT_ALL
	except:
		log.exception("Unhandled exception in twitch.message_cb")
		return hexchat.EAT_NONE
	finally:
		message_cb_recurse = False


# Your message hook
def yourmsg_cb(word, word_eol, msgtype):
	try:
		if len(word) > 1 and word[1][0] == '.':
			# eat messages beginning with '.' like Twitch does
			return hexchat.EAT_ALL
		else:
			return message_cb(word, word_eol, msgtype)
	except:
		log.exception("Unhandled exception in twitch.yourmsg_cb")
		return hexchat.EAT_NONE


# MODE hook to track mods
def mode_cb(word, word_eol, msgtype):
	try:
		chan = word[2]
		mode = word[3]
		whom = word[4]
		user = twitch.user.get(whom)
		what = '+'
		
		for char in mode:
			if char == '+' or char == '-':
				what = char
			elif what == '+':
				user.setChannelMode(chan, char, True)
			elif what == '-':
				user.setChannelMode(chan, char, False)
	except:
		log.exception("Unhandled exception in twitch.mode_cb")
	finally:
		return hexchat.EAT_NONE


# When we join a channel, set up the user info and get stream status
def youjoin_cb(word, word_eol, msgtype):
	try:
		chan = twitch.channel.get(word[1])
		
		# automatically set up some users
		jtv = twitch.user.get('jtv')
		jtv.joinChannel(chan)
		jtv.setAttrs({'admin':True,'bot':True})
		
		twitchnotify = twitch.user.get('twitchnotify')
		twitchnotify.joinChannel(chan)
		twitchnotify.setAttrs({'admin':True,'bot':True})
		
		broadcaster = twitch.user.get(chan.name)
		broadcaster.joinChannel(chan)
		broadcaster.setChanAttr(chan, 'broadcaster', True)
	except:
		log.exception("Unhandled exception in twitch.youjoin_cb")
	finally:
		return hexchat.EAT_NONE
		
		
def isCommand(name, obj):
	return (callable(obj) and (not name.startswith('_'))
		and hasattr(obj, 'command'))
		
		
# handler for /twitch command
def twitchcmd_cb(word, word_eol, userdata):
	try:
		log.debug("/twitch command: %s" % word)
		if len(word) < 2:
			print("Available commands:")
			for name, obj in twitch.commands.__dict__.items():
				if isCommand(name, obj):
					print("%s - %s" % (name, obj.command['desc']))
			return hexchat.EAT_ALL
		
		cmd = word[1]
		if not hasattr(twitch.commands, cmd):
			raise twitch.exceptions.UnknownCommandError(cmd)

		f = getattr(twitch.commands, cmd)
		if not hasattr(f, 'command'):
			raise twitch.exceptions.UnknownCommandError(cmd)

		f(word[2:], word_eol[2:])
	except twitch.exceptions.BadParameterError as ex:
		print("%s: %s" % (cmd, ex))
	except twitch.exceptions.UnknownCommandError as ex:
		print("%s: Unknown command" % ex)
	except:
		log.exception("Unhandled exception in twitch.twitchcmd_cb(%s)" % cmd)
	finally:
		return hexchat.EAT_ALL
		
		
# Install the hooks
def install():
	twitch.hook.server('376', endofmotd_cb)
	twitch.hook.server('421', servererr_cb)
	twitch.hook.server('PRIVMSG', privmsg_cb)
	twitch.hook.prnt('Channel Action',         message_cb)
	twitch.hook.prnt('Channel Action Hilight', message_cb)
	twitch.hook.prnt('Channel Message',        message_cb)
	twitch.hook.prnt('Channel Msg Hilight',    message_cb)
	twitch.hook.prnt('Your Message', yourmsg_cb)
	twitch.hook.server('MODE', mode_cb)
	twitch.hook.prnt('You Join', youjoin_cb)
	twitch.hook.command('twitch', twitchcmd_cb)
