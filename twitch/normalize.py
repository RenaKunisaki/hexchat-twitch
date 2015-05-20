import hexchat
import twitch.user, twitch.channel

def nick(n):
	if type(n) is twitch.user.user:
		return n.nick
	elif type(n) is twitch.channel.channel: # each user has their own channel
		return n.name
	else:
		return hexchat.strip(n).lower()
	
def channel(c):
	if type(c) is twitch.channel.channel:
		return c.name
	elif type(c) is twitch.user.user:
		return c.nick
	else:
		c = hexchat.strip(c).lower()
		if c[0] == '#':
			c = c[1:]
		return c
