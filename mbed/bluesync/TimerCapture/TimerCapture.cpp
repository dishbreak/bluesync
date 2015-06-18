#include "TimerCapture.h"

bool TimerCapture::timerStarted = false;

TimerCapture::TimerCapture(PinName pCapturePin) {
    uint8_t bitcount_pinselect = 0;
    uint8_t bitcount_capture_control = 0;
    
    #if DEBUG
    printf("Entering ctor\r\n");
    #endif
    
    switch (pCapturePin) {
        case p30:
            bitcount_pinselect = 8;
            bitcount_capture_control = 0;
            break;
        case p29:
            bitcount_pinselect = 10;
            bitcount_capture_control = 3;
            break;
        default:
            error("TimerCapture: Invalid pin specified! Pick either p29 (P0.5) or p30 (p0.4).");
            break;
    }
    
    #if DEBUG
    printf("Bitcounts selected: %d (pinselect) %d (capture control)\r\n", bitcount_pinselect, bitcount_capture_control);
    #endif
    
    uint32_t bitmask_pinselect = (0x3 << bitcount_pinselect);
    mCapturePin = pCapturePin;
    
    // error out if the pin is already configured.
    if ((LPC_PINCON->PINSEL0 & bitmask_pinselect) == bitmask_pinselect) {
        error("TimerCapture: Pin is already configured!");
    }
    
    
    //check if peripheral has power, else this operation will hang!
    if ((LPC_SC->PCONP & (1 << 22)) == 0) {
        error("TimerCapture: Attempted to write to timer registers with power off!");
    }
    
    #if DEBUG
    printf("OK to configure registers\r\n");
    #endif
    
    // configure the pin
    LPC_PINCON->PINSEL0 |= bitmask_pinselect;
    
    #if DEBUG
    printf("Configuring rising edge. Register is %08x\r\n", LPC_TIM2->CCR);
    #endif
    
    // store on rising edge of input
    LPC_TIM2->CCR |= (1 << bitcount_capture_control); 
    
    #if DEBUG
    printf("Leaving ctor\r\n");
    #endif
}

void TimerCapture::startTimer() {
    if (!timerStarted) {
        timerStarted = true;
        
        configureTimer();
        
        //start timer
        LPC_TIM2->TCR = 1;
    }
}

void TimerCapture::stopTimer() {
    timerStarted = false;
    //stop timer
    LPC_TIM2->TCR = 0;
}

bool TimerCapture::isRunning() {
    return timerStarted;
}

void TimerCapture::resetTimer() {
    //reset timer
    LPC_TIM2->TCR = 2;
    LPC_TIM2->TCR = 0;
    LPC_TIM2->CR0 = 0;
    LPC_TIM2->CR1 = 0;
}

uint32_t TimerCapture::getTime() {
    uint32_t observedTime = 0;
    switch(mCapturePin) {
        case p30:
            observedTime = LPC_TIM2->CR0;
            break;
        case p29:
            observedTime = LPC_TIM2->CR1;
            break;
        default:
            observedTime = 0;
            break;
    }
    
    return observedTime;
}

void TimerCapture::configureTimer() {
    // Power on Peripheral TIMER2
    LPC_SC->PCONP |= (1 << 22);
    
    // Set clock source for TIMER2
    uint8_t clockSel = 0x01;
    LPC_SC->PCLKSEL1 |= (clockSel << 12);
    
    // Set prescaler counter
    LPC_TIM2->PR = SystemCoreClock/1000; //should increment once a milisecond.
    
}
       