/*
 * main.c
 *
 */

/* DriverLib Includes */
#include "driverlib.h"

/* Standard Includes */
#include <stdint.h>

#include <stdbool.h>

extern void UART_init (void);
extern void PWM_init (void);

int main(void)
{
    /* Halting WDT  */
    MAP_WDT_A_holdTimer();

    UART_init();
    PWM_init();

    /* Enabling interrupts */
    MAP_Interrupt_enableSleepOnIsrExit();
    MAP_Interrupt_enableMaster();

    while(1)
    {
        MAP_PCM_gotoLPM0();
    }
}
