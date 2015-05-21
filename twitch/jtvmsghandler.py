import hexchat
import twitch.channel, twitch.user, twitch.logger, twitch.settings
from twitch import irc
log = twitch.logger.get()

# each function defined in this module corresponds to a message sent by Twitch.
# for sanity's sake, messages beginning with _ are ignored.

def _serverText(ctxt, text):
	ctxt.emit_print('Server Text', irc.color('orange', text))
	return hexchat.EAT_ALL

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
	return _serverText(chan.getContext(), "End of history replay")
	
def CLEARCHAT(channel, param):
	# someone got the boot, or possibly the channel was cleared?
	chan = twitch.channel.get(channel)
	ctxt = chan.getContext()
	if len(param) > 0:
		victim = param[0]
		return _serverText(ctxt, "%s has been timed out." % victim)
	else:
		if twitch.settings.get('twitch.honorclear'):
			hexchat.command('CLEAR')
		return _serverText(ctxt, "Chat was cleared by a moderator")
	
def HOSTTARGET(channel, param):
	# we started or stopped hosting another channel
	chan    = twitch.channel.get(channel)
	ctxt    = chan.getContext()
	dest    = param[0]
	viewers = param[1]
	if dest == '-':
		return _serverText(ctxt, "No longer hosting")
	else:
		return _serverText(ctxt,
			"Now hosting %s for %d viewers" % (dest,viewers))
	