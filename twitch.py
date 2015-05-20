#!/usr/bin/env python3
import hexchat
import logging
import sys
import os

__module_name__ = 'Twitch'
__module_author__ = 'RenaKunisaki & TingPing'
__module_version__ = '1'
__module_description__ = 'Better integration with Twitch.tv'

# append current path to module load path
sys.path.append(os.path.join(
	hexchat.get_info("configdir"), "addons"))

import twitch
log = twitch.logger.get('main')

# set up an unload hook
def unload_cb(userdata):
	twitch.shutdown()
	msg = "{} v{} unloaded".format(__module_name__, __module_version__)
	print(msg)
	logging.info(msg)
hexchat.hook_unload(unload_cb)

msg = "{} v{} loaded".format(__module_name__, __module_version__)
print(msg)
logging.info(msg)

twitch.run()
logging.info("{} v{} setup OK".format(__module_name__, __module_version__))
