import sys

class ArgsError:
	
	def __init__(self, message = None):
		print "Invalid arguments" + ("" if message is None else ": " + message)
		sys.exit(1)


