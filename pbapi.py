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

## We need to patch suds.client.SoapClient because it doesn't throw an exception in case of bad authentication
class SudsClientPatched(suds.client.SoapClient):
	def failed(self, binding, error):
		raise error
suds.client.SoapClient = SudsClientPatched
## End patch

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
			code = transportError.httpcode
			error = self.codeToError[code if code in self.codeToError else 0]
			errorMessage = customErrorMessages[error] if error in customErrorMessages else self.defaultErrorMessages[error]
			print "Error %d: %s: %s." % (code, error, errorMessage)
			sys.exit(code)
	
	class ArgsError:
		
		def __init__(self, message = None):
			print "Invalid arguments" + ("" if message is None else ": " + message)
			sys.exit(1)
	
	class API:
		
		url = "https://api.profitbricks.com/1.1/wsdl";
		
		def __init__(self, username, password):
			try:
				self.client = suds.client.Client(url = self.url, username = username, password = password)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"UNAUTHORIZED": "Invalid username or password"});
		
		def getAllDataCenters(self):
			try:
				return self.client.service.getAllDataCenters()
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err)
		
		def getDataCenter(self, id):
			try:
				return self.client.service.getDataCenter(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Data Center does not exist"})
		
		def getServer(self, id):
			try:
				return self.client.service.getServer(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Data Center does not exist"})
		
		def createDataCenter(self, name):
			try:
				return self.client.service.createDataCenter(name)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"BAD_REQUEST": "Invalid characters in DataCenter name"})
		
		def getDataCenterState(self, id):
			try:
				return self.client.service.getDataCenterState(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "DataCenter does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter"})
		
		def updateDataCenter(self, apiArgs):
			args = { "dataCenterId": apiArgs["dcid"] }
			if "name" in apiArgs:
				args["dataCenterName"] = apiArgs["name"]
			try:
				return self.client.service.updateDataCenter(args)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"BAD_REQUEST": "Invalid characters in DataCenter name", "RESOURCE_NOT_FOUND": "Specified DataCenter ID does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter"})
		
		def clearDataCenter(self, id):
			try:
				return self.client.service.clearDataCenter(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "DataCenter does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter"})
		
		def deleteDataCenter(self, id):
			try:
				return self.client.service.deleteDataCenter(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "DataCenter does not exist", "UNAUTHORIZED": "User is not authorized to access the DataCenter", "BAD_REQUEST": "DataCenter is not empty"})
		
		def createServer(self, apiArgs):
			args = { "cores": apiArgs["cores"], "ram": apiArgs["ram"] }
			if "dcid" in apiArgs:
				args["dataCenterId"] = apiArgs["dcid"]
			if "name" in apiArgs:
				args["serverName"] = apiArgs["name"]
			if "bootFromImageId" in apiArgs:
				args["bootFromImageId"] = apiArgs["bootFromImageId"]
			if "bootFromStorageId" in apiArgs:
				args["bootFromStorageId"] = apiArgs["bootFromStorageId"]
			if "lanId" in apiArgs:
				args["lanId"] = apiArgs["lanId"]
			if "internetAccess" in apiArgs:
				args["internetAccess"] = ((apiArgs["internetAccess"].lower() + 'x')[0] == "y")
			if "osType" in apiArgs:
				args["osType"] = apiArgs["osType"]
			try:
				return self.client.service.createServer(args)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Boot media does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server", "BAD_REQUEST": "Invalid characters in Virtual Server name / Wrong boot image type / Too many boot devices / Invalid RAM or Cores size", "OVER_LIMIT_SETTING": "Cores and/or RAM resources exceed resource limits"})
			
		def rebootServer(self, id):
			try:
				return self.client.service.rebootServer(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err)
		
		def updateServer(self, apiArgs):
			args = { "serverId": apiArgs["srvid"] }
			if "name" in apiArgs:
				args["serverName"] = apiArgs["name"]
			for i in ["cores", "ram", "bootFromImageId", "bootFromStorageId", "osType"]:
				if i in apiArgs:
					args[i] = apiArgs[i]
			print args
			try:
				return self.client.service.updateServer(args)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"BAD_REQUEST": "Invalid characters in the Virtual Server name / Wrong boot image type / Too many boot images / Invalid Cores/RAM size", "OVER_LIMIT_SETTING": "Cores and/or RAM exceed limits", "RESOURCE_NOT_FOUND": "Specified Virtual Server / Boot Image / Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server"})
		
		def deleteServer(self, id):
			try:
				return self.client.service.deleteServer(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Virtual Server does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server"})
		
		def createStorage(self, apiArgs):
			args = { "size": apiArgs["size"] }
			if "dcid" in apiArgs:
				args["dataCenterId"] = apiArgs["dcid"]
			if "name" in apiArgs:
				args["storageName"] = apiArgs["name"]
			if "mountImageId" in apiArgs:
				args["mountImageId"] = apiArgs["mountImageId"]
			try:
				return self.client.service.createStorage(args)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"BAD_REQUEST": "Invalid characters in Virtual Storage name", "OVER_LIMIT_SETTING": "Storage size exceeds limit", "UNAUTHORIZED": "User is not authorized to access the Virtual Storage"})
		
		def getStorage(self, id):
			try:
				return self.client.service.getStorage(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_DELETED": "The Virtual Storage has been deleted by the user", "RESOURCE_NOT_FOUND": "Specified Virtual Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Storage"})
		
		def connectStorageToServer(self, stoId, srvId, busType, deviceNumber = None):
			args = { "storageId": stoId, "serverId": srvId, "busType": busType }
			if deviceNumber != None:
				args["deviceNumber"] = deviceNumber
			try:
				return self.client.service.connectStorageToServer(args)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Specified Virtual Server or Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server or Storage", "BAD_REQUEST": "Specified Virtual Server and Storage are not in the same Data Center"})
		
		def disconnectStorageFromServer(self, stoId, srvId):
			try:
				return self.client.service.disconnectStorageFromServer(stoId, srvId)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"PROVISIONING_NO_CHANGES": "Storage is not connected to specified server", "RESOURCE_NOT_FOUND": "Specified Virtual Server or Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server or Storage"})
		
		def updateStorage(self, apiArgs):
			args = { "storageId": apiArgs["stoid"] }
			if "name" in apiArgs:
				args["serverName"] = apiArgs["name"]
			for i in ["size", "mountImageId"]:
				if i in apiArgs:
					args[i] = apiArgs[i]
			try:
				return self.client.service.updateStorage(args)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"OVER_LIMIT_SETTING": "Storage size exceeds limit", "RESOURCE_NOT_FOUND": "Storage or Image does not exist", "BAD_REQUEST": "Invalid characters in Virtual Storage name / invalid storage size (must be > 1 GiB)", "UNAUTHORIZED": "User is not authorized to access the storage"})
		
		def deleteStorage(self, id):
			try:
				return self.client.service.deleteStorage(id)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Specified Virtual Storage does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Storage"})
		
		def addRomDriveToServer(self, apiArgs):
			args = { "imageId": apiArgs["imgid"], "serverId": apiArgs["srvid"] }
			if "devnum" in apiArgs:
				args["deviceNumber"] = apiArgs["devnum"]
			try:
				return self.client.service.addRomDriveToServer(arg)
			except suds.transport.TransportError as (err):
				ProfitBricks.APIError(err, {"RESOURCE_NOT_FOUND": "Specified Virtual Server or image does not exist", "UNAUTHORIZED": "User is not authorized to access the Virtual Server", "BAD_REQUEST": "Wrong image type (not a CD/DVD ISO image)"})
		
	
	class Formatter:
		
		indentValue = 0
		short = False
		
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
		def requireArgs(soapResponse, requiredArgs, replaceMissingWith = "ERROR"):
			result = {}
			for arg in requiredArgs:
				result[arg] = str(soapResponse[arg]) if arg in soapResponse else replaceMissingWith
			return result
		
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
				self.out("Connected to VM ID: %s", (" ; ".join(storage.serverIds)) if "serverIds" in storage else "ERROR")
				self.out("Mount image ID: %s", (storage.mountImage.imageId if "mountImage" in storage else "none"))
				self.indent(-1)
			else:
				self.out()
				self.out("Name: %s", st["storageName"])
				self.out("Storage ID: %s", st["storageId"])
				self.out("Size: %s GiB", st["size"])
				self.out("Connected to Virtual Servers: %s", (" ; ".join(storage.serverIds)) if "serverIds" in storage else "ERROR")
				self.out("Provisioning state: %s", st["provisioningState"])
				self.out("Operating system: %s", st["osType"])
				self.out("Mount image:")
				self.indent(1)
				if "mountImage" in storage:
					self.printImage(self, storage.mountImage)
				else:
					self.out("No image")
				self.indent(-1)
		
		def printDataCenter(self, dataCenter):
			dc = self.requireArgs(dataCenter, ["dataCenterName", "provisioningState", "dataCenterVersion"])
			if self.short:
				self.out("%s is %s", dc["dataCenterName"], dc["provisioningState"])
				self.out("Servers:")
				self.indent(1);
				if "servers" in dataCenter:
					for server in dataCenter.servers:
						self.printServer(server)
				else:
					self.out("ERROR")
				self.indent(-1);
				self.out("Storages:")
				self.indent(1);
				if "storages" in dataCenter:
					for storage in dataCenter.storages:
						self.printStorage(storage)
				else:
					self.out("ERROR")
				self.indent(-1);
			else:
				self.out()
				self.out("Name: %s", dc["dataCenterName"])
				self.out("Provisioning state: %s", dc["provisioningState"])
				self.out("Version: %s", dc["dataCenterVersion"])
				self.out()
				self.out("Servers:")
				self.indent(1)
				if "servers" in dataCenter:
					for server in dataCenter.servers:
						self.printServer(server)
				else:
					self.out("ERROR")
				self.indent(-1)
				self.out()
				self.out("Storages:")
				self.indent(1);
				if "storages" in dataCenter:
					for storage in dataCenter.storages:
						self.printStorage(storage)
				else:
					self.out("ERROR")
				self.indent(-1);

## Parse arguments

# -u -p -auth and -s are baseArgs, everything else is opArgs

baseArgs = {"s": False, "debug": False } # s = short output formatting
opArgs = {}
i = 1
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg == "-":
		continue
	elif arg != "" and arg[0] == "-":
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
			except:
				ProfitBricks.ArgsError("Authfile does not exist or cannot be read")
			baseArgs["u"] = authFile.readline().strip("\n")
			baseArgs["p"] = authFile.readline().strip("\n")
			authFile.close()
			i += 1
		elif arg.lower() == "-s":
			baseArgs["s"] = True
		elif arg.lower() == "-debug":
			baseArgs["debug"] = True
		else:
			opArgs[arg[1:].lower()] = (sys.argv[i + 1] if i < len(sys.argv) - 1 else "")
			i += 1
	else:
		baseArgs["op"] = sys.argv[i];
	i += 1

## Verify that all required arguments are present

if "u" not in baseArgs:
	ProfitBricks.ArgsError("Missing username")
if "p" not in baseArgs:
	ProfitBricks.ArgsError("Missing password")
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
		"lambda": lambda: formatter.printConnectStorageToServer(api.connectStorageToServer(opArgs["stoid"], opArgs["srvid"], opArgs["bus"], opArgs["deviceNumber"] if "deviceNumber" in opArgs else None))
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
		"lambda": lambda: formatter.printAddRomDriveToServer(api.addRomDrivetoServer(opArgs))
	},
	"getNIC": {
		"args": ["nicid"],
		"lambda": lambda: formatter.printNIC(api.getNIC(opArgs["nicid"]))
	}
}

## Instantiate API and API formatter

api = ProfitBricks.API(baseArgs["u"], baseArgs["p"])
formatter = ProfitBricks.Formatter()
if baseArgs["s"]:
	formatter.shortFormat()
if baseArgs["debug"] == True:
	logging.getLogger('suds.client').setLevel(logging.DEBUG)
	#logging.getLogger('suds.transport').setLevel(logging.DEBUG)

## Perform requested operation and display formatted output

opFound = False
for operation in operations:
	if baseArgs["op"].replace("-", "").lower() == operation.replace("-", "").lower():
		if "args" in operations[operation]:
			for requiredArg in operations[operation]["args"]:
				if not requiredArg in opArgs or opArgs[requiredArg] == "":
					ProfitBricks.ArgsError("Operation '%s' is missing argument '%s'" % (baseArgs["op"], "-" + requiredArg))
		operations[operation]["lambda"]()
		opFound = True
if not opFound:
	print "Unknown operation:", baseArgs["op"]
	print sys.argv
	sys.exit(2)

if not baseArgs["s"]:
	print


