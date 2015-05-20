import requests

# exceptions we might get if the network breaks, which we'll deal with somehow
NetworkFailure = (
	requests.exceptions.ConnectionError,
	requests.exceptions.Timeout)
	
# used when user command has bad/missing parameters
class BadParameterError(ValueError):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

# used when user command doesn't exist
class UnknownCommandError(ValueError):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
