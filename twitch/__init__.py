import twitch.logger, twitch.hooks, twitch.user, twitch.topic, twitch.emotes
import twitch.settings

def run():
	twitch.settings.load()
	twitch.hooks.install()
	twitch.emotes.load()
	twitch.topic.run()
	
def shutdown():
	twitch.settings.save()
	for nick, user in twitch.user.users.items():
		user.save()
