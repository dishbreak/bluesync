from contrib import bglib
import time
from modules import types


class Scanner():
    """docstring for Scanner"""

    device_prefix = [0x00, 0x07, 0x80][::-1]

    @staticmethod
    def bytes_to_hex(bytes):
        return ":".join("{:02X}".format(byte) for byte in bytes[::-1])

    def __init__(self, bglib, serial):
        
        self.bglib = bglib
        self.serial = serial
        self.scanned_list = {}
        self.is_scanning = False

    def on_get_address(self, sender, args):
        print("Using device {}".format(args['address']))

    def on_scan_result(self, sender, args):

        if (args['data'] == types.bluesync_slave_adv_data):
            device = types.Device(
                Scanner.bytes_to_hex(args['sender']), 
                args['sender'],
                time.time()
            )
            if not device.addr_str in self.scanned_list:
                 print("Found device {}".format(device.addr_str))

            self.scanned_list[device.addr_str] = device 

    def scan(self):

        self.is_scanning = True

        self.bglib.ble_rsp_system_address_get += self.on_get_address
        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_system_address_get()
        )
        self.bglib.check_activity(self.serial, 1)
        self.bglib.ble_rsp_system_address_get -= self.on_get_address

        self.bglib.ble_evt_gap_scan_response += self.on_scan_result

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_end_procedure()
        )

        self.bglib.check_activity(self.serial, 1)

        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_discover(1)
        )
        self.bglib.check_activity(self.serial, 1)

        while self.is_scanning:
            time.sleep(0.1)
            self.bglib.check_activity(self.serial)

            for device in self.scanned_list.values():
                if device.last_heard < time.time() - 5:
                    print("Lost device {}".format(device.addr_str))
                    self.scanned_list.pop(device.addr_str)

        print('Stopping scanning.')
        self.bglib.send_command(
            self.serial,
            self.bglib.ble_cmd_gap_end_procedure()
        )
        self.bglib.check_activity(self.serial, 1)


    def stop_scan(self):
        self.is_scanning = False

        self.bglib.ble_evt_gap_scan_response -= self.on_scan_result

