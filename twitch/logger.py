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


# existing loggers indexed by module name
loggers = {}


logger = logging.getLogger('twitch')
logger.setLevel(logging.DEBUG)
logger.propagate = False # do not fall back to default handler


# Formatter to format messages nicely
formatter = logging.Formatter(
	'%(asctime)s %(name)s:%(lineno)d %(levelname)s: %(message)s', datefmt)

	
# File handler to write to debug.log
fh = logging.FileHandler(debuglog)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


# Custom handler to write to a hexchat context.
# If no context is given, it logs to the currently active context.
class HexchatContextHandler(logging.StreamHandler):
	def __init__(self, ctxt=None):
		super().__init__()
		if ctxt is None:
			ctxt = hexchat
		self.ctxt = ctxt
		
	def emit(self, record):
		from twitch import irc
		msg   = self.format(record)
		level = '* twitch.logger.%s:' % logging.getLevelName(self.level)
		self.ctxt.emit_print("Generic Message", irc.color('red', level), msg)
	
	def flush(self):
		pass

# Log critical messages to the active context
crit_formatter = logging.Formatter( #we don't need level here
	'%(asctime)s %(name)s:%(lineno)d %(message)s', datefmt)
crit = HexchatContextHandler(None)
crit.setLevel(logging.CRITICAL)
crit.setFormatter(crit_formatter)
logger.addHandler(crit)

# XXX another handler to log non-critical messages to a separate context


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
