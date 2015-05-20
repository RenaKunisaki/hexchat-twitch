import hexchat
from twitch.twitchOnly import twitchOnly

# friendly wrappers for hexchat.hook_* which pass the message type as userdata
# and wrap the callback with twitchOnly decorator

def command(msg, cb):
	return hexchat.hook_command(msg, twitchOnly(cb), msg)

def prnt(msg, cb): # print is a reserved word
	return hexchat.hook_print(msg, twitchOnly(cb), msg)

def server(msg, cb):
	return hexchat.hook_server(msg, twitchOnly(cb), msg)
	
def timer(timeout, cb):
	return hexchat.hook_timer(timeout, twitchOnly(cb))
