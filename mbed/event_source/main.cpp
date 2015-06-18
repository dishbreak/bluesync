#include "mbed.h"
 
InterruptIn button(p28);
DigitalOut led(LED1);
DigitalOut flash(LED4);
DigitalOut sigPin(p18);
Serial pc(USBTX, USBRX);
 
void led_on() {
    led = !led;
}

void led_off() {
    led = 0;
}

void on_pc_rcv() {
    pc.getc();
    led = 1;
    sigPin = 1;
    wait(0.25);
    sigPin = 0;
    led = 0;
}
 
int main() {
    pc.attach(&on_pc_rcv);
    button.rise(&led_on);  
    button.fall(&led_off); 
    while(1) {           // wait around, interrupts will interrupt this!
        flash = !flash;
        wait(0.25);
    }
}