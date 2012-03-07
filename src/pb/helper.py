import re

class Helper:
	
	@staticmethod
	def camelCaseToDash(s):
		s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
		return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
	
	@staticmethod
	def printOperations(operations):
		for op in operations:
			print Helper.camelCaseToDash(re.sub('@', '', op))

