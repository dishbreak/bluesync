from contrib import bglib
from collections import namedtuple
from modules import types

import time

class BleHandles():
    """docstring for BleHandles"""
    def __init__(
            self, 
            connection = -1, 
            service_start = -1, 
            service_end = -1, 
            timestamp = -1, 
            trigger_scanning = -1, 
            ref_time = -1,
            sequence_number = -1,
            standard_flag = -1
        ):
        self.connection = connection
        self.service_start = service_start
        self.service_end = service_end
        self.timestamp = timestamp
        self.trigger_scanning = trigger_scanning
        self.ref_time = ref_time
        self.sequence_number = sequence_number
        self.standard_flag = standard_flag
 
class TimestampData():
    def __init():
        self.timestamp = 0
        self.ref_time = 0
        self.sequence_number = 0
        self.standard_flag = 0

    def to_string(self):
        return "Timestamp: {} Seq_Num: {} Ref_Time: {} Std_Flag: {}".format(
                self.timestamp,
                self.sequence_number,
                self.ref_time,
                self.standard_flag
            )

class BluetoothDevice():
    """docstring for BluetoothDevice"""
    def __init__(self, bglib, serial, device_info, logfile, retry_count = 3):
        self.bglib = bglib
        self.serial = serial
        self.device_info = device_info
        self.retry_count = retry_count
        self.retries_remaining = retry_count
        self.handles = BleHandles()
        self.service_discovery_in_progress = False
        self.connection_in_progress = False
        self.connection_failed = False
        self.sequence_number = 1
        self.handle_being_read = -1
        self.time_data = 0
        self.last_command = 0
        self.logfile = logfile
        print("constructor called")        

    
    def on_connect_rsp(self, sender, args):
        if args['result'] == 0:
            self.handles.connection = args['connection_handle']
            print("{} got connection handle {}".format(
                self.device_info.addr_str, 
                self.handles.connection)
            )
        else:
            print("Connection error: {0} ({0:04X})".format(args['result']))

    def __reconnect(self):
        self.retries_remaining -= 1
        if self.retries_remaining > 0:
            print("Retrying, {} retry attempts remaining".format(self.retries_remaining))
            self.connect(self.retries_remaining, True)
        else:
            print("Couldn't connect.")
            self.connection_failed = True

    def on_connection_status_evt(self, sender, args):
        if(args['flags'] == 0x05):
            print("Connected (I think).")
            self.connection_in_progress = False
        else:
            print("Got flags value 0x{:02X}...reconnecting")
            self.__reconnect()
    
    def on_disconnection_event(self, sender, args):
        print("Got disconnection event with reason {0} ({0:04X})".format(args['reason']))
        if args['reason'] == 0x023E:
            self.__reconnect()

    def connect(self, retry_count = -1, is_retry = False):
        if retry_count == -1:
            retry_count = self.retry_count

        print("attempting a connection to {}".format(self.device_info.addr_str))
        
        if not is_retry:
            self.bglib.ble_rsp_gap_connect_direct += self.on_connect_rsp
            self.bglib.ble_evt_connection_status += self.on_connection_status_evt

        self.connection_in_progress = True
        self.retries_remaining = retry_count

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_connect_direct(
                self.device_info.addr, 0, 60, 76, 100, 0
            )
        ) #sorry for the magic numbers

        self.bglib.check_activity(self.serial, 1)

        timeout = time.time() + 5
        while self.connection_in_progress:
            time.sleep(0.1)
            self.bglib.check_activity(self.serial)
            if time.time() > timeout:
                break;

        if self.connection_in_progress:
            print("Connection timeout. attempting a reconnect.")
            self.__reconnect()

        self.bglib.ble_evt_connection_status -= self.on_connection_status_evt
        self.bglib.ble_rsp_gap_connect_direct -= self.on_connect_rsp

    def disconnect(self):
        print("disconnecting from device {}".format(
            self.handles.connection)
        )

        self.device_info = types.Device(
            self.device_info.addr_str, self.device_info.addr, time.time())

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_connection_disconnect(self.handles.connection)
        )

        self.bglib.check_activity(self.serial, 1)

    def on_service_characteristic_rsp(self, sender, args):
        print("responded with code {:0X}".format(args['result']))

    def on_service_discovered(self, sender, args):
        if args['uuid'] == types.bluesync_uuid:
            self.handles.service_start = args['start']
            self.handles.service_end = args['end']
            print("Found BlueSync service on device {} [{}-{}]".format(
                self.handles.connection, self.handles.service_start, 
                self.handles.service_end)
            )

        if args['end'] == 0xFFFF:
            self.service_discovery_in_progress = False

    def on_characteristic_discovered(self, sender, args):
        print("Discovered handle {}".format(args['chrhandle']))
        if args['uuid'] == types.timestamp_uuid:
            self.handles.timestamp = args['chrhandle']
        elif args['uuid'] == types.trigger_scanning_uuid:
            self.handles.trigger_scanning = args['chrhandle']
        elif args['uuid'] == types.reference_time_uuid:
            self.handles.ref_time = args['chrhandle']
        elif args['uuid'] == types.sequence_number_uuid:
            self.handles.sequence_number = args['chrhandle']
        elif args['uuid'] == types.standard_flag_uuid:
            self.handles.standard_flag = args['chrhandle']

    def on_characteristics_end(self, sender, args):
        self.service_discovery_in_progress = False
        print("timestamp:{} trigger_scanning:{} ref_time:{} seq_num:{} std:{}".format(
                self.handles.timestamp,
                self.handles.trigger_scanning,
                self.handles.ref_time,
                self.handles.sequence_number,
                self.handles.standard_flag
            )
        )


    def on_characteristic_read(self, sender, args):
        # print("read characteristic {}: {} ({})".format(args['atthandle'], 
        #     args['value'], types.array_to_integer(args['value'])))

        if args['atthandle'] == self.handle_being_read:
            self.handle_being_read = -1

        read_value = types.array_to_integer(args['value'])
        if args['atthandle'] == self.handles.timestamp:
            self.time_data.timestamp = read_value
        elif args['atthandle'] == self.handles.standard_flag:
            self.time_data.standard_flag = read_value
        elif args['atthandle'] == self.handles.ref_time:
            self.time_data.ref_time = read_value
        elif args['atthandle'] == self.handles.sequence_number:
            self.time_data.sequence_number = read_value



    def on_characteristic_read_rsp(self, sender, args):
        print("command response {:04X}".format(args['result']))
        if args['result'] == 0x0186:
            print("attempting a reconnect")
            self.connect()
            print('resending last command...')
            self.bglib.send_command(
                self.serial,
                self.bglib.ble_cmd_attclient_read_by_handle(
                    self.handles.connection,
                    self.handle_being_read)
            )
            self.bglib.check_activity(self.serial, 1)

    def read_timestamp_data(self):
        self.bglib.ble_evt_attclient_attribute_value += self.on_characteristic_read
        self.bglib.ble_rsp_attclient_read_by_handle += self.on_characteristic_read_rsp

        print("timestamp:{} trigger_scanning:{} ref_time:{}".format(
                self.handles.timestamp,
                self.handles.trigger_scanning,
                self.handles.ref_time
            )
        )

        handles = [
            self.handles.timestamp, 
            self.handles.ref_time,
            self.handles.sequence_number,
            self.handles.standard_flag
        ]

        self.time_data = TimestampData()

        for handle in handles:
            self.handle_being_read = handle
            # print("reading handle {}".format(handle))
            self.last_command = self.bglib.ble_cmd_attclient_read_by_handle(
                self.handles.connection,
                handle
            )
            self.bglib.send_command(
                self.serial, 
                self.last_command
            )
            # print("waiting for response...")
            # Catch response
            self.bglib.check_activity(self.serial, 3)
            # print("waiting for event...")
            while self.handle_being_read != -1:
                self.bglib.check_activity(self.serial)
                time.sleep(0.1)

        print("RESULT device {} data: {}".format(self.handles.connection, self.time_data.to_string()))
        self.logfile.write("RESULT device {} data: {}".format(self.handles.connection, self.time_data.to_string()))

        self.bglib.ble_evt_attclient_attribute_value -= self.on_characteristic_read        
        self.bglib.ble_rsp_attclient_read_by_handle -= self.on_characteristic_read_rsp

        return self.time_data


    def discover_services(self):
        self.service_discovery_in_progress = True
        self.bglib.ble_rsp_attclient_find_information += self.on_service_characteristic_rsp
        self.bglib.ble_evt_attclient_group_found += self.on_service_discovered

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_attclient_read_by_group_type(
                self.handles.connection,
                1, 65535, [0x00, 0x28]
            )
        )

        self.bglib.check_activity(self.serial, 1)

        while self.service_discovery_in_progress:
            time.sleep(0.1)
            self.bglib.check_activity(self.serial)

        if self.handles.service_start == -1:
            print("Didn't discover uuid for BlueSync")

        self.bglib.ble_evt_attclient_group_found -= self.on_service_discovered
        self.bglib.ble_rsp_attclient_find_information += self.on_service_characteristic_rsp

        
        self.service_discovery_in_progress = True
        self.bglib.ble_evt_attclient_find_information_found += self.on_characteristic_discovered
        self.bglib.ble_evt_attclient_procedure_completed += self.on_characteristics_end
        self.bglib.ble_rsp_attclient_find_information += self.on_service_characteristic_rsp

        self.bglib.send_command(self.serial,
            self.bglib.ble_cmd_attclient_find_information(
                self.handles.connection,
                self.handles.service_start,
                self.handles.service_end,
            )
        )
        self.bglib.check_activity(self.serial, 1)

        while self.service_discovery_in_progress:
            self.bglib.check_activity(self.serial)
            time.sleep(0.1)

        self.bglib.ble_evt_attclient_find_information_found -= self.on_characteristic_discovered
        self.bglib.ble_evt_attclient_procedure_completed -= self.on_characteristics_end
        self.bglib.ble_rsp_attclient_find_information -= self.on_service_characteristic_rsp



    def trigger_scanning(self):
        self.bglib.send_command(self.serial,
            self.bglib.ble_cmd_attclient_attribute_write(
                self.handles.connection,
                self.handles.trigger_scanning,
                [0x01]
            )
        )
        self.bglib.check_activity(self.serial, 1)




