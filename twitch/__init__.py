import twitch.logger, twitch.hooks, twitch.user, twitch.topic, twitch.emotes
import twitch.settings, twitch.channel
import hexchat
log = twitch.logger.get()

def run():
	twitch.settings.load()
	twitch.hooks.install()
	twitch.emotes.load()
	twitch.topic.run()
	for chan in hexchat.get_list('channels'):
		if '.twitch.tv' in chan.server:
			c = twitch.channel.get(chan.channel)
			c.join()
	
def shutdown():
	twitch.settings.save()
	for nick, user in twitch.user.users.items():
		user.save()
	log.info("Script unloaded")
