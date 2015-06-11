import hexchat
import logging
from twitch import irc
import twitch.user, twitch.channel, twitch.logger
import twitch.emotes
from twitch.exceptions import BadParameterError, UnknownCommandError
log = twitch.logger.get()

# used by twitchcmd_cb() to show command usage
def showCmdUsage(f):
	info  = f.command
	
	if 'usage' in info:
		cmd = irc.bold("/twitch %s %s" % (info['name'], info['usage']))
	else:
		cmd = irc.bold("/twitch %s" % info['name'])
	
	print("Usage: %s - %s" % (cmd, info['desc']))
	
	if 'detail' in info:
		detail = info['detail']
		if type(detail) is list:
			for line in detail:
				print(irc.format(line))
		else:
			print(irc.format(detail))
	
	if 'example' in info:
		print(irc.format("Example: %B/twitch %s%B") % info['example'])


# decorator, used to add information to command functions, which will be
# presented to the user when they ask for it.
# this also marks the function as being a command the user can invoke.
def command(info):
	def cmd_decorator(func):
		info['name'] = func.__name__
		func.command   = info
		
		if 'minparams' in info:
			minparams = info['minparams']
			def f(*args, **kwargs):
				if len(args[0]) < minparams:
					return showCmdUsage(func)
				else:
					return func(*args, **kwargs)
			f.command = func.command
			return f
		return func
	return cmd_decorator
	
	

################################################################################
def getLogLevel(logger=None):
	if logger is None:
		logger = logging.getLogger()
	return logging.getLevelName(logger.level)

@command({
	"usage" : "[module [level]]",
	"desc"  : "set or display debug logging level",
	"detail": [
		"Levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL",
		"module can be ALL, or one of the modules listed by " + \
			"%B/twitch loglevel%B",
	],
})
def loglevel(param, param_eol):
	modname = param[0].lower() if len(param) > 0 else None
	level   = param[1].upper() if len(param) > 1 else None
	loggers = twitch.logger.loggers
	
	# "loglevel" or "loglevel all": list all modules' levels
	if modname is None or (modname == 'all' and level is None):
		for mod, logger in sorted(loggers.items()):
			print("* %s: %s" % (mod, getLogLevel(logger)))
			
	elif level is None: # show single module
		if modname in loggers:
			print("* %s: %s" % (modname, getLogLevel(loggers[modname])))
		else:
			print("* %s: unknown module" % modname)
			
	else: # set module log level
		if modname == 'all':
			for mod, logger in sorted(loggers.items()):
				logger.setLevel(level)
			print("* All modules -> %s" % level)
		elif modname in loggers:
			logger = loggers[modname]
			oldLevel = getLogLevel(logger)
			logger.setLevel(level)
			print("* %s: %s -> %s" % (modname, oldLevel, level))
		else:
			print("* %s: unknown module" % modname)

	# XXX be able to change the log levels for output to file/console
	
	
################################################################################
@command({
	"usage"    : "level text...",
	"desc"     : "print text at specified debug log level",
	"minparams": 2,
})
def testlog(param, param_eol):
	level = logging.getLevelName(param[0].upper())
	log.log(level, param_eol[1])
	
		
################################################################################
@command({
	"usage"    : "command",
	"desc"     : "show help for a command",
	"minparams": 1,
})
def help(param, param_eol):
	if len(param) > 0:
		try:
			cmd = param[0]
			if not hasattr(twitch.commands, cmd):
				raise UnknownCommandError(cmd)

			f = getattr(twitch.commands, cmd)
			if not f.command:
				raise UnknownCommandError(cmd)
			
			showCmdUsage(f)
		except UnknownCommandError as ex:
			print("%s: Unknown command" % ex)
	else:
		showCmdUsage(help)
		
		

################################################################################
@command({
	"usage"  : "what which",
	"desc"   : "show info about a user or channel (mainly for debugging)",
	"example": "show channel xkeeper_",
})
def show(param, param_eol):
	if len(param) < 2:
		return showCmdUsage(show)
	what  = param[0]
	which = param[1]
	
	if what == 'user':
		print(twitch.user.get(which))
	elif what == 'channel':
		print(twitch.channel.get(which))
	else:
		raise BadParameterError("Unknown entity '%s'" % what)


################################################################################
@command({
	"usage"    : "emote [set|del|reload|list|show]",
	"desc"     : "manage Twitch emote display",
	"example"  : "emote set :) 😊",
	"minparams": 1,
})
def emote(param, param_eol):
	action = param[0]
	
	if action == 'set':
		if len(param) < 3:
			raise BadParameterError("Usage: emote set text replacement")
		twitch.emotes.set(param[1], param[2])
		twitch.emotes.save()
		print("* %s => %s" % (param[1], irc.format(param[2])))
	
	elif action == 'del':
		if len(param) < 2:
			raise BadParameterError("Usage: emote del name")
		twitch.emotes.delete(param[1])
		twitch.emotes.save()
		print("* %s deleted" % param[1])
	
	elif action == 'reload':
		twitch.emotes.load()
		print("* Loaded %d emotes" % len(twitch.emotes.emotes))
	
	elif action == 'list':
		for key in twitch.emotes.parsed_emotes:
			print("* %s => %s" % (key, twitch.emotes.parsed_emotes[key]))
	
	elif action == 'show':
		if len(param) < 2:
			raise BadParameterError("Usage: emote show name")
		name = param[1]
		if name in twitch.emotes.parsed_emotes:
			print("* %s => %s" % (name, twitch.emotes.parsed_emotes[name]))
		else:
			print("* No emote '%s' defined" % name)
	
	else:
		raise BadParameterError("Unknown action '%s'" % action)
		

################################################################################
@command({
	"usage"    : "echo text...",
	"desc"     : "echo text, for testing emotes and formats",
	"minparams": 1,
})
def echo(param, param_eol):
	print(irc.format(twitch.emotes.insert(param_eol[0])))
	
	
################################################################################
_eval = eval
@command({
	"usage"    : "eval expression...",
	"desc"     : "eval Python expression in twitch module context, for debugging",
	"minparams": 1,
})
def eval(param, param_eol):
	global _eval
	try:
		print(_eval(param_eol[0]))
	except Exception as ex:
		print(irc.color('red', 'Error: ' + str(ex)))
	
	
################################################################################
_exec = exec
@command({
	"usage"    : "exec code...",
	"desc"     : "execute Python code in twitch module context, for debugging",
	"minparams": 1,
})
def exec(param, param_eol):
	global _exec
	try:
		_exec(param_eol[0])
	except Exception as ex:
		print(irc.color('red', 'Error: ' + str(ex)))
