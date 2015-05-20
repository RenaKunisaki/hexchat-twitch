import hexchat
import requests
import twitch.normalize, twitch.logger
log = twitch.logger.get()

def get(params):
	method = 'GET'
	if 'method' in params:
		method = params['method']
	r = requests.request(method, **params)
	return r.json()

def getUser(nick):
	nick = twitch.normalize.nick(nick)
	url = "https://api.twitch.tv/kraken/users/" + nick
	return get({"url":url})
		
def getChannel(name):
	name = twitch.normalize.channel(name)
	url = "https://api.twitch.tv/kraken/streams"
	return get({
		"url": url,
		"params": {"channel":name},
	})
