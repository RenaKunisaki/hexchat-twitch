import hexchat
import logging
import datetime
import sys
import os

datefmt = "%y%m%d %H%M%S" # nice compact fixed-width format
now = datetime.datetime.now().strftime(datefmt)
debuglog = os.path.join(hexchat.get_info("configdir"),
	"addons", "twitch", "debug.log")
f = open(debuglog, 'wt', encoding='utf-8') # truncate the file
f.write("\n\n=== Logging started at %s ===\n\n" % now)
f.close()

logger = logging.getLogger('twitch')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
	'%(asctime)s %(name)s:%(lineno)d %(levelname)s: %(message)s', datefmt)

fh = logging.FileHandler(debuglog)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# XXX custom handler to log to a hexchat context,
# and prevent DEBUG level logging to current context

# existing loggers indexed by module name
loggers = {}

# get the logger for a module, creating it if it doesn't exist
# if no module name is provided, it automatically extracts from the caller's
# stack frame.
def get(moduleName=None):
	if moduleName is None:
		caller = sys._getframe(1)
		moduleName = caller.f_globals['__name__'].replace("twitch.", "", 1)
	
	if moduleName not in loggers:
		loggers[moduleName] = logging.getLogger("twitch." + moduleName)
		loggers[moduleName].setLevel(logging.WARNING)
	return loggers[moduleName]
	
	
# get the lgoger for a module but DON'T create it if it doesn't exist
def find(moduleName):
	return loggers.get(moduleName)
