import hexchat
import math
import re
import twitch.logger
log = twitch.logger.get()

# default IRC colours
colors = {
	"white":     0,
	"black":     1,
	"blue":      2,
	"green":     3,
	"red":       4,
	"brown":     5,
	"dkpurple":  6,
	"orange":    7,
	"yellow":    8,
	"lime":      9,
	"aqua":     10,
	"teal":     11,
	"purple":   12,
	"pink":     13,
	"dkgray":   14,
	"dkgrey":   14,
	"gray":     15,
	"grey":     15,
}
for i in range(16): colors[i] = i # colors[n] = n

# the actual RGB of those colours
colors_rgb = [
	(255, 255, 255), # white
	(  0,   0,   0), # black
	(  0,   0, 127), # blue
	(  0, 147,   0), # green
	(255,   0,   0), # light red
	(127,   0,   0), # brown
	(156,   0, 156), # purple
	(252, 127,   0), # orange
	(255, 255,   0), # yellow
	(  0, 252,   0), # light green
	(  0, 147, 147), # cyan
	(  0, 255, 255), # light cyan
	(  0,   0, 252), # light blue
	(255,   0, 255), # pink
	(127, 127, 127), # grey
	(210, 210, 210), # light grey
]

# from http://www.compuphase.com/cmetric.htm
# compute distance between two RGB colours
# expects (r, g, b) in range 0-255
def colorDistance(A, B):
	rmean = int((A[0] + B[0]) / 2)
	r = A[0] - B[0]
	g = A[1] - B[1]
	b = A[2] - B[2]
	return math.sqrt((((512+rmean)*r*r)>>8) + 4*g*g + (((767-rmean)*b*b)>>8))
	

# map HTML colour ("#FF00FF") to IRC colour index
def mapColor(col):
	col = bytearray.fromhex(col[1:]) # strip leading '#'
	col = (col[0], col[1], col[2]) # byte array to tuple
	
	match = colors['grey'] # default
	dist  = 99999999
	for i in range(len(colors_rgb)):
		d = colorDistance(col, colors_rgb[i])
		if d < dist:
			dist  = d
			match = i
	return match


# make some text bold.
# if not given any text, just returns the formatting code to toggle bold.
def bold(*text):
	if len(text) == 0:
		return "\x02"
	else:
		return "\x02%s\x02" % text[0]
		
# underline some text.
def underline(*text):
	if len(text) == 0:
		return "\x1F"
	else:
		return "\x1F%s\x1F" % text[0]
		
# make some text italic (or inverted).
def italic(*text):
	if len(text) == 0:
		return "\x1D"
	else:
		return "\x1D%s\x1D" % text[0]

# colour some text.
# col is either a string naming a colour from above,
# or a tuple of (fg) or (fg,bg).
# if not given any text, just returns the formatting code to set that colour.
def color(col, *text):
	if type(col) is tuple:
		if len(col) > 1:
			fmt = "\x03%02d,%02d" % (colors[col[0]], colors[col[1]])
		else:
			fmt = "\x03%02d" % (colors[col[0]])
	else:
		fmt = "\x03%02d" % (colors[col])
	
	if len(text) == 0:
		return fmt
	else:
		return "%s%s\x0F" % (fmt, text[0]) # XXX better "end colour" code?
		

fmtcode = { # find => replace
	"%B": "\x02", # bold
	"%I": "\x1D", # italic (displays as inverted on some clients)
	"%U": "\x1F", # underline
	"%R": "\x0F", # reset all attributes
}
re_attrs = re.compile(r"(%[BIUR])")
re_color = re.compile(r"(%C\(([\w,]+)\))")

def _repl(match): # replace callback
	code = match.group(1)
	if code.startswith('%C'): # colour
		cols = []
		for name in match.group(2).split(','): #extract colours
			col = None
			if name.isdigit(): # allow specifying colours by number
				idx = int(name)
				if idx >= 0 and idx <= 99: col = idx
			elif name in colors:
				col = colors[name]
			
			if col is None:
				raise ValueError("Unknown color '%s'" % name)
			else:
				cols.append("%02d" % col)
		#log.debug("color: %s => %s" % (match.group(2), cols))
		return "\x03" + (",".join(cols))
	
	elif code in fmtcode: # not a colour code
		return fmtcode[code]
	else:
		return code

# replace formatting codes in some text.
def format(text):
	text = re_attrs.sub(_repl, text) # do normal attributes
	text = re_color.sub(_repl, text) # do dual colours: %C(red,blue)
	return text
	
	
# output some text to a hexchat context.
def emit_print(ctxt, msgtype, *args):
	if ctxt is None:
		ctxt = hexchat
	elif "<hexchat.Context object" not in str(name): #HACK XXX - is channel obj?
		ctxt = ctxt.getContext()
	
	ctxt.emit_print(msgtype, *args)
