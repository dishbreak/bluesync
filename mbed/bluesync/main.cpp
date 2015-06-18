#include "mbed.h"
#include "TimerCapture.h"
#include "bluesync_types.h"

/** @file main.cpp
@brief Main for the BlueSync mbed application. */

Serial ble112(p9, p10); ///< Serial connection for communicating with the BLE112.
TimerCapture * capPin; ///< Capture pin, wired to GPIO pin on BLE112.
TimerCapture * evtPin; 
DigitalOut bleSlaveLed(LED1);
DigitalOut bleScanningLed(LED2);
DigitalOut bleAdvRecv(LED3);
DigitalOut statusLed(LED4);
Ticker ticker;
InterruptIn evtWatchPin(p28);

void blankOutLeds() {
    bleSlaveLed = 0;
    bleScanningLed = 0;
    bleAdvRecv = 0;
    //statusLed = 0;
}

/*uint8_t[] toByteArray(uint32_t input) {
    uint8_t byte[4]; 
    
    byte[0] = input & 0x000000FF;
    byte[1] = (input & 0x0000FF00) >> 8;
    byte[2] = (input & 0x00FF0000) >> 16;
    byte[3] = (input & 0xFF000000) >> 24;
    
    return byte;
}*/

void on_adv_recv() {
    blankOutLeds();
    bleAdvRecv = 1;
    uint8_t hw_addr[6];
    for (int i = 5; i >=0; i--) {
        hw_addr[i] = ble112.getc();
    }
    
    printf("***************\r\n");
    printf("HW Addr: %02x:%02x:%02x:%02x:%02x:%02x ", 
        hw_addr[0], 
        hw_addr[1], 
        hw_addr[2], 
        hw_addr[3], 
        hw_addr[4], 
        hw_addr[5]);
    printf("Obs At: %d\r\n", capPin->getTime());
}

void on_master_mode() {
    blankOutLeds();
    bleScanningLed = 1;
}

void on_slave_mode() {
    blankOutLeds();
    bleSlaveLed = 1;
    intByteArray bitArray;
    bitArray.integer = capPin->getTime();
    printf("Sending timestamp %d (%08x)\r\n", bitArray.integer, bitArray.integer);
    uint8_t event = (uint8_t) EventCode::SET_TIMESTAMP;
    printf("Sending event: %x\r\n", event);
    ble112.putc(0x05);   
    for (int i = 0; i < 4; i++) {
        ble112.putc(bitArray.byte[i]);
    }
}

void on_offset_recv() {
    blankOutLeds();
    statusLed = 1;
    intByteArray bitArray;
    printf("Trying to get offset\r\n");
    for (int i = 0; i < 4; i++) {
        printf("Reading byte[%d]\r\n", i);
        bitArray.byte[i] = ble112.getc();
    }
    printf("Got offset %d\r\n", bitArray.signed_integer);
    
    LPC_TIM2->TC += bitArray.signed_integer;
}

void on_interrupt_recv() {
    uint8_t event = (uint8_t) EventCode::SET_SENSOR_TIME;
    intByteArray bitArray;
    bitArray.integer = evtPin->getTime();
    printf("Sending sensor time %d (%08x)\r\n", bitArray.integer, bitArray.integer);
    ble112.putc(event);
    for (int i = 0; i < 4; i++) {
        ble112.putc(bitArray.byte[i]);
    }
}

void on_serial_rcv() {
    uint8_t command = ble112.getc();
    printf("Command: %x\r\n", command);
    switch (command) {
    case EventCode::ADV_RECV:
        on_adv_recv();
        break;
    case EventCode::SLAVE_MODE:
        on_slave_mode();
        break;
    case EventCode::MASTER_MODE:
        on_master_mode();
        break;
    case EventCode::SET_TIMESTAMP:
        
        break;
    case EventCode::OFFSET_RECV:
        on_offset_recv();
        break;
    default:
        printf("Got unexpected byte '%x' from terminal!\r\n",command);
        break;
    } 
}

void on_tick() {
    uint32_t timestamp = capPin->getTime();
    printf("+++Capture register: %d (%08x) timer: %d (%08x)\r\n", timestamp, timestamp,
        LPC_TIM2->TC, LPC_TIM2->TC
    );
    statusLed = !statusLed;
}  

int main() {
    printf("Booted!\r\n");
    printf("SystemCoreClock is %d, %d ticks per ms\r\n", SystemCoreClock, SystemCoreClock/1000);
    ticker.attach(&on_tick, 5.0);
    statusLed = 1;
    TimerCapture::startTimer();
    capPin = new TimerCapture(p30);
    evtPin = new TimerCapture(p29);
    evtWatchPin.rise(&on_interrupt_recv);
    ble112.baud(9600);
    ble112.set_flow_control(SerialBase::RTSCTS, p7, p8);
    ble112.attach(&on_serial_rcv);
    uint8_t command = (uint8_t) EventCode::GET_STATE;
    printf("Sending command %x\r\n", command);
    ble112.putc(command);
    for (int i = 0; i < 4; i++) {
        ble112.putc(0x00);
    }
}
