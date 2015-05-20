import twitch.logger, twitch.hooks, twitch.user, twitch.topic, twitch.emotes

def run():
	twitch.hooks.install()
	twitch.emotes.load()
	twitch.topic.run()
	
def shutdown():
	for nick, user in twitch.user.users.items():
		user.save()
