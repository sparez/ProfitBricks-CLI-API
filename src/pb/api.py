import sys
import suds
import logging
from suds.transport.http import HttpAuthenticated
from suds.transport import Request

## We need to patch suds.client.SoapClient because it doesn't throw an exception in case of bad authentication
class SudsClientPatched(suds.client.SoapClient):
	_oldFailed = suds.client.SoapClient.failed
	def failed(self, binding, error):
		if error.httpcode == 500:
			return SudsClientPatched._oldFailed(self, binding, error)
		else:
			raise error
suds.client.SoapClient = SudsClientPatched
## End patch

class API:
	
	url = "https://api.profitbricks.com/1.1/wsdl"
	debug = False
	requestId = None
	
	def __init__(self, username, password, debug = False):
		self.debug = debug
		if debug:
			logging.getLogger("suds.server").setLevel(logging.DEBUG)
			logging.getLogger("suds.client").setLevel(logging.DEBUG)
			logging.getLogger("suds.transport").setLevel(logging.DEBUG)
		else:
			logging.getLogger('suds.client').setLevel(logging.CRITICAL) # hide soap faults

		try:
			self.client = suds.client.Client(url = self.url, username = username, password = password)
		except suds.transport.TransportError as (err):
			if err.httpcode == 401:
				print "Error: Invalid username or password"
			else:
				print "Error: Unknown error: %s" % str(err)
			sys.exit(3)
	
	# Calls the func() function using SOAP and the given arguments list (must always be an array)
	def call(self, func, args):
		if (self.debug):
			print "# Calling %s %s" % (func, args)
		try:
			method = getattr(self.client.service, func)
			result = method(*args)
			if self.requestId is None:
				if "requestId" in result:
					self.requestId = result["requestId"]
				else:
					self.requestId = "(no info)"
			return result
		except suds.WebFault as (err):
			print "Error: %s" % str(err)
			sys.exit(2)
		except suds.transport.TransportError as (err):
			if err.httpcode == 401:
				print "Error: Invalid username or password"
			else:
				print "Error: Unknown error: %s" % str(err)
			sys.exit(3)
	
	# Returns the userArgs hash, but replaces the keys with the values found in translation and only the ones found in translation
	# eg, parseArgs({"a": 10, "b": 20, "c": 30}, {"a": "a", "b": "B"}) => {"a": 10, "B": 20}
	def parseArgs(self, userArgs, translation):
		args = {}
		for i in translation:
			if i.lower() in userArgs:
				args[translation[i]] = userArgs[i.lower()]
		return args
	
	def getAllDataCenters(self):
		return self.call("getAllDataCenters", [])
	
	def getDataCenter(self, id):
		return self.call("getDataCenter", [id])
	
	def getServer(self, id):
		return self.call("getServer", [id])
	
	def createDataCenter(self, name):
		return self.call("createDataCenter", [name])
	
	def getDataCenterState(self, id):
		return self.call("getDataCenterState", [id])
	
	def updateDataCenter(self, userArgs):
		args = self.parseArgs(userArgs, {"dcid": "dataCenterId", "name": "dataCenterName"})
		return self.call("updateDataCenter", [args])
	
	def clearDataCenter(self, id):
		return self.call("clearDataCenter", [id])
	
	def deleteDataCenter(self, id):
		return self.call("deleteDataCenter", [id])
	
	def createServer(self, userArgs):
		args = self.parseArgs(userArgs, {"cores": "cores", "ram": "ram", "bootFromStorageId": "bootFromStorageId", "bootFromImageId": "bootFromImageId", "lanId": "lanId", "dcid": "dataCenterId", "name": "serverName"})
		if "ostype" in userArgs:
			args["osType"] = userArgs["ostype"].upper()
		if "internetaccess" in userArgs:
			args["internetAccess"] = (userArgs["internetaccess"][:1].lower() == "y")
		return self.call("createServer", [args])
	
	def rebootServer(self, id):
		return self.call("rebootServer", [id])
	
	def updateServer(self, userArgs):
		args = self.parseArgs(userArgs, {"srvid": "serverId", "name": "serverName", "cores": "cores", "ram": "ram", "bootFromImageId": "bootFromImageId", "bootFromStorageId": "bootFromStorageId", "osType": "osType"})
		return self.call("updateServer", [args])
	
	def deleteServer(self, id):
		return self.call("deleteServer", [id])
	
	def createStorage(self, userArgs):
		args = self.parseArgs(userArgs, {"dcid": "dataCenterId", "size": "size", "name": "storageName", "mountImageId": "mountImageId"})
		return self.call("createStorage", [args])
	
	def getStorage(self, id):
		return self.call("getStorage", [id])
	
	def connectStorageToServer(self, userArgs):
		args = self.parseArgs(userArgs, {"stoid": "storageId", "srvid": "serverId", "bus": "busType", "devnum": "deviceNumber"})
		args["busType"] = args["busType"].upper()
		return self.call("connectStorageToServer", [args])
	
	def disconnectStorageFromServer(self, stoId, srvId):
		return self.call("disconnectStorageFromServer", [stoId, srvId])
	
	def updateStorage(self, userArgs):
		args = self.parseArgs(userArgs, {"stoid": "storageId", "name": "storageName", "size": "size", "mountImageId": "mountImageId"})
		return self.call("updateStorage", [args])
	
	def deleteStorage(self, id):
		return self.call("deleteStorage", [id])
	
	def createLoadBalancer(self, userArgs):
		args = self.parseArgs(userArgs, {"dcid": "dataCenterId", "name": "loadBalancerName", "ip": "ip", "lanid": "lanId"})
		if "algo" in userArgs:
			args["loadBalancerAlgorithm"] = userArgs["algo"].upper()
		if "srvid" in userArgs:
			args["serverIds"] = ",".split(userArgs["srvid"])
		result = self.call("createLoadBalancer", [args])
		return result.loadBalancerId
	
	def getLoadBalancer(self, id):
		return self.call("getLoadBalancer", [id])
	
	def registerServersOnLoadBalancer(self, srvids, bid):
		return self.call("registerServersOnLoadBalancer", [srvids, bid])
	
	def deregisterServersOnLoadBalancer(self, srvids, bid):
		return self.call("deregisterServersOnLoadBalancer", [srvids, bid])
	
	def activateServersOnLoadBalancer(self, srvids, bid):
		return self.call("activateServersOnLoadBalancer", [srvids, bid])
	
	def deactivateServersOnLoadBalancer(self, srvids, bid):
		return self.call("deactivateServersOnLoadBalancer", [srvids, bid])
	
	def deleteLoadBalancer(self, id):
		return self.call("deleteLoadBalancer", [id])
	
	def addRomDriveToServer(self, userArgs):
		args = self.parseArgs(userArgs, {"imgid": "imageId", "srvid": "serverId", "devnum": "deviceNumber"})
		return self.call("addRomDriveToServer", [args])
	
	def removeRomDriveFromServer(self, id, srvid):
		return self.call("addRomDriveToServer", [id, srvid])
	
	def setImageOsType(self, imgid, ostype):
		return self.call("setImageOsType", [imgid, ostype])
	
	def getImage(self, id):
		return self.call("getImage", [id])
	
	def getAllImages(self):
		return self.call("getAllImages", [])
	
	def deleteImage(self, id):
		return self.call("deleteImage", [id])
	
	def createNIC(self, userArgs):
		args = self.parseArgs(userArgs, {"srvid": "serverId", "lanid": "lanId", "name": "nicName", "ip": "ip"})
		return self.call("createNic", [args])
	
	def getNIC(self, id):
		return self.call("getNic", [id])
	
	def setInternetAccess(self, dcid, lanid, internetAccess):
		return self.call("setInternetAccess", [dcid, lanid, internetAccess])
	
	def updateNIC(self, userArgs):
		args = self.parseArgs(userArgs, {"nicid": "nicId", "lanid": "lanId", "name": "nicName"})
		if "ip" in userArgs:
			args["ip"] = (userArgs["ip"] if userArgs["ip"].lower() != "reset" else "")
		return self.call("updateNic", [args])
	
	def deleteNIC(self, id):
		return self.call("deleteNic", [id])
	
	def reservePublicIPBlock(self, size):
		return self.call("reservePublicIpBlock", [size])
	
	def addPublicIPToNIC(self, ip, nicId):
		return self.call("addPublicIpToNic", [ip, nicId])
	
	def getAllPublicIPBlocks(self):
		result = self.call("getAllPublicIpBlocks", [])
		return result
	
	def removePublicIPFromNIC(self, ip, nicId):
		return self.call("removePublicIpFromNic", [ip, nicId])
	
	def releasePublicIPBlock(self, id):
		return self.call("releasePublicIpBlock", [id])
	
	def _parseFirewallRule(self, userRule):
		rule = self.parseArgs(userRule, {"smac": "sourceMac", "sip": "sourceIp", "dip": "targetIp", "icmptype": "icmpType", "icmpcode": "icmpCode"})
		if "proto" in userRule:
			rule["protocol"] = userRule["proto"].upper()
		if "port" in userRule:
			ports = userRule["port"].split(":")
			rule["portRangeStart"] = ports[0]
			rule["portRangeEnd"] = ports[len(ports) - 1]
		return rule
	
	def addFirewallRuleToNic(self, id, userRule):
		rule = self._parseFirewallRule(userRule)
		return self.call("addFirewallRuleToNic", [id, [rule]])
	
	def addFirewallRuleToLoadBalancer(self, id, userRule):
		rule = self._parseFirewallRule(userRule)
		return self.call("addFirewallRuleToLoadBalancer", [id, [rule]])
	

