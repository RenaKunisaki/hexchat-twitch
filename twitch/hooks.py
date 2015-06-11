import hexchat
import re
import sys
import twitch.hook, twitch.jtvmsghandler, twitch.user, twitch.channel
import twitch.normalize, twitch.commands, twitch.exceptions, twitch.topic
import twitch.logger, twitch.settings
from twitch import irc
log = twitch.logger.get()

# regex for extracting time from ban message
ban_msg_regex = re.compile(r"for (\d+) more seconds")


# Identify ourselves as Twitch IRC client to get user info
def endofmotd_cb(word, word_eol, userdata):
	hexchat.command('CAP REQ :twitch.tv/tags twitch.tv/commands')

	
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
				irc.emit_print(None, 'Server Text', text[1:])
				return hexchat.EAT_ALL
			elif "You are banned" in text:
				chan = twitch.channel.get(chan)
				if not chan.areWeBanned:
					chan.areWeBanned = True
					match = ban_msg_regex.search(text)
					time  = int(match.group(1))

					def clear_ban(userdata):
						chan.areWeBanned = False
						chan.emit_print('Server Text',
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
					twitch.channel.get(chan).emit_print('Server Text', text[1:])
					return hexchat.EAT_ALL
		elif nick == 'twitchnotify':
			twitch.channel.get(chan).emit_print('Server Text', text[1:])
			return hexchat.EAT_ALL
		else:
			twitch.user.get(nick).joinChannel(chan)
			return hexchat.EAT_NONE
	except:
		log.exception("Unhandled exception in twitch.privmsg_cb")
		return hexchat.EAT_NONE
		
		
# handle Twitch USERSTATE and GLOBALUSERSTATE messages
def userstate_cb(word, word_eol, msgtype):
	try:
		log.debug("Got %s msg: %s", msgtype, word)
		# Nothing to do here (except eat the message) until Hexchat adds a
		# way to read the message's IRCv3 tags.
		pass
	except:
		log.exception("Unhandled exception in twitch.userstate_cb")
	finally:
		return hexchat.EAT_ALL
		
		
# handle Twitch HOSTTARGET messages
# :tmi.twitch.tv HOSTTARGET #renakunisaki :cloakedyoshi -
def hosttarget_cb(word, word_eol, msgtype):
	try:
		param = [word[1], word[2]]
		return twitch.jtvmsghandler.HOSTTARGET(word[0], param)
	except:
		log.exception("Unhandled exception in twitch.hosttarget_cb")
	finally:
		return hexchat.EAT_ALL

		
#def rawmsg_cb(word, word_eol, msgtype, attributes):
#	try:
#		log.debug("Got raw msg: %s", word)
#	except:
#		log.exception("Unhandled exception in twitch.rawmsg_cb")
#	finally:
#		return hexchat.EAT_NONE


# message hook to format user messages nicely.
message_cb_recurse = False
def message_cb(word, word_eol, msgtype):
	# avoid infinite loop
	global message_cb_recurse
	if message_cb_recurse:
		return
	message_cb_recurse = True
	try:
		#log.debug("message_cb word=%s" % str(word))
		#log.debug("message_cb word_eol=%s" % str(word_eol))
		if len(word) < 1:
			return hexchat.EAT_NONE
		nick = twitch.normalize.nick(word[0])
		try:
			text = word[1]
		except IndexError:
			text = ''
		user = twitch.user.get(nick)
		chan = twitch.channel.get(hexchat.get_context())
		if chan is not None:
			user.joinChannel(chan)
			user.printMessage(chan, text, msgtype)
		else:
			log.error("Got user message for invalid channel: <%s> %s" %
				(nick, text))
		return hexchat.EAT_ALL
	except:
		log.exception("Unhandled exception in twitch.message_cb")
		return hexchat.EAT_NONE
	finally:
		message_cb_recurse = False


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
		chan.join()
		hexchat.command("CAP REQ :twitch.tv/membership")
		
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
		
		
# When we leave a channel, stop updating it
def youpart_cb(word, word_eol, msgtype):
	try:
		if msgtype == 'You Kicked':
			chan = word[1]
		else:
			chan = word[2]
		twitch.channel.get(chan).leave()
	except:
		log.exception("Unhandled exception in twitch.youpart_cb")
		
		
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
		
		
# ignore repeated JOIN events that can happen because we simulate them
# (since Twitch doesn't always send them reliably)
def join_cb(word, word_eol, msgtype):
	try:
		nick = twitch.normalize.nick((word[0][1:].split('!')[0]))
		user = twitch.user.get(nick)
		chan = twitch.channel.get(word[2])
		if chan.hasUser(user):
			return hexchat.EAT_ALL
		else:
			user.joinChannel(chan)
			if ".twitch.hexchat.please.stop.being.butts" not in word[0]:
				# eat JOINs that actually come from Twitch
				return hexchat.EAT_ALL
			else:
				return hexchat.EAT_NONE
	except:
		log.exception("Unhandled exception in twitch.join_cb(%s)" % str(word))
		return hexchat.EAT_NONE
		

# suppress "gives/removes channel operator status" messages
def chanop_cb(word, word_eol, msgtype):
	if twitch.settings.get('mute.chanop'):
		return hexchat.EAT_ALL
	else:
		return hexchat.EAT_NONE
		
		
# suppress join/part messages
def joinpart_cb(word, word_eol, msgtype):
	if twitch.settings.get('mute.joinpart'):
		log.debug("Muted a join/part message: %s" % str(word))
		return hexchat.EAT_ALL
	else:
		return hexchat.EAT_NONE
		
		
# suppress "capabilities acknowledged" messages
def capack_cb(word, word_eol, msgtype):
	return hexchat.EAT_ALL
		
		
# lowercase channel name before joining, or else we won't get any messages
def joincmd_cb(word, word_eol, userdata):
	try:
		chan = word[1]
		orig = chan
		chan = chan.lower()
		
		# also handle URLs
		unslashed = re.search('([^/]+)$', chan)
		if unslashed: chan = unslashed.group(1)
		
		# also handle bare username
		if chan[0] != '#': chan = '#' + chan
		log.debug("JOIN(%s) => (%s)", orig, chan)
		
		if orig == chan:
			return hexchat.EAT_NONE
		else:
			hexchat.command("JOIN " + chan)
			return hexchat.EAT_ALL
	except:
		log.exception("Unhandled exception in twitch.joincmd_cb(%s)" % cmd)
		return hexchat.EAT_NONE
		
		
# Install the hooks
def install():
	twitch.hook.server ('376',                    endofmotd_cb)
	twitch.hook.server ('421',                    servererr_cb)
	twitch.hook.server ('PRIVMSG',                privmsg_cb)
	twitch.hook.server ('USERSTATE',              userstate_cb)
	twitch.hook.server ('GLOBALUSERSTATE',        userstate_cb)
	twitch.hook.server ('HOSTTARGET',             hosttarget_cb)
	#twitch.hook.server_attrs('RAW LINE',               rawmsg_cb)
	twitch.hook.prnt   ('Channel Action',         message_cb)
	twitch.hook.prnt   ('Channel Action Hilight', message_cb)
	twitch.hook.prnt   ('Channel Message',        message_cb)
	twitch.hook.prnt   ('Channel Msg Hilight',    message_cb)
	twitch.hook.prnt   ('Your Action',            message_cb)
	twitch.hook.prnt   ('Your Message',           message_cb)
	twitch.hook.server ('MODE',                   mode_cb)
	twitch.hook.server ('JOIN',                   join_cb)
	twitch.hook.prnt   ('You Join',               youjoin_cb)
	twitch.hook.prnt   ('You Part',               youpart_cb)
	twitch.hook.prnt   ('You Part with Reason',   youpart_cb)
	twitch.hook.prnt   ('You Kicked',             youpart_cb)
	twitch.hook.command('twitch',                 twitchcmd_cb)
	twitch.hook.prnt   ('Channel Operator',       chanop_cb)
	twitch.hook.prnt   ('Channel DeOp',           chanop_cb)
	twitch.hook.prnt   ('Join',                   joinpart_cb)
	twitch.hook.prnt   ('Part',                   joinpart_cb)
	twitch.hook.command('join',                   joincmd_cb)
	twitch.hook.prnt   ('Capability Acknowledgement', joinpart_cb)
