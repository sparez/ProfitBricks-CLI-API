import re

class Helper:
	
	@staticmethod
	def camelCaseToDash(s):
		s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
		return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
	
	@staticmethod
	def printOperations(operations):
		print "Available operations and mandatory arguments:"
		for op in sorted(operations):
			print ":",\
				Helper.camelCaseToDash(re.sub('@', '', op)),\
				("(-" + " -".join(operations[op]["args"]) + ")") if len(operations[op]["args"]) > 0 else "",\
				"(internal)" if re.search("@", op) else ""

