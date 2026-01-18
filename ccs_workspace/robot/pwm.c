/*
 * -------------------------------------------
 *    MSP432 DriverLib - v3_21_00_05 
 * -------------------------------------------
 *
 * --COPYRIGHT--,BSD,BSD
 * Copyright (c) 2016, Texas Instruments Incorporated
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * --/COPYRIGHT--*/
/*******************************************************************************
 * MSP432 Timer_A - Variable PWM
 *
 * Description: In this example, the Timer_A module is used to create a precision 
 * PWM with an adjustable duty cycle. The PWM initial period is 200 ms and is
 * output on P2.4. The initial duty cycle of the PWM is 10%, however when the
 * button is pressed on P1.1 the duty cycle is sequentially increased by 10%.
 * Once the duty cycle reaches 90%, the duty cycle is reset to 10% on the
 * following button press.
 *
 *                MSP432P401
 *             ------------------
 *         /|\|                  |
 *          | |                  |
 *          --|RST         P1.1  |<--Toggle Switch
 *            |                  |
 *            |                  |
 *            |            P2.4  |--> Output PWM
 *            |                  |
 *            |                  |
 *
* Author: Timothy Logan
 *******************************************************************************/
/* DriverLib Includes */
#include "driverlib.h"

/* Standard Includes */
#include <stdint.h>

#include <stdbool.h>

#include "pwm.h"

/* Timer_A PWM Configuration Parameter */
Timer_A_PWMConfig pwmConfig =
{
        TIMER_A_CLOCKSOURCE_SMCLK,
        TIMER_A_CLOCKSOURCE_DIVIDER_1,
        3200,
        TIMER_A_CAPTURECOMPARE_REGISTER_3,
        TIMER_A_OUTPUTMODE_RESET_SET,
        0
};


void PWM_init(void)
{
//    /* Setting MCLK to REFO at 128Khz for LF mode
//     * Setting SMCLK to 64Khz */
//    MAP_CS_setReferenceOscillatorFrequency(CS_REFO_128KHZ);
//    MAP_CS_initClockSignal(CS_MCLK, CS_REFOCLK_SELECT, CS_CLOCK_DIVIDER_1);
//    MAP_CS_initClockSignal(CS_SMCLK, CS_REFOCLK_SELECT, CS_CLOCK_DIVIDER_2);
//    MAP_PCM_setPowerState(PCM_AM_LF_VCORE0);

    /* Configuring GPIO2.4 as peripheral output for PWM  and P6.7 for button
     * interrupt */
    MAP_GPIO_setAsPeripheralModuleFunctionOutputPin(GPIO_PORT_P2, GPIO_PIN6 | GPIO_PIN7,
            GPIO_PRIMARY_MODULE_FUNCTION);

    /* Set motor direction to forwards */
    MAP_GPIO_setAsOutputPin(GPIO_PORT_P5, GPIO_PIN4 | GPIO_PIN5);
    MAP_GPIO_setOutputHighOnPin(GPIO_PORT_P5, GPIO_PIN4 | GPIO_PIN5);

    MAP_GPIO_setAsInputPinWithPullUpResistor(GPIO_PORT_P1, GPIO_PIN1);
    MAP_GPIO_clearInterruptFlag(GPIO_PORT_P1, GPIO_PIN1);
    MAP_GPIO_enableInterrupt(GPIO_PORT_P1, GPIO_PIN1);

    /* Configuring Timer_A to have a period of approximately 50ms and
     * an initial duty cycle of 10% of that (320 ticks)  */
    MAP_Timer_A_generatePWM(TIMER_A0_BASE, &pwmConfig);

    /* Enabling interrupts and starting the watchdog timer */
    MAP_Interrupt_enableInterrupt(INT_PORT1);
}

/* Port1 ISR - This ISR will progressively step up the duty cycle of the PWM
 * on a button press
 */
void PORT1_IRQHandler(void)
{
    uint32_t status = MAP_GPIO_getEnabledInterruptStatus(GPIO_PORT_P1);
    MAP_GPIO_clearInterruptFlag(GPIO_PORT_P1, status);

    if (status & GPIO_PIN1)
    {
    	PWM_set(0, 0);
    }
}

void PWM_set(int8_t left, int8_t right) {
	if (right >= 0) {
	    MAP_GPIO_setOutputHighOnPin(GPIO_PORT_P5, GPIO_PIN5);
	} else {
	    MAP_GPIO_setOutputLowOnPin(GPIO_PORT_P5, GPIO_PIN5);
	    right = -right;
	}
	pwmConfig.dutyCycle = ((uint32_t)pwmConfig.timerPeriod) * right / 128;
    pwmConfig.compareRegister = TIMER_A_CAPTURECOMPARE_REGISTER_3;
    MAP_Timer_A_generatePWM(TIMER_A0_BASE, &pwmConfig);

	if (left >= 0) {
	    MAP_GPIO_setOutputHighOnPin(GPIO_PORT_P5, GPIO_PIN4);
	} else {
	    MAP_GPIO_setOutputLowOnPin(GPIO_PORT_P5, GPIO_PIN4);
	    left = -left;
	}
	pwmConfig.dutyCycle = ((uint32_t)pwmConfig.timerPeriod) * left / 128;
    pwmConfig.compareRegister = TIMER_A_CAPTURECOMPARE_REGISTER_4;
    MAP_Timer_A_generatePWM(TIMER_A0_BASE, &pwmConfig);
}
