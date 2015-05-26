import hexchat
import twitch.channel, twitch.user, twitch.logger, twitch.settings
from twitch import irc
log = twitch.logger.get()

# each function defined in this module corresponds to a message sent by Twitch.
# for sanity's sake, messages beginning with _ are ignored.

def USERCOLOR(channel, param):
	# e.g. USERCOLOR pioxys #FF0000
	twitch.user.get(param[0]).setColor(param[1])
	return hexchat.EAT_ALL
	
def EMOTESET(channel, param):
	# e.g. EMOTESET michadk [0,7297]
	# tells what emotes the user can use
	# we don't actually do anything with this...
	return hexchat.EAT_ALL
	
def SPECIALUSER(channel, param):
	# e.g. SPECIALUSER evolem subscriber
	twitch.user.get(param[0]).setChanAttr(channel, param[1], True)
	return hexchat.EAT_ALL
	
def HISTORYEND(channel, param):
	# when we join a channel, some older messages are replayed.
	# this tells when those messages are finished.
	chan = twitch.channel.get(channel)
	if not chan.histEndRecvd:
		chan.emit_print('Server Text', "End of history replay")
		chan.histEndRecvd = True
	return hexchat.EAT_ALL
	
def CLEARCHAT(channel, param):
	# someone got the boot, or possibly the channel was cleared?
	chan = twitch.channel.get(channel)
	if len(param) > 0:
		victim = param[0]
		chan.emit_print('Server Text', "%s has been timed out." % victim)
		return hexchat.EAT_ALL
	else:
		if twitch.settings.get('twitch.honorclear'):
			chan.getContext().command('CLEAR')
		chan.emit_print('Server Text', "Chat was cleared by a moderator")
		return hexchat.EAT_ALL
	
def HOSTTARGET(channel, param):
	# we started or stopped hosting another channel
	chan    = twitch.channel.get(channel)
	dest    = param[0]
	viewers = param[1]
	if dest == '-':
		chan.emit_print('Server Text', "No longer hosting")
	else:
		msg = "Currently hosting http://twitch.tv/%s [ #%s ]" % (dest, dest)
		if viewers == '-':
			chan.emit_print('Server Text', "%s, who is offline." % msg)
		else:
			chan.emit_print('Server Text', "%s for %s viewers" % (msg, viewers))
	return hexchat.EAT_ALL
	