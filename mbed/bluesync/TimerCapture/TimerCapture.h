#ifndef TIMERCAPTURE_H
#define TIMERCAPTURE_H

#include "mbed.h"

/** Directive that will toggle debug output via `printf`. Set to 1 to enable, 0 to disable. */
#define DEBUG 0

/** A class that will start TIMER2 on the LPC1768 and configure it to use one of the two capture pins (p29 or p30). 
* Capture pins allow the hardware to "timestamp" when a pin goes high or low, depending on the configuration. For more information, consult the 
* <a href="http://www.nxp.com/documents/user_manual/UM10360.pdf">LPC1768 user manual</a>.
* <h3>Example</h3>
* The following example will set up a capture pin, and will print out the timestamp from the capture register whenever a keypress is detected on the USB serial interface.
* @code
* #include "mbed.h"
* #include "TimerCapture.h"
* 
* Serial pc(USBTX, USBRX);
* TimerCapture * capture;
* 
* void handleInput() {
*     pc.getc(); // clear the interrupt handler.
*     printf("Capture register reads: %d\r\n", capture->getTime());
* }
* 
* int main() {
*     pc.printf("Timer Capture Program Starting\r\n");
*     TimerCapture::startTimer();
*     capture = new TimerCapture(p29);
*     pc.attach(&handleInput);
* }
* @endcode
*
* @attention Because this code operates directly on TIMER2, it has the potential to (a) mess with existing code or (b) cause errors when you instantiate too many objects. 
* Make sure to read this documentation thoroughly, else you may find yourself staring at <a href="https://developer.mbed.org/handbook/Debugging#runtime-errors">lights of death</a>!
*/
class TimerCapture {

public:

    /** Configures registers to use the given pin as a capture pin.
    * Initializes an object that will configure and read from a capture pin. 
    * If the timer is not already running, it will get configured. 
    *
    * @attention <b>There are only two pins that will act as capture pins for TIMER2.</b> These are P0.4 (DIP p30) and P0.5(DIP p29). 
    *
    * @warning This will cause a runtime error if: 
    *<ul>
    * <li>pCapturePin is not set to an actual capture pin on the LPC1768.
    * <li>The specified capture pin is already in use (i.e. already configured). 
    * <li>The timer hasn't yet been started (i.e. peripheral is off)
    *</ul>
    * @param pCapturePin The PinName intended to be used for the capture.
    */
    TimerCapture(PinName pCapturePin); 
    
    /** Get the time captured by the capture pin's register. 
    * @return Time in miliseconds since the timer got started.
    */
    uint32_t getTime();

    /** Starts the TIMER2 timer, and configures it if it's not already configured. */
    static void startTimer();
    
    /** Checks if the TIMER2 timer is running. 
    * @return True if the timer is running, false otherwise.
    */
    static bool isRunning();
    
    /** Stops the TIMER2 timer. */
    static void stopTimer();
    
    /** Resets the TIMER2 timer. 
    * @attention This will also clear both timer registers. You've been warned!
    */
    static void resetTimer();
    
private:
    PinName mCapturePin;

    static bool timerStarted;
    
    static void configureTimer();
    
};
#endif