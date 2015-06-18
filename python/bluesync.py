from threading import Thread 
from collections import namedtuple

from modules import scanner
from modules import syncrouter
from contrib import bglib

import serial
import random
import time


bgapi = bglib.BGLib()
bgapi.debug = True
ser = 0
mbed = 0
scanner_thread = 0
serial_port = '/dev/ttyACM0'
mbed_port = '/dev/ttyACM1'
f = open("results.txt", "a", 0)

def main():
    try:
        ser = serial.Serial(port=serial_port, baudrate=115200, timeout=115200)
    except serial.SerialException as e:
        print("Port error on {}: {}".format(serial_port, e))

    ser.flushInput()
    ser.flushOutput()

    try:
        mbed = serial.Serial(port=mbed_port, baudrate=9600, timeout=9600)
    except serial.SerialException as e:
        print("Port error on {}: {}".format(mbed_port, e))

    mbed.flushInput()
    mbed.flushOutput()

    
    scanner_obj = scanner.Scanner(bgapi, ser)
    router_obj = syncrouter.SyncRouter(bgapi, ser, mbed, f)
    
    
    while True:
        print("ready, starting scan")
        
        scanner_thread = Thread(target=scanner_obj.scan)
        #let the scan take place in the background
        scanner_thread.daemon = True
        scanner_thread.start()
        #wait 30 seconds to allow the scan to take place.
        scanner_thread.join(10.0)

        #stop the scan, then wait for the scanner to finish running.
        scanner_obj.stop_scan()
        scanner_thread.join()

        router_obj.set_devices(scanner_obj.scanned_list.values())
        router_thread = Thread(target=router_obj.sync_devices)
        router_thread.daemon = True
        router_thread.start()
        router_thread.join()

        delays = [10, 30, 60, 500]
        for delay in delays:
            print("Waiting for {} seconds before firing event".format(delay))
            time.sleep(delay)
            router_obj.generate_event(delay)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("shutting down...")
 

