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
	printDeleteLoadBalancer = operationCompleted
	printDeregisterServersOnLoadBalancer = operationCompleted
	
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
	
	def printCreateLoadBalancer(self, id):
		self.out("Load balancer ID: %s", id)
	
	def printLoadBalancer(self, loadBalancer):
		self.out("Load balancer ID: %s", loadBalancer["loadBalancerId"])
		self.out("Name: %s", loadBalancer["loadBalancerName"])
		self.out("Algorithm: %s", loadBalancer["loadBalancerAlgorithm"])
		self.out("IP address: %s", loadBalancer["ip"])
		self.out("LAN ID: %s", loadBalancer["lanId"])
		self.out("Balanced servers:")
		self.indent(1)
		if "balancedServers" in loadBalancer:
			for srv in loadBalancer["balancedServers"]:
				self.printBalancedServer(srv)
		else:
			self.out("(none)")
		self.indent(-1)
		self.out("Firewall:")
		self.indent(1)
		if "firewall" in loadBalancer:
			self.printFirewall(loadBalancer.firewall)
		else:
			self.out("(none)")
		self.indent(-1)
		self.out("Creation time [%s] modification time [%s]", loadBalancer["creationTime"], loadBalancer["lastModificationTime"])
		self.out("Provisioning state: %s", loadBalancer["provisioningState"])
	
	def printBalancedServer(self, srv):
		# it may be "active" instead of "activate", but the documentation specifies it is "activate"
		if self.short:
			self.out("%s on server %s (%s) NIC %s", "Active" if srv["activate"] else "Inactive", srv["serverName"], srv["serverId"], srv["balancedNicId"])
		else:
			self.out()
			self.out("Server ID: %s", srv["serverId"])
			self.out("Server name: %s", srv["serverName"])
			self.out("NIC ID: %s", srv["balancedNicId"])
			self.out("Active: %s", "yes" if srv["activate"] else "no")
	
	def printRegisterServersOnLoadBalancer(self, response):
		self.out("Load balancer ID: %s", response["loadBalancerId"])
		self.out("LAN ID: %s", response["lanId"])
		if "balancedServers" in response:
			for srv in response["balancedServers"]:
				self.printBalancedServer(srv)
		else:
			sel.out("ERROR")
	
	def _printImage(self, image): # need to test whether to use this or other method
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
			self.out("Writable: %s", "yes" if image["writeable"] else "nno")
			self.out("CPU hot plugging: %s", "yes" if image["cpuHotpluggable"] else "no")
			self.out("Memory hot plugging: %s", "yes" if image["memoryHotpluggable"] else "no")
			self.out("Server IDs: %s", (" ; ".join(image["serverIds"])) if "serverIds" in image else "(none)")
			self.out("Operating system: %s", image["osType"])
	
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


