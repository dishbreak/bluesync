from contrib import bglib
import serial
import time

ble = bglib.BGLib()
#ble.debug = True
ser = 0
scanRunning = True

scanList = {}
connectedList = {}
connectionData = {}
result = 0
connected_device_count = 0
handle = 0

bluesync_uuid = [0x92, 0xb8, 0xb4, 0xf7, 0xd9, 
	0x96, 0xb3, 0xaf, 0x24, 0x48, 
	0x03, 0x20, 0x35, 0x74, 0x67, 
	0x86]

timestamp_uuid = [0x6e, 0x16, 0x71, 0x8f, 0xb9, 
	0xde, 0x2b, 0x92, 0xa0, 0x4b, 
	0x9d, 0x92, 0xaa, 0x49, 0xd4, 
	0x63]

tigger_scanning_uuid = [0x04, 0x48, 0x2f, 0x9a, 0x2e, 
	0x35, 0xc7, 0xa8, 0xcd, 0x4c, 
	0x4b, 0x90, 0x9a, 0xcb, 0xec, 
	0xe8]

reference_time_uuid = [0x1d, 0x4f, 0xc4, 0xeb, 0xf5, 
	0x2c, 0x94, 0xb9, 0xfc, 0x42, 
	0xca, 0x9e, 0x4a, 0x3b, 0xd9, 
	0x33]

proceed = False

def handle_timeout(sender, args):
	print("Whoops! BLED112 timed out. :-(\n")

def addr_to_string(addr):
	return "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(*addr[::-1])

def hex_to_string(hex):
	return ":".join("{:02x}".format(p) for p in hex[::-1])

def handle_get_info(sender, args):
	print("BlueGiga BLED112, BGAPI v{}.{}.{} (Build {})\n".format( 
		args['major'], 
		args['minor'], 
		args['patch'], 
		args['build']))

def handle_scan_result(sender, args):
	global scanList
	blueGigaFlag = ""
	blueGigaPrefix = [0x00, 0x07, 0x80][::-1] ## 0x80, 0x07, 0x00
	addr_string = addr_to_string(args['sender'])
	
	if args['sender'][3:6] == blueGigaPrefix:
		if not addr_string in scanList:
			print("Found Device {}".format(addr_to_string(args['sender'])))
			scanList[addr_string] = args;

def handle_connection_response(sender, args):
	global handle
	print("got handle {}".format(args['connection_handle']))
	handle = args['connection_handle']

def handle_connection_event(sender, args):
	global connected_device_count, handle, proceed
	proceed = True
	if args['flags'] == 0x05:
		print("Connected to {}".format(addr_to_string(args['address'])))
		connected_device_count = connected_device_count - 1
		print("{} {} remaining".format(
			connected_device_count, 'device' if connected_device_count == 1 else 'devices'))
		connectedList[handle] = {'address': args['address']}
	else:
		print("Connection to {} failed! :-(".format(
			addr_to_string(args['address'])))

def handle_disconnection(sender, args):
	print("Device {0} disconnecting with reason {1} ({1:04X})".format(
		args['connection'], args['reason']))

def main():
	global connected_device_count, scanList, connectedList, proceed, connectionData;

	try:
		ser = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=115200)
	except serial.SerialException as e:
		print("Port error on /dev/ttyACM0: {}", e)

	ser.flushInput()
	ser.flushOutput()
	
	ble.ble_rsp_system_get_info += handle_get_info
	ble.ble_evt_gap_scan_response += handle_scan_result
	ble.ble_evt_connection_status += handle_connection_event
	ble.ble_rsp_gap_connect_direct += handle_connection_response
	ble.ble_evt_connection_disconnected += handle_disconnection

	ble.on_timeout += handle_timeout

	ble.send_command(ser, ble.ble_cmd_system_get_info())
	ble.check_activity(ser, 1)

	ble.send_command(ser, ble.ble_cmd_gap_end_procedure())
	ble.check_activity(ser, 1)

	ble.send_command(ser, ble.ble_cmd_gap_discover(1))
	ble.check_activity(ser, 1)

	print("Scanning for 3 seconds...")
	timeout = time.time() + 3
	while True:
		ble.check_activity(ser)
		time.sleep(0.01)
		if time.time() > timeout:
			break;

	
	print("Found {} {}".format(
		len(scanList), 'device' if len(scanList) == 1 else 'devices'))

	if len(scanList) == 0:
		print("No devices found.")
		exit(0)

	connected_device_count = len(scanList)

	for device_addr, device in scanList.iteritems():
		print("Connecting to {}".format(device_addr))
		ble.send_command(ser, ble.ble_cmd_gap_connect_direct(
			device['sender'], 0, 60, 76, 100, 0))
		ble.check_activity(ser, 1)
		proceed = False
		while proceed != True:
			ble.check_activity(ser)
			time.sleep(0.01)

	timeout = time.time() + 10
	print("waiting for all devices to finish connecting...")
	while True:
		ble.check_activity(ser)
		time.sleep(0.01)
		if (connected_device_count == 0) or (time.time() > timeout):
			break

	#ble.ble_evt_connection_status -= handle_connection_event

	if connected_device_count != 0:
		print("WARNING: Not all devices connected")

	proceed = False
	connectionData = {}
	def on_service_discovered(sender, args):
		global proceed, connectedList
		
		# print("Service[{} - {}] {}".format(
		# 	args['start'],
		# 	args['end'],
		# 	hex_to_string(args["uuid"])))

		if args['uuid'] == bluesync_uuid:
			print("Bluesync!")
			connectedList[args["connection"]]['service_start'] = args['start']
			connectedList[args["connection"]]['service_end'] = args['end']
			connectedList[args["connection"]]['handle'] = args['connection']
		
		if args['end'] == 0xffff:
			print("Found end of services!")
			proceed = True

	def on_characteristic_discovered(sender, args):
		global connectionData

		#print("Characteristic[{}] {}".format( connHandle,
		#	args['chrhandle'], hex_to_string(args['uuid'])))
		if args['uuid'] == tigger_scanning_uuid:
			print("trigger_scanning")
			connectionData['trigger_scanning'] = args['chrhandle']
		elif args['uuid'] == reference_time_uuid:
			print("reference_time")
			connectionData['reference_time'] = args['chrhandle']
		elif args['uuid'] == timestamp_uuid:
			print("timestamp")
			connectionData['timestamp'] = args['chrhandle']

		#print(connectionData)


	def on_characteristic_discovered_proceed(sender, args):
		global proceed
		print("Result: {0} ({0:04X})".format(args['result']))
		proceed = True

	def on_result_recd(sender, args):
		print("Discovery Result: {0} ({0:04X})".format(args['result']))


	ble.ble_evt_attclient_group_found += on_service_discovered
	ble.ble_evt_attclient_find_information_found += on_characteristic_discovered
	ble.ble_evt_attclient_procedure_completed += on_characteristic_discovered_proceed
	ble.ble_rsp_attclient_find_information += on_result_recd

	print("Performing service discovery.")
	for connHandle in connectedList:
		print("Discovering on device {}".format(connHandle))
		proceed = False
		ble.send_command(ser, ble.ble_cmd_attclient_read_by_group_type(connHandle, 1, 65535, [0x00, 0x28]))
		ble.check_activity(ser, 1)
		while proceed != True:
			ble.check_activity(ser)
			time.sleep(0.01)
		#print(connectedList)

		print("Fetching Bluesync characteristics")
		proceed = False

		ble.send_command(ser, ble.ble_cmd_attclient_find_information(connHandle, 
			connectedList[connHandle]['service_start'], connectedList[connHandle]['service_end']))
		ble.check_activity(ser, 1)
		while proceed != True:
			ble.check_activity(ser)
			time.sleep(0.01)

		print(connectionData)
		connectedList[connHandle]['characteristics'] = connectionData
		print(connectedList)

	
	print("putting all devices in scanning mode")
	for connHandle in connectedList:
		charHandle = connectedList[connHandle]['characteristics']['trigger_scanning']
		ble.send_command(ser, ble.ble_cmd_attclient_attribute_write(connHandle, charHandle, [0x01]))
		ble.check_activity(ser, 1)

	print("waiting for scans to complete...")
	timeout = time.time() + 7
	while time.time() < timeout:
		time.sleep(0.01)

	print("Ok, disconnecting from devices")
	for connHandle in connectedList:
		print("disconnecting device {}".format(connHandle))
		ble.send_command(ser, ble.ble_cmd_connection_disconnect(connHandle))
		ble.check_activity(ser, 1)



main()