/**
  **********************************************************************************************************************
  * @file    main.c
  * @author  MCD Application Team
  * @brief   Main program body
  **********************************************************************************************************************
  * @attention
  *
  * Copyright (c) 2021 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  **********************************************************************************************************************
  */

/* Includes ----------------------------------------------------------------------------------------------------------*/
#include <stdio.h>
#include <stdlib.h>
#include "main.h"
#include "trcRecorder.h"


/******************************************************************************
 * REGISTER_TASK
 *
 * This macro is used to manually register two tasks, "IDLE" and "main-thread".
 * where IDLE represents the HAL_Delay() call in main_superloop(). The macro
 * stores a Task ID together with a display name for Tracealyzer. The Task IDs
 * are passed as arguments to xTraceTaskSwitch() for tracing when entering and
 * leaving the HAL_Delay call.
 *
 * Calling xTraceTaskSwitch and REGISTER_TASK manually like this is only needed
 * for bare-metal systems. When using a supported RTOS such as FreeRTOS, all
 * kernel tasks are traced automatically.
 *
 * Other alternatives for more detailed TraceRecorder tracing includes:
 *  - User events (see TraceRecorder/include/trcPrint.h)
 *  - State Machines (see TraceRecorder/include/trcStateMachine.h)
 *  - Runnables (see TraceRecorder/include/trcRunnable.h)
 *  - Interval Sets (see TraceRecorder/include/trcInterval.h)
 *
 *****************************************************************************/
#define REGISTER_TASK(ID, name) xTraceTaskRegisterWithoutHandle((void*)ID, name, 0)

// Handles for baremetal "tasks" (see above)
#define TASK_IDLE 100
#define TASK_MAIN 101

volatile unsigned int throttle_delay = 5000;

int main(void)
{
	vTraceInitialize();

	HAL_Init();

	/* Configure the System clock to have a frequency of 120 MHz */
	system_clock_config();

	/* Use systick as time base source and configure 1ms tick (default clock after Reset is HSI) */
	HAL_InitTick(TICK_INT_PRIORITY);

	/* Enable the Instruction Cache */
	instruction_cache_enable();

	/* Initialize bsp resources */
	bsp_init();

	/* No buffer for printf usage, just print characters one by one.*/
	setbuf(stdout, NULL);

	console_config();

	BSP_PB_Init(BUTTON_USER, BUTTON_MODE_EXTI);

	/* Initialize Percepio TraceRecorder (stores events to ring buffer) */
	xTraceEnable(TRC_START);

	printf("\nTracealyzer STLINK/ITM streaming demo\n\n");

    /* Just to set a better name for the main thread...*/
    REGISTER_TASK(TASK_MAIN, "main-thread");

    /* Used for tracing the HAL_Delay call in the bare-metal superloop. */
    REGISTER_TASK(TASK_IDLE, "IDLE");

    // Perhaps not needed.
    xTraceTaskReady(TASK_IDLE);
    xTraceTaskReady(TASK_MAIN);

    // Enable interrupts (needed?)
    __set_BASEPRI(0);
    __enable_irq();

    while(1)
    {
        xTraceTaskReady(TASK_MAIN);
    	xTraceTaskSwitch((void*)TASK_MAIN, 0);

    	for (volatile int counter=0; counter<throttle_delay; counter++);

        xTraceTaskSwitch((void*)TASK_IDLE, 0);
    }

    return 0;
}


void HAL_GPIO_EXTI_Rising_Callback(uint16_t GPIO_Pin)
{
	if (GPIO_Pin >> 13 == 1) // User Button is Pin 13
	{
		throttle_delay = throttle_delay * 0.8;
		printf("throttle_delay: %u\n", throttle_delay);
	}
}


