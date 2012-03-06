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
from suds.transport.http import HttpAuthenticated
from suds.transport import Request

import logging
logging.basicConfig(level=logging.INFO)

class ProfitBricks:

	class APIError:
		
		codeToError = {
			0: "UNKNOWN_ERROR",
			400: "BAD_REQUEST",
			401: "UNAUTHORIZED",
			404: "RESOURCE_NOT_FOUND",
			409: "PROVISIONING_IN_PROGRESS",
			410: "RESOURCE_DELETED",
			413: "OVER_LIMIT_SETTING",
			503: "SERVER_EXCEEDED_CAPACITY",
		}
		
		defaultErrorMessages = {
			"UNKNOWN_ERROR": "Unknown error",
			"BAD_REQUEST": "Invalid name parameters, missing mandatory parameters, etc",
			"UNAUTHORIZED": "The request resource does not exist or this user is not authorized to access it",
			"PROVISIONING_IN_PROGRESS": "Operation cannot be executed. The user has to wait, until the provisioning process is finished and the data center is available again",
			"RESOURCE_NOT_FOUND": "Resource not found",
			"OVER_LIMIT_SETTING": "Too many resources"
		}
		
		def __init__(self, transportError, customErrorMessages = {}):
			code = int(transportError.fault.detail.ProfitbricksServiceFault.httpCode)
			error = self.codeToError[code if code in self.codeToError else 0]
			errorMessage = customErrorMessages[error] if error in customErrorMessages else self.defaultErrorMessages[error]
			print "Error %d: %s: %s." % (code, error, errorMessage)
			sys.exit(2)
	
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
				ProfitBricks.APIError(err, {"UNAUTHORIZED": "Invalid username or password"});
		
		# Calls the func() function using SOAP and the given arguments list (must always be an array)
		# If the call fails, the customErrorMessages hash will be used to extend the ProfitBricks.APIError.defaultErrorMessages hash (for making errors more human-readable)
		def call(self, func, args, customErrorMessages):
			if (self.debug):
				print "# Calling %s %s" % (func, args)
			try:
				method = getattr(self.client.service, func)
				return method(*args)
			except suds.WebFault as (err):
				ProfitBricks.APIError(err, customErrorMessages)
		
		# Returns the userArgs hash, but replaces the keys with the values found in translation and only the ones found in translation
		# eg, parseArgs({"a": 10, "b": 20, "c": 30}, {"a": "a", "b": "B"}) => {"a": 10, "B": 20}
		def parseArgs(self, userArgs, translation):
			args = {}
			for i in translation:
				if i.lower() in userArgs:
					args[translation[i]] = userArgs[i.lower()]
			return args
		
		def getAllDataCenters(self):
			return self.call("getAllDataCenters", [], {})
		
		def getDataCenter(self, id):
			return self.call("getDataCenter", [id], {"RESOURCE_NOT_FOUND": "Data Center does not exist"})
		
		def getServer(self, id):
			return self.call("getServer", [id], {"RESOURCE_NOT_FOUND": "Data Center does not exist"})
		
		def createDataCenter(self, name):
			return self.call("createDataCenter", [name], {"BAD_REQUEST": "Invalid characters in DataCenter name"})
		
		def getDataCenterState(self, id):
			return self.call("getDataCenterState", [id], {"RESOURCE_NOT_FOUND": "DataCenter does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter"})
		
		def updateDataCenter(self, userArgs):
			args = self.parseArgs(userArgs, {"dcid": "dataCenterId", "name": "dataCenterName"})
			errors = {"BAD_REQUEST": "Invalid characters in DataCenter name", "RESOURCE_NOT_FOUND": "Specified DataCenter ID does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter"}
			return self.call("updateDataCenter", [args], errors)
		
		def clearDataCenter(self, id):
			errors = {"RESOURCE_NOT_FOUND": "DataCenter does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter"}
			return self.call("clearDataCenter", [id], errors)
		
		def deleteDataCenter(self, id):
			errors = {"RESOURCE_NOT_FOUND": "DataCenter does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter", "BAD_REQUEST": "DataCenter is not empty"}
			return self.call("deleteDataCenter", [id], errors)
		
		def createServer(self, userArgs):
			args = self.parseArgs(userArgs, {"cores": "cores", "ram": "ram", "bootFromStorageId": "bootFromStorageId", "bootFromImageId": "bootFromImageId", "osType": "osType", "lanId": "lanId", "dcid": "dataCenterId", "name": "serverName"})
			if "internetAccess" in userArgs:
				args["internetAccess"] = ((userArgs["internetAccess"].lower() + "x")[0] == "y")
			errors = {"RESOURCE_NOT_FOUND": "Boot media does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server", "BAD_REQUEST": "Invalid characters in Virtual Server name / Wrong boot image type / Too many boot devices / Invalid RAM or Cores size", "OVER_LIMIT_SETTING": "Cores and/or RAM resources exceed resource limits"}
			return self.call("createServer", [args], errors)
		
		def rebootServer(self, id):
			return self.call("rebootServer", [id], {})
		
		def updateServer(self, userArgs):
			args = self.parseArgs(userArgs, {"srvid": "serverId", "name": "serverName", "cores": "cores", "ram": "ram", "bootFromImageId": "bootFromImageId", "bootFromStorageId": "bootFromStorageId", "osType": "osType"})
			errors = {"BAD_REQUEST": "Invalid characters in the Virtual Server name / Wrong boot image type / Too many boot images / Invalid Cores/RAM size", "OVER_LIMIT_SETTING": "Cores and/or RAM exceed limits", "RESOURCE_NOT_FOUND": "Specified Virtual Server / Boot Image / Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server"}
			return self.call("updateServer", [args], errors)
		
		def deleteServer(self, id):
			errors = {"RESOURCE_NOT_FOUND": "Virtual Server does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server"}
			return self.call("deleteServer", [id], errors)
		
		def createStorage(self, userArgs):
			args = self.parseArgs(userArgs, {"dcid": "dataCenterId", "size": "size", "name": "storageName", "mountImageId": "mountImageId"})
			errors = {"BAD_REQUEST": "Invalid characters in Virtual Storage name", "OVER_LIMIT_SETTING": "Storage size exceeds limit", "UNAUTHORIZED": "User is not authorized to access the Virtual Storage"}
			return self.call("createStorage", [args], errors)
		
		def getStorage(self, id):
			errors = {"RESOURCE_DELETED": "The Virtual Storage has been deleted by the user", "RESOURCE_NOT_FOUND": "Specified Virtual Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Storage"}
			return self.call("getStorage", [id], errors)
		
		def connectStorageToServer(self, userArgs):
			args = self.parseArgs(userArgs, {"stoid": "storageId", "srvid": "serverId", "bus": "busType", "devnum": "deviceNumber"})
			args["busType"] = args["busType"].upper()
			errors = {"RESOURCE_NOT_FOUND": "Specified Virtual Server or Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server or Storage", "BAD_REQUEST": "Specified Virtual Server and Storage are not in the same Data Center"}
			return self.call("connectStorageToServer", [args], errors)
		
		def disconnectStorageFromServer(self, stoId, srvId):
			errors = {"PROVISIONING_NO_CHANGES": "Storage is not connected to specified server", "RESOURCE_NOT_FOUND": "Specified Virtual Server or Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server or Storage"}
			return self.call("disconnectStorageFromServer", [stoId, srvId], errors)
		
		def updateStorage(self, userArgs):
			args = self.parseArgs(userArgs, {"stoid": "storageId", "name": "storageName", "size": "size", "mountImageId": "mountImageId"})
			errors = {"OVER_LIMIT_SETTING": "Storage size exceeds limit", "RESOURCE_NOT_FOUND": "Storage or Image does not exist", "BAD_REQUEST": "Invalid characters in Virtual Storage name / invalid storage size (must be > 1 GiB)", "UNAUTHORIZED": "User is not authorized to access the storage"}
			return self.call("updateStorage", [args], errors)
		
		def deleteStorage(self, id):
			errors = {"RESOURCE_NOT_FOUND": "Specified Virtual Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Storage"}
			return self.call("deleteStorage", [id], errors)
		
		def addRomDriveToServer(self, userArgs):
			args = self.parseArgs(userArgs, {"imgid": "imageId", "srvid": "serverId", "devnum": "deviceNumber"})
			errors = {"RESOURCE_NOT_FOUND": "Specified Virtual Server or image does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server", "BAD_REQUEST": "Wrong image type (not a CD/DVD ISO image)"}
			return self.call("addRomDriveToServer", [args], errors)
		
		def removeRomDriveFromServer(self, imgid, srvid):
			errors = {"RESOURCE_NOT_FOUND": "Specified Virtual Server or image does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server"}
			return self.call("addRomDriveToServer", [imgid, srvid], errors)
		
		def createNIC(self, userArgs):
			args = self.parseArgs(userArgs, {"srvid": "serverId", "lanid": "lanId", "name": "nicName", "ip": "ip"})
			return self.call("createNic", [args], {}) # TODO: Must get error messages from documentation
		
		def setInternetAccess(self, dcid, lanid, internetAccess):
			errors = {"RESOURCE_NOT_FOUND": "Specified NIC/server does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server / Data Center"}
			return self.call("setInternetAccess", [dcid, lanid, internetAccess], errors)
		
	
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
		printCreateNIC = operationCompleted
		printEnableInternetAccess = operationCompleted
		printDisableInternetAccess = operationCompleted
		
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
		
		def printImage(self, image):
			if self.short:
				self.out("Image %s (%s)", image["imageName"], image["imageId"])
			else:
				self.out()
				self.out("Name: %s", image["imageName"])
				self.out("Image ID: %s", image["imageId"])
		
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

## Load auth from default.auth if exists

if "u" not in baseArgs or "p" not in baseArgs:
	try:
		authFile = open("default.auth", "r")
		baseArgs["u"] = authFile.readline().strip("\n")
		baseArgs["p"] = authFile.readline().strip("\n")
		authFile.close()
	except:
		pass

## Verify that all required arguments are present

if "u" not in baseArgs or "p" not in baseArgs:
	ProfitBricks.ArgsError("Missing authentication")
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
	}
}


## Instantiate API and API output formatter

api = ProfitBricks.API(baseArgs["u"], baseArgs["p"], debug = baseArgs["debug"])
formatter = ProfitBricks.Formatter()
if baseArgs["s"]:
	formatter.shortFormat()
if baseArgs["debug"] == True:
	logging.getLogger("suds.server").setLevel(logging.DEBUG)
	logging.getLogger("suds.client").setLevel(logging.DEBUG)
	logging.getLogger("suds.transport").setLevel(logging.DEBUG)
	pass


## Perform requested operation and display formatted output

opFound = False
for op in operations:
	if baseArgs["op"].replace("-", "").lower() == op.replace("-", "").lower():
		if "args" in operations[op]:
			for requiredArg in operations[op]["args"]:
				if not requiredArg in opArgs or opArgs[requiredArg] == "":
					args = ""
					for requiredArg in operations[op]["args"]:
						args = args + "-" + requiredArg + " "
					ProfitBricks.ArgsError("operation '%s' is requires these arguments: %s" % (baseArgs["op"], args)) # '%s'" % (baseArgs["op"], "-" + requiredArg))
		operations[op]["lambda"]()
		opFound = True
if not opFound:
	print "Unknown operation:", baseArgs["op"]
	print sys.argv
	sys.exit(2)

if not baseArgs["s"]:
	print

