from contrib import bglib
from modules import bluetoothdevice
from modules import types

import time

class SyncRouter():
    """docstring for SyncRouter"""
    def __init__(self, bglib, serial, mbed, logfile):
        self.connected_devices = {}
        self.connected_addrs = {}
        self.discovered_devices = []
        self.serial = serial
        self.bglib = bglib
        self.sequence_number = 0
        self.time_offsets = {}
        self.mbed = mbed
        self.error_data = {}
        self.logfile = logfile

    def set_devices(self, devices):
        self.discovered_devices = devices
        self.connected_devices = {}
        self.connected_addrs = {}

    def connect_to_devices(self):
        for device in self.discovered_devices:
            self.connect_to_device(device)

    def reconnect_to_devices(self):
        for device in self.connected_devices.values():
            device.connect();

    def connect_to_device(self, device):
        device_obj = bluetoothdevice.BluetoothDevice(
            self.bglib,
            self.serial,
            device,
            self.logfile)

        device_obj.connect()

        if not device_obj.connection_failed:
            self.connected_devices[device_obj.handles.connection] = device_obj
            self.connected_addrs[device.addr_str] = device_obj
        else:
            print("Connection failed to {}.".format(device_obj.device_info.addr_str))

    def discover_services(self):
        for device in self.connected_devices.values():
            device.discover_services()

    def on_disconnection_event(self, sender, args):
        handle = args['connection']
        reason = args['reason']
        if handle > 0 and handle < len(self.connected_devices) \
                and handle in self.connected_devices:
            #simply pass along the disconnection event to the device object
            self.connected_devices[handle].on_disconnection_event(sender, args)
            if self.connected_devices[handle].connection_failed:
                print("giving up on {}".format(self.connected_devices[handle].device_info))
                self.connected_devices.pop(handle)
        else:
            print("got disconection event 0x{1:02X} for unknown handle {0}".format(
                handle, reason))

    def trigger_scanning(self):
        print("Triggering scanning.")
        #self.bglib.ble_evt_connection_disconnected -= self.on_disconnection_event
        for device in self.connected_devices.values():
            device.trigger_scanning()
        time.sleep(1.0)
        #self.bglib.ble_evt_connection_disconnected += self.on_disconnection_event


    def calculate_timestamps(self):
        print("Reading timestamp data")
        standard_clock_data = 0
        read_timestamps = {}
        for device in self.connected_devices.values():
            results = device.read_timestamp_data()
            if results.standard_flag:
                if results.sequence_number != self.sequence_number:
                    print("ERROR. standard clock did not recieve last sequence_number {}. aborting sync run".format(self.sequence_number))
                    return
                print("device {} is the standard clock".format(device.device_info.addr_str))
                standard_clock_data = results
            read_timestamps[device.device_info.addr_str] = results.timestamp

        if not standard_clock_data:
            print("aborting--standard clock data missing")
            return

        for addr_str in read_timestamps:
            self.time_offsets[addr_str] = standard_clock_data.timestamp - read_timestamps[addr_str]
            print("RESULT offset for {}: {}".format(addr_str, self.time_offsets[addr_str]))
            self.logfile.write("RESULT offset for {}: {}".format(addr_str, self.time_offsets[addr_str]))


    def disconnect_devices(self):
        if len(self.connected_devices) != 0:
            for device in self.connected_devices.values():
                device.disconnect()


    def send_advertisement(self):
        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_end_procedure()
        )
        self.bglib.check_activity(self.serial, 1)

        self.sequence_number += 1

        adv_data = types.bluesync_master_adv_data_prefix + \
            types.integer_to_array(self.sequence_number)

        adv_data_len = len(adv_data)
        adv_data_str = ":".join("{:02X}".format(byte) for byte in adv_data)

        print("sending {} bytes: {}".format(adv_data_len, adv_data_str))

        def on_adv_data_rsp(sender, args):
            print("adv_data response code: {0} ({0:04X})".format(args['result']))

        self.bglib.ble_rsp_gap_set_adv_data += on_adv_data_rsp
        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_set_adv_data(0, adv_data)
        )
        self.bglib.check_activity(self.serial, 1)
        self.bglib.ble_rsp_gap_set_adv_data -= on_adv_data_rsp

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_set_adv_parameters(
                0x20, 0x20, 7
            )
        )

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_set_mode(4, 2)
        )
        self.bglib.check_activity(self.serial, 1)

        time.sleep(10.0)

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_set_mode(0, 0)
        )
        self.bglib.check_activity(self.serial, 1)

        
    def generate_event(self, delay):
        print("firing GPIO event")
        self.mbed.write('\x07')
        time.sleep(0.5)

        reference_value = 0
        self.error_data = {}
        observed_values = {}

        discovered_addr_strs = []
        sync_addr_set = set(self.time_offsets.keys())

        for device in self.discovered_devices:
            discovered_addr_strs.append(device.addr_str)

        discovered_addr_set = set(discovered_addr_strs)

        observable_addr_set = discovered_addr_set.intersection(sync_addr_set)

        for addr in observable_addr_set:
            self.connected_addrs[addr].connect()
            results = self.connected_addrs[addr].read_timestamp_data()
            self.connected_addrs[addr].disconnect()
            if results.standard_flag:
                reference_value = results.ref_time
            observed_values[addr] = results.ref_time

        for addr in observable_addr_set:
            self.error_data[addr] = reference_value - observed_values[addr] - self.time_offsets[addr]
            print("RESULT delay: {}  error for {}: {}".format(delay, addr, self.error_data[addr]))
            self.logfile.write("RESULT delay: {}  error for {}: {}".format(delay, addr, self.error_data[addr]))

        
    def sync_devices(self):
        self.bglib.ble_evt_connection_disconnected += self.on_disconnection_event
        self.connect_to_devices()
        self.discover_services()
        self.trigger_scanning()
        self.send_advertisement()
        self.reconnect_to_devices()
        self.calculate_timestamps()

        time.sleep(10.0)

        self.disconnect_devices()

        self.bglib.ble_evt_connection_disconnected -= self.on_disconnection_event













