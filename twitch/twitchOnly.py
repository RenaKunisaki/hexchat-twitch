import hexchat

# decorator: run only on Twitch IRC
# needed because hooks are global, so each hook callback needs to make sure
# it's only running on Twitch server contexts
def twitchOnly(func):
	def if_twitch(*args, **kwargs):
		for host in (hexchat.get_info('host'), hexchat.get_info('server')):
			if host and '.twitch.tv' in host:
				return func(*args, **kwargs)
		else:
			return hexchat.EAT_NONE
	return if_twitch
