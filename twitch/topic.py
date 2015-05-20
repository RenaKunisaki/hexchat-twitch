import hexchat
import threading
import twitch.hook, twitch.channel, twitch.logger
log = twitch.logger.get()


# Don't show the "changed topic" message (but do update the topic bar)
def topic_print_cb(word, word_eol, msgtype):
	return hexchat.EAT_ALL


# work around hexchat bugs (likes to segfault when using RECV in other threads)
topic_changes = []
def topic_update_cb(userdata):
	try:
		while len(topic_changes) > 0:
			log.debug("%d updates queued" % len(topic_changes))
			topic = topic_changes.pop(0)
			log.debug("topic change: %s" % str(topic))
			
			cmd = "RECV :twitch.py!twitch@twitch.tv TOPIC #{0} :{1}"\
				.format(topic["channel"], topic["topic"])
			log.debug(cmd)
			
			hexchat.command(cmd)
			log.debug("Posted topic change OK")
	
	except:
		log.exception("Unhandled exception in twitch.topic_update_cb")
	
	finally:
		return True # keep timer running


# Thread callback to update a channel
def update_channel_thread(chan):
	try:
		if chan.update() and chan.makeTopic():
			log.debug("queue update for channel %s" % chan.name)
			topic_changes.append({
				"channel": chan.name,
				"topic"  : chan.topic,
			})
	except:
		log.exception("Unhandled exception in %s" %
			threading.current_thread().name)


# Periodically update channel info
def update_channels_cb(userdata):
	try:
		for name in twitch.channel.channels:
			log.debug("Update channel %s" % name)
			t = threading.Thread(
				target = update_channel_thread,
				args   = (twitch.channel.channels[name],),
				name   = "twitch.update_channel_thread(%s)" % name,
				daemon = True)
			t.start()
	except:
		log.exception("Unhandled exception in twitch.update_channels_cb")
	
	finally:
		return True # keep timer running
		
		
# Manually update a channel
def update_channel(chan):
	log.debug("manually queue update for channel %s" % chan.name)
	topic_changes.append({
		"channel": chan.name,
		"topic"  : chan.topic,
	})
		

def run():
	twitch.hook.prnt('Topic Change', topic_print_cb)
	twitch.hook.timer(1000, topic_update_cb)
	twitch.hook.timer(60000, update_channels_cb)
