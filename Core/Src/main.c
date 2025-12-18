#include <stdio.h>
#include <stdlib.h>
#include "main.h"
#include "trcRecorder.h"

#define REGISTER_TASK(ID, name, prio) xTraceTaskRegisterWithoutHandle((void*)ID, name, prio)

#define TASK_IDLE 100
#define TASK_MAIN 101
#define TASK_A 102
#define TASK_B 103

volatile unsigned int throttle_delay = 1000;

TraceStringHandle_t chn = NULL;

void busy_wait(int i);

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

	/* Configure User Button */
	BSP_PB_Init(BUTTON_USER, BUTTON_MODE_EXTI);

	/* Initialize Percepio TraceRecorder */
	xTraceEnable(TRC_START);

	printf("\nTracealyzer STLINK/ITM streaming demo\n\n");

	/* Register a name to use as "channel" in xTracePrintF below. */
	xTraceStringRegister("Throttle delay", &chn);

	/* Not needed when using an RTOS... */
    REGISTER_TASK(TASK_MAIN, "main-thread", 0);
    REGISTER_TASK(TASK_A, "TaskA", 5);
    REGISTER_TASK(TASK_B, "TaskB", 10);
    REGISTER_TASK(TASK_IDLE, "IDLE", 0);

    __set_BASEPRI(0);
    __enable_irq();

    xTraceTaskReady(TASK_IDLE);
    busy_wait(100);

   /* Main loop */
    while(1)
    {
    	xTracePrintF(chn, "Throttle delay: %d",  throttle_delay);

    	/* This demo is without specific RTOS assumptions, so calling tracing functions directly. Using the baremetal kernelport.
    	 * These functions are normally called by the RTOS kernel if using a supported RTOS. */

        xTraceTaskReady(TASK_A);

        xTraceTaskSwitch((void*)TASK_A, 5);
        busy_wait(throttle_delay*2);

        xTraceTaskReady(TASK_B);
        xTraceTaskSwitch((void*)TASK_B, 10);
        busy_wait(throttle_delay);

        xTraceTaskSwitch((void*)TASK_A, 5);
        busy_wait(throttle_delay);

        xTraceTaskSwitch((void*)TASK_IDLE, 0);
        busy_wait(throttle_delay*10);
    }

    return 0;
}

void busy_wait(int i)
{
	for (volatile int counter=0; counter<i; counter++);
}

/* If pushing the blue "User Button" on the board */
void HAL_GPIO_EXTI_Rising_Callback(uint16_t GPIO_Pin)
{
	if (GPIO_Pin >> 13 == 1) // User Button is Pin 13
	{
		throttle_delay = throttle_delay * 0.8;
		printf("throttle_delay: %u\n", throttle_delay);
	}
}


