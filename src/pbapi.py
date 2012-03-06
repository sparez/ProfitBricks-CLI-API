#!/usr/bin/python

#
# Copyright 2012 ProfitBricks GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sys
import suds
import re
from suds.transport.http import HttpAuthenticated
from suds.transport import Request

import logging
logging.basicConfig(level=logging.INFO)

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

class ProfitBricks:

	class ArgsError:
		
		def __init__(self, message = None):
			print "Invalid arguments" + ("" if message is None else ": " + message)
			sys.exit(1)
	
	class API:
		
		url = "https://api.profitbricks.com/1.1/wsdl"
		debug = False
		
		def __init__(self, username, password, debug = False):
			self.debug = debug
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
				return method(*args)
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
			args = self.parseArgs(userArgs, {"cores": "cores", "ram": "ram", "bootFromStorageId": "bootFromStorageId", "bootFromImageId": "bootFromImageId", "osType": "osType", "lanId": "lanId", "dcid": "dataCenterId", "name": "serverName"})
			if "internetAccess" in userArgs:
				args["internetAccess"] = ((userArgs["internetAccess"].lower() + "x")[0] == "y")
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
			return self.call("createNic", [args], {}) # TODO: Must get error messages from documentation
		
		def getNIC(self, id):
			return self.call("getNic", [id])
		
		def setInternetAccess(self, dcid, lanid, internetAccess):
			return self.call("setInternetAccess", [dcid, lanid, internetAccess])
		
		def updateNIC(self, userArgs):
			args = self.parseArgs(userArgs, {"nicid": "nicId", "lanid": "lanID", "ip": "ip", "name": "nicName"})
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
	
	class Formatter:
		
		indentValue = 0
		short = False
		
		def __init__(self):
			self.longFormat()
		
		def shortFormat(self):
			self.short = True
		
		def longFormat(self):
			self.short = False
		
		def indent(self, indentModification):
			if indentModification is None:
				return " " * self.indentValue
			else:
				self.indentValue += indentModification
		
		def out(self, outStr = "", *args):
			print ("\t" * self.indentValue) + outStr % args
		
		@staticmethod
		def requireArgs(soapResponse, requiredArgs, replaceMissingWith = "(none)"):
			result = {}
			for arg in requiredArgs:
				result[arg] = str(soapResponse[arg]) if arg in soapResponse else replaceMissingWith
			return result
		
		# Generic method, for many operations that don't give any response (except through HTTP, which is handled by ProfitBricks.API)
		def operationCompleted(self, response):
			self.out("Operation completed")
		
		printClearDataCenter = operationCompleted
		printUpdateDataCenter = operationCompleted
		printRebootServer = operationCompleted
		printDeleteDataCenter = operationCompleted
		printUpdateServer = operationCompleted
		printDeleteServer = operationCompleted
		printDeleteStorage = operationCompleted
		printConnectStorageToServer = operationCompleted
		printDisconnectStorageFromServer = operationCompleted
		printUpdateStorage = operationCompleted
		printAddRomDriveToServer = operationCompleted
		printRemoveRomDriveFromServer = operationCompleted
		printSetImageOsType = operationCompleted
		printDeleteImage = operationCompleted
		printCreateNIC = operationCompleted
		printEnableInternetAccess = operationCompleted
		printDisableInternetAccess = operationCompleted
		printUpdateNIC = operationCompleted
		printDeleteNIC = operationCompleted
		printAddPublicIPToNIC = operationCompleted
		printRemovePublicIPFromNIC = operationCompleted
		printReleasePublicIPBlock = operationCompleted
		
		def printCreateDataCenter(self, response):
			self.out("Data center ID: %s", response["dataCenterId"])
		
		def printCreateServer(self, response):
			self.out("Server ID: %s", response["serverId"])
		
		def printCreateStorage(self, response):
			self.out("Virtual storage ID: %s", response["storageId"])
		
		def printDataCenterState(self, response):
			self.out("Provisioning state: %s", response)
		
		def printAllDataCenters(self, dataCenters):
			if not self.short:
				self.out()
			self.out("%s %s %s", "Name".ljust(40), "Data Center ID".ljust(40), "Version".ljust(9))
			self.out("%s %s %s", "-" * 40, "-" * 40, "-" * 9)
			for dataCenter in dataCenters:
				dc = self.requireArgs(dataCenter, ["dataCenterName", "dataCenterId", "dataCenterVersion"]);
				self.out("%s %s %s", dc["dataCenterName"].ljust(40), dc["dataCenterId"].ljust(40), dc["dataCenterVersion"].ljust(9))
		
		def printNIC(self, apiNIC):
			nic = self.requireArgs(apiNIC, ["nicName", "nicId", "lanId", "internetAccess", "macAddress"])
			if self.short:
				self.out("%s (%s) => %s", nic["nicName"], "inet" if nic["internetAccess"].upper() == "TRUE" else "priv", " ; ".join(apiNIC.ips))
			else:
				self.out()
				self.out("Name: %s", nic["nicName"])
				self.out("NIC ID: %s", nic["nicId"])
				self.out("LAN ID: %s", nic["lanId"])
				self.out("Internet access: %s", "yes" if nic["internetAccess"] == "TRUE" else "no")
				self.out("IP Addresses: %s", " ; ".join(apiNIC.ips))
				self.out("MAC Address: %s", nic["macAddress"])
		
		def printServer(self, server):
			srv = self.requireArgs(server, ["serverName", "serverId", "creationTime", "lastModificationTime", "provisioningState", "virtualMachineState", "ram", "cores", "internetAccess", "osType"])
			if self.short:
				self.out("%s => %s is %s and %s", srv["serverName"], srv["serverId"], srv["provisioningState"], srv["virtualMachineState"])
				self.indent(1)
				self.out("%s Cores ; %s MiB RAM ; OS: %s ; Internet access [%s]", srv["cores"], srv["ram"], srv["osType"], "yes" if srv["internetAccess"].upper() == "TRUE" else "no")
				if "nics" in server:
					for nic in server.nics:
						self.printNIC(nic);
				self.indent(-1)
			else:
				self.out()
				self.out("Name: %s", srv["serverName"])
				self.out("Server ID: %s", srv["serverId"])
				self.out("Created: [%s] Modified: [%s]", srv["creationTime"], srv["lastModificationTime"])
				self.out("Provisioning state: %s", srv["provisioningState"])
				self.out("Virtual machine state: %s", srv["virtualMachineState"])
				self.out("Cores: %s", srv["cores"])
				self.out("RAM: %s MiB", srv["ram"])
				self.out("Internet access: %s", "yes" if srv["internetAccess"].upper() == "TRUE" else "no")
				self.out("Operating system: %s", srv["osType"])
				self.out("IP Addresses: %s", (" ; ".join(server.ips)) if "ips" in server else "-")
				if "nics" in server:
					self.indent(1)
					for nic in server.nics:
						self.printNIC(nic);
					self.indent(-1)
		
		def printStorage(self, storage):
			st = self.requireArgs(storage, ["storageName", "storageId", "provisioningState", "size", "osType"])
			if self.short:
				self.out("%s => %s is %s", st["storageName"], st["storageId"], st["provisioningState"])
				self.indent(1)
				self.out("Size: %s GiB", st["size"])
				self.out("Connected to VM ID: %s", (" ; ".join(storage.serverIds)) if "serverIds" in storage else "(none)")
				if "mountImage" in storage:
					self.printImage(storage.mountImage)
				else:
					self.out("(none)")
				self.indent(-1)
			else:
				self.out()
				self.out("Name: %s", st["storageName"])
				self.out("Storage ID: %s", st["storageId"])
				self.out("Size: %s GiB", st["size"])
				self.out("Connected to Virtual Servers: %s", (" ; ".join(storage.serverIds)) if "serverIds" in storage else "(none)")
				self.out("Provisioning state: %s", st["provisioningState"])
				self.out("Operating system: %s", st["osType"])
				self.out("Mount image:")
				self.indent(1)
				if "mountImage" in storage:
					self.printImage(storage.mountImage)
				else:
					self.out("No image")
				self.indent(-1)
		
		def _printImage(self, image):
			if self.short:
				self.out("Image %s (%s)", image["imageName"], image["imageId"])
			else:
				self.out()
				self.out("Name: %s", image["imageName"])
				self.out("Image ID: %s", image["imageId"])
		
		def printImage(self, image):
			if self.short:
				self.out("Image %s (%s)", image["imageName"], image["imageId"])
			else:
				self.out()
				self.out("Name: %s", image["imageName"])
				self.out("Image ID: %s", image["imageId"])
				self.out("Type: %s", image["imageType"])
				self.out("Writable: %s", "y" if image["writeable"] else "n")
				self.out("CPU hot plugging: %s", "y" if image["cpuHotpluggable"] else "n")
				self.out("Memory hot plugging: %s", "y" if image["memoryHotpluggable"] else "n")
				self.out("Server IDs: %s", (" ; ".join(image["serverIds"])) if "serverIds" in image else "(none)")
				self.out("OS Type: %s", image["osType"])
		
		def printAllImages(self, imageList):
			for i in imageList:
				self.printImage(i)
		
		def printDataCenter(self, dataCenter):
			dc = self.requireArgs(dataCenter, ["dataCenterName", "provisioningState", "dataCenterVersion"])
			if self.short:
				self.out("%s is %s", dc["dataCenterName"], dc["provisioningState"])
				self.out("Servers (%d):", len(dataCenter.servers) if "servers" in dataCenter else 0)
				self.indent(1);
				if "servers" in dataCenter:
					for server in dataCenter.servers:
						self.printServer(server)
				else:
					self.out("(none)")
				self.indent(-1);
				self.out("Storages (%s):", len(dataCenter.storages) if "storages" in dataCenter else 0)
				self.indent(1);
				if "storages" in dataCenter:
					for storage in dataCenter.storages:
						self.printStorage(storage)
				else:
					self.out("(none)")
				self.indent(-1);
			else:
				self.out()
				self.out("Name: %s", dc["dataCenterName"])
				self.out("Provisioning state: %s", dc["provisioningState"])
				self.out("Version: %s", dc["dataCenterVersion"])
				self.out()
				self.out("Servers (%d):", len(dataCenter.servers) if "servers" in dataCenter else 0)
				self.indent(1)
				if "servers" in dataCenter:
					for server in dataCenter.servers:
						self.printServer(server)
				else:
					self.out("(none)")
				self.indent(-1)
				self.out()
				self.out("Storages (%s):", len(dataCenter.storages) if "storages" in dataCenter else 0)
				self.indent(1);
				if "storages" in dataCenter:
					for storage in dataCenter.storages:
						self.printStorage(storage)
				else:
					self.out("(none)")
				self.indent(-1);
		
		def printPublicIPBlock(self, ipBlock):
			if not self.short:
				self.out()
			self.out("Block ID: %s", ipBlock["blockId"])
			self.out("IP addresses: %s", " ; ".join(ipBlock["ips"]))
		
		def printGetAllPublicIPBlocks(self, blockList):
			for ipBlock in blockList:
				ips = []
				for ipObj in ipBlock.publicIps:
					ips.append(ipObj.ip)
				self.printPublicIPBlock({"blockId": ipBlock.blockId, "ips": ips})
	
	class Helper:
	
		@staticmethod
		def camelCaseToDash(s):
			s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
			return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
		
		@staticmethod
		def printOperations(operations):
			for op in operations:
				if op[0] != "@":
					print ProfitBricks.Helper.camelCaseToDash(op)
			sys.exit(0)


## Parse arguments

# -u -p -auth -debug and -s are base arguments, everything else are operation arguments

baseArgs = {"s": False, "debug": False} # s = short output formatting
opArgs = {}
i = 1
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg == "-" or arg == "":
		i += 1
		continue
	# no dash = operation
	if arg[0] != "-":
		baseArgs["op"] = sys.argv[i]
		i += 1
		continue
	# base args
	if arg.lower() == "-u":
		if i == len(sys.argv) - 1:
			ProfitBricks.ArgsError("Missing username")
		baseArgs["u"] = sys.argv[i + 1]
		i += 1
	elif arg.lower() == "-p":
		if (i == len(sys.argv) - 1) or (sys.argv[i + 1][0] == "-"):
			import getpass
			baseArgs["p"] = getpass.getpass()
		else:
			baseArgs["p"] = sys.argv[i + 1]
		i += 1
	elif arg.lower() == "-auth":
		if i == len(sys.argv) - 1:
			ProfitBricks.ArgsError("Missing authfile")
		baseArgs["auth"] = sys.argv[i + 1]
		try:
			authFile = open(sys.argv[i + 1], "r")
			baseArgs["u"] = authFile.readline().strip("\n")
			baseArgs["p"] = authFile.readline().strip("\n")
			authFile.close()
		except:
			ProfitBricks.ArgsError("Authfile does not exist or cannot be read")
		i += 1
	elif arg.lower() == "-debug":
		baseArgs["debug"] = True
	elif arg.lower() == "-s":
		baseArgs["s"] = True
	# if not base arg, then it is operation arg
	else:
		opArgs[arg[1:].lower()] = (sys.argv[i + 1] if i < len(sys.argv) - 1 else "")
		i += 1
	i += 1

if "op" not in baseArgs:
	ProfitBricks.ArgsError("Missing operation")


## Define known operations

operations = {
	"createDataCenter": {
		"args": ["name"],
		"lambda": lambda: formatter.printCreateDataCenter(api.createDataCenter(opArgs["name"]))
	},
	"getDataCenter": {
		"args": ["dcid"],
		"lambda": lambda: formatter.printDataCenter(api.getDataCenter(opArgs["dcid"]))
	},
	"getDataCenterState": {
		"args": ["dcid"],
		"lambda": lambda: formatter.printDataCenterState(api.getDataCenterState(opArgs["dcid"]))
	},
	"getAllDataCenters": {
		"lambda": lambda: formatter.printAllDataCenters(api.getAllDataCenters())
	},
	"updateDataCenter": {
		"args": ["dcid"],
		"lambda": lambda: formatter.printUpdateDataCenter(api.updateDataCenter(opArgs))
	},
	"clearDataCenter": {
		"args": ["dcid"],
		"lambda": lambda: formatter.printClearDataCenter(api.clearDataCenter(opArgs["dcid"]))
	},
	"deleteDataCenter": {
		"args": ["dcid"],
		"lambda": lambda: formatter.printDeleteDataCenter(api.deleteDataCenter(opArgs["dcid"]))
	},
	"createServer": {
		"args": ["cores", "ram"],
		"lambda": lambda: formatter.printCreateServer(api.createServer(opArgs))
	},
	"getServer": {
		"args": ["srvid"],
		"lambda": lambda: formatter.printServer(api.getServer(opArgs["srvid"]))
	},
	"rebootServer": {
		"args": ["srvid"],
		"lambda": lambda: formatter.printRebootServer(api.rebootServer(opArgs["srvid"]))
	},
	"updateServer": {
		"args": ["srvid"],
		"lambda": lambda: formatter.printUpdateServer(api.updateServer(opArgs))
	},
	"deleteServer": {
		"args": ["srvid"],
		"lambda": lambda: formatter.printDeleteServer(api.deleteServer(opArgs["srvid"]))
	},
	"createStorage": {
		"args": ["size", "dcid"],
		"lambda": lambda: formatter.printCreateStorage(api.createStorage(opArgs))
	},
	"getStorage": {
		"args": ["stoid"],
		"lambda": lambda: formatter.printStorage(api.getStorage(opArgs["stoid"]))
	},
	"connectStorageToServer": {
		"args": ["stoid", "srvid", "bus"],
		"lambda": lambda: formatter.printConnectStorageToServer(api.connectStorageToServer(opArgs))
	},
	"disconnectStorageFromServer": {
		"args": ["stoid", "srvid"],
		"lambda": lambda: formatter.printDisconnectStorageFromServer(api.disconnectStorageFromServer(opArgs["stoid"], opArgs["srvid"]))
	},
	"updateStorage": {
		"args": ["stoid"],
		"lambda": lambda: formatter.printUpdateStorage(api.updateStorage(opArgs))
	},
	"deleteStorage": {
		"args": ["stoid"],
		"lambda": lambda: formatter.printDeleteStorage(api.deleteStorage(opArgs["stoid"]))
	},
	"addRomDriveToServer": {
		"args": ["imgid", "srvid"],
		"lambda": lambda: formatter.printAddRomDriveToServer(api.addRomDriveToServer(opArgs))
	},
	"removeRomDriveFromServer": {
		"args": ["imgid", "srvid"],
		"lambda": lambda: formatter.printRemoveRomDriveFromServer(api.removeRomDriveFromServer(opArgs))
	},
	"setImageOsType": {
		"args": ["imgid", "ostype"],
		"lambda": lambda: formatter.printSetImageOsType(api.setImageOsType(opArgs["imgid"], opArgs["ostype"]))
	},
	"getImage": {
		"args": ["imgid"],
		"lambda": lambda: formatter.printImage(api.getImage(opArgs["imgid"]))
	},
	"getAllImages": {
		"args": [],
		"lambda": lambda: formatter.printAllImages(api.getAllImages())
	},
	"deleteImage": {
		"args": ["imgid"],
		"lambda": lambda: formatter.printDeleteImage(api.deleteImage(opArgs["imgid"]))
	},
	"createNIC": {
		"args": ["srvid", "lanid"],
		"lambda": lambda: formatter.printCreateNIC(api.createNIC(opArgs))
	},
	"getNIC": {
		"args": ["nicid"],
		"lambda": lambda: formatter.printNIC(api.getNIC(opArgs["nicid"]))
	},
	"enableInternetAccess": {
		"args": ["dcid", "lanid"],
		"lambda": lambda: formatter.printEnableInternetAccess(api.setInternetAccess(opArgs["dcid"], opArgs["lanid"], True))
	},
	"disableInternetAccess": {
		"args": ["dcid", "lanid"],
		"lambda": lambda: formatter.printDisableInternetAccess(api.setInternetAccess(opArgs["dcid"], opArgs["lanid"], False))
	},
	"updateNic": {
		"args": ["nicid", "lanid"],
		"lambda": lambda: formatter.printUpdateNIC(api.updateNIC(opArgs))
	},
	"deleteNic": {
		"args": ["nicid"],
		"lambda": lambda: formatter.printDeleteNIC(api.deleteNIC(opArgs["nicid"]))
	},
	"reservePublicIpBlock": {
		"args": ["size"],
		"lambda": lambda: formatter.printPublicIPBlock(api.reservePublicIPBlock(opArgs["size"]))
	},
	"addPublicIpToNic": {
		"args": ["ip", "nicid"],
		"lambda": lambda: formatter.printAddPublicIPToNIC(api.addPublicIPToNIC(opArgs["ip"], opArgs["nicid"]))
	},
	"getAllPublicIpBlocks": {
		"args": [],
		"lambda": lambda: formatter.printGetAllPublicIPBlocks(api.getAllPublicIPBlocks())
	},
	"removePublicIpFromNic": {
		"args": ["ip", "nicid"],
		"lambda": lambda: formatter.printRemovePublicIPFromNIC(api.removePublicIPFromNIC(opArgs["ip"], opArgs["nicid"]))
	},
	"releasePublicIpBlock": {
		"args": ["blockid"],
		"lambda": lambda: formatter.printReleasePublicIPBlock(api.releasePublicIPBlock(opArgs["blockid"]))
	},
	"@list": {
		"args": [],
		"lambda": lambda: ProfitBricks.Helper.printOperations(operations)
	}
}

## Load auth from default.auth if exists

if "u" not in baseArgs or "p" not in baseArgs:
	try:
		authFile = open("default.auth", "r")
		baseArgs["u"] = authFile.readline().strip("\n")
		baseArgs["p"] = authFile.readline().strip("\n")
		authFile.close()
	except:
		pass


## Find requested operation

opFound = None
userOperation = baseArgs["op"].replace("-", "").lower()
for op in operations:
	if userOperation == op.replace("-", "").lower() or '@' + userOperation == op.replace("-", "").lower():
		if "args" in operations[op]:
			for requiredArg in operations[op]["args"]:
				if not requiredArg in opArgs or opArgs[requiredArg] == "":
					args = ""
					for requiredArg in operations[op]["args"]:
						args = args + "-" + requiredArg + " "
					ProfitBricks.ArgsError("operation '%s' requires these arguments: %s" % (baseArgs["op"], args)) # '%s'" % (baseArgs["op"], "-" + requiredArg))
		opFound = op

if opFound is None:
	print sys.argv
	print "Unknown operation:", baseArgs["op"]
	sys.exit(2)


if opFound[0] != "@": # @ operations don't require authentication
	## Instantiate API and API output formatter
	
	if "u" not in baseArgs or "p" not in baseArgs:
		ProfitBricks.ArgsError("Missing authentication")
	
	api = ProfitBricks.API(baseArgs["u"], baseArgs["p"], debug = baseArgs["debug"])
	formatter = ProfitBricks.Formatter()
	if baseArgs["s"]:
		formatter.shortFormat()
	if baseArgs["debug"] == True:
		logging.getLogger("suds.server").setLevel(logging.DEBUG)
		logging.getLogger("suds.client").setLevel(logging.DEBUG)
		logging.getLogger("suds.transport").setLevel(logging.DEBUG)
	else:
		logging.getLogger('suds.client').setLevel(logging.CRITICAL) # hide soap faults


## Perform operation

operations[opFound]["lambda"]()

