import sys

should_exit_python = True

def last_error():
	tmp = last_error.last
	last_error.last = 0
	return tmp
last_error.last = 0

def exit(level = 0):
	# 0 = ok
	# 1 = args error
	# 2 = authentication error
	# 3 = soap fault
	if should_exit_python:
		sys.exit(level)
	if last_error.last == 0:
		last_error.last = level

class ArgsError:
	
	def __init__(self, message = None):
		print "Invalid arguments" + ("" if message is None else ": " + message)
		exit(1)

