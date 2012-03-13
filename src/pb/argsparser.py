import sys
import errorhandler

class ArgsParser:
	
	def __init__(self):
		self.baseArgs = {"s": False, "debug": False} # s = short output formatting
		self.opArgs = {}
	
	def readUserArgs(self):
		i = 1
		# -u -p -auth -debug and -s are base arguments, everything else are operation arguments
		while i < len(sys.argv):
			arg = sys.argv[i]
			if arg == "-" or arg == "":
				i += 1
				continue
			# no dash = operation
			if arg[0] != "-":
				self.baseArgs["op"] = sys.argv[i]
				i += 1
				continue
			# base args
			if arg.lower() == "-u":
				if i == len(sys.argv) - 1:
					ProfitBricks.ArgsError("Missing username")
				self.baseArgs["u"] = sys.argv[i + 1]
				i += 1
			elif arg.lower() == "-p":
				if (i == len(sys.argv) - 1) or (sys.argv[i + 1][0] == "-"):
					import getpass
					self.baseArgs["p"] = getpass.getpass()
				else:
					self.baseArgs["p"] = sys.argv[i + 1]
				i += 1
			elif arg.lower() == "-auth":
				if i == len(sys.argv) - 1:
					ProfitBricks.ArgsError("Missing authfile")
				self.baseArgs["auth"] = sys.argv[i + 1]
				try:
					authFile = open(sys.argv[i + 1], "r")
					self.baseArgs["u"] = authFile.readline().strip("\n")
					self.baseArgs["p"] = authFile.readline().strip("\n")
					authFile.close()
				except:
					ProfitBricks.ArgsError("Authfile does not exist or cannot be read")
				i += 1
			elif arg.lower() == "-debug":
				self.baseArgs["debug"] = True
			elif arg.lower() == "-s":
				self.baseArgs["s"] = True
			# if not base arg, then it is operation arg
			else:
				self.opArgs[arg[1:].lower()] = (sys.argv[i + 1] if i < len(sys.argv) - 1 else "")
				i += 1
			i += 1
		
		if "op" not in self.baseArgs:
			errorhandler.ArgsError("Missing operation")
		
		self._loadAuthFile()
	
	def getRequestedOperation(self):
		userOperation = self.baseArgs["op"].replace("-", "").lower()
		for op in ArgsParser.operations:
			if '@' + userOperation == op.replace("-", "").lower():
				return op
			if userOperation != op.replace("-", "").lower():
				continue
			for requiredArg in ArgsParser.operations[op]["args"]:
				if not requiredArg in self.opArgs:
					errorhandler.ArgsError("operation '%s' requires these arguments: -%s" % (self.baseArgs["op"], " -".join(ArgsParser.operations[op]["args"])))
			return op
		return None
	
	def _loadAuthFile(self):
		if "u" not in self.baseArgs or "p" not in self.baseArgs:
			try:
				authFile = open("default.auth", "r")
				self.baseArgs["u"] = authFile.readline().strip("\n")
				self.baseArgs["p"] = authFile.readline().strip("\n")
				authFile.close()
			except:
				pass
	
	def isAuthenticated(self):
		return "u" in self.baseArgs and "p" in self.baseArgs
	
	operations = {
			"createDataCenter": {
				"args": ["name"],
				"lambda": lambda formatter, api, opArgs: formatter.printCreateDataCenter(api.createDataCenter(opArgs["name"]))
			},
			"getDataCenter": {
				"args": ["dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDataCenter(api.getDataCenter(opArgs["dcid"]))
			},
			"getDataCenterState": {
				"args": ["dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDataCenterState(api.getDataCenterState(opArgs["dcid"]))
			},
			"getAllDataCenters": {
				"args": [],
				"lambda": lambda formatter, api, opArgs: formatter.printAllDataCenters(api.getAllDataCenters())
			},
			"updateDataCenter": {
				"args": ["dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printUpdateDataCenter(api.updateDataCenter(opArgs))
			},
			"clearDataCenter": {
				"args": ["dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printClearDataCenter(api.clearDataCenter(opArgs["dcid"]))
			},
			"deleteDataCenter": {
				"args": ["dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeleteDataCenter(api.deleteDataCenter(opArgs["dcid"]))
			},
			"createServer": {
				"args": ["cores", "ram"],
				"lambda": lambda formatter, api, opArgs: formatter.printCreateServer(api.createServer(opArgs))
			},
			"getServer": {
				"args": ["srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printServer(api.getServer(opArgs["srvid"]))
			},
			"rebootServer": {
				"args": ["srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printRebootServer(api.rebootServer(opArgs["srvid"]))
			},
			"updateServer": {
				"args": ["srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printUpdateServer(api.updateServer(opArgs))
			},
			"deleteServer": {
				"args": ["srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeleteServer(api.deleteServer(opArgs["srvid"]))
			},
			"createStorage": {
				"args": ["size", "dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printCreateStorage(api.createStorage(opArgs))
			},
			"getStorage": {
				"args": ["stoid"],
				"lambda": lambda formatter, api, opArgs: formatter.printStorage(api.getStorage(opArgs["stoid"]))
			},
			"connectStorageToServer": {
				"args": ["stoid", "srvid", "bus"],
				"lambda": lambda formatter, api, opArgs: formatter.printConnectStorageToServer(api.connectStorageToServer(opArgs))
			},
			"disconnectStorageFromServer": {
				"args": ["stoid", "srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDisconnectStorageFromServer(api.disconnectStorageFromServer(opArgs["stoid"], opArgs["srvid"]))
			},
			"updateStorage": {
				"args": ["stoid"],
				"lambda": lambda formatter, api, opArgs: formatter.printUpdateStorage(api.updateStorage(opArgs))
			},
			"deleteStorage": {
				"args": ["stoid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeleteStorage(api.deleteStorage(opArgs["stoid"]))
			},
			"createLoadBalancer": {
				"args": ["dcid"],
				"lambda": lambda formatter, api, opArgs: formatter.printCreateLoadBalancer(api.createLoadBalancer(opArgs))
			},
			"getLoadBalancer": {
				"args": ["bid"],
				"lambda": lambda formatter, api, opArgs: formatter.printLoadBalancer(api.getLoadBalancer(opArgs["bid"]))
			},
			"registerServersOnLoadBalancer": {
				"args": ["srvid", "bid"],
				"lambda": lambda formatter, api, opArgs: formatter.printRegisterServersOnLoadBalancer(api.registerServersOnLoadBalancer(",".split(opArgs["srvid"]), opArgs["bid"]))
			},
			"deregisterServersOnLoadBalancer": {
				"args": ["srvid", "bid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeregisterServersOnLoadBalancer(api.deregisterServersOnLoadBalancer(",".split(opArgs["srvid"]), opArgs["bid"]))
			},
			"activateLoadBalancingOnServer": {
				"args": ["srvid", "bid"],
				"lambda": lambda formatter, api, opArgs: formatter.printActivateLoadBalancingOnServers(api.activateLoadBalancingOnServer(",".split(opArgs["srvid"]), opArgs["bid"]))
			},
			"deactivateLoadBalancingOnServer": {
				"args": ["srvid", "bid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeactivateLoadBalancingOnServers(api.deactivateLoadBalancingOnServer(",".split(opArgs["srvid"]), opArgs["bid"]))
			},
			"deleteLoadBalancer": {
				"args": ["bid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeleteLoadBalancer(api.deleteLoadBalancer(opArgs["bid"]))
			},
			"addRomDriveToServer": {
				"args": ["imgid", "srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printAddRomDriveToServer(api.addRomDriveToServer(opArgs))
			},
			"removeRomDriveFromServer": {
				"args": ["imgid", "srvid"],
				"lambda": lambda formatter, api, opArgs: formatter.printRemoveRomDriveFromServer(api.removeRomDriveFromServer(opArgs))
			},
			"setImageOsType": {
				"args": ["imgid", "ostype"],
				"lambda": lambda formatter, api, opArgs: formatter.printSetImageOsType(api.setImageOsType(opArgs["imgid"], opArgs["ostype"]))
			},
			"getImage": {
				"args": ["imgid"],
				"lambda": lambda formatter, api, opArgs: formatter.printImage(api.getImage(opArgs["imgid"]))
			},
			"getAllImages": {
				"args": [],
				"lambda": lambda formatter, api, opArgs: formatter.printAllImages(api.getAllImages())
			},
			"deleteImage": {
				"args": ["imgid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeleteImage(api.deleteImage(opArgs["imgid"]))
			},
			"createNIC": {
				"args": ["srvid", "lanid"],
				"lambda": lambda formatter, api, opArgs: formatter.printCreateNIC(api.createNIC(opArgs))
			},
			"getNIC": {
				"args": ["nicid"],
				"lambda": lambda formatter, api, opArgs: formatter.printNIC(api.getNIC(opArgs["nicid"]))
			},
			"enableInternetAccess": {
				"args": ["dcid", "lanid"],
				"lambda": lambda formatter, api, opArgs: formatter.printEnableInternetAccess(api.setInternetAccess(opArgs["dcid"], opArgs["lanid"], True))
			},
			"disableInternetAccess": {
				"args": ["dcid", "lanid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDisableInternetAccess(api.setInternetAccess(opArgs["dcid"], opArgs["lanid"], False))
			},
			"updateNic": {
				"args": ["nicid", "lanid"],
				"lambda": lambda formatter, api, opArgs: formatter.printUpdateNIC(api.updateNIC(opArgs))
			},
			"deleteNic": {
				"args": ["nicid"],
				"lambda": lambda formatter, api, opArgs: formatter.printDeleteNIC(api.deleteNIC(opArgs["nicid"]))
			},
			"reservePublicIpBlock": {
				"args": ["size"],
				"lambda": lambda formatter, api, opArgs: formatter.printPublicIPBlock(api.reservePublicIPBlock(opArgs["size"]))
			},
			"addPublicIpToNic": {
				"args": ["ip", "nicid"],
				"lambda": lambda formatter, api, opArgs: formatter.printAddPublicIPToNIC(api.addPublicIPToNIC(opArgs["ip"], opArgs["nicid"]))
			},
			"getAllPublicIpBlocks": {
				"args": [],
				"lambda": lambda formatter, api, opArgs: formatter.printGetAllPublicIPBlocks(api.getAllPublicIPBlocks())
			},
			"removePublicIpFromNic": {
				"args": ["ip", "nicid"],
				"lambda": lambda formatter, api, opArgs: formatter.printRemovePublicIPFromNIC(api.removePublicIPFromNIC(opArgs["ip"], opArgs["nicid"]))
			},
			"releasePublicIpBlock": {
				"args": ["blockid"],
				"lambda": lambda formatter, api, opArgs: formatter.printReleasePublicIPBlock(api.releasePublicIPBlock(opArgs["blockid"]))
			},
			"@list": {
				"args": [],
				"lambda": lambda helper: helper.printOperations(ArgsParser.operations)
			},
			"@list-simple": {
				"args": [],
				"lambda": lambda helper: helper.printOperationsSimple(ArgsParser.operations)
			}
		}



