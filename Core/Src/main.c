#include <stdio.h>
#include <stdlib.h>
#include "main.h"
#include "trcRecorder.h"

#define REGISTER_TASK(ID, name) xTraceTaskRegisterWithoutHandle((void*)ID, name, 0)

#define TASK_IDLE 100
#define TASK_MAIN 101

volatile unsigned int throttle_delay = 5000;

TraceStringHandle_t chn = NULL;

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
    REGISTER_TASK(TASK_MAIN, "main-thread");
    REGISTER_TASK(TASK_IDLE, "IDLE");
    xTraceTaskReady(TASK_IDLE);
    xTraceTaskReady(TASK_MAIN);
    __set_BASEPRI(0);
    __enable_irq();

   /* Main loop */
    while(1)
    {
    	/* Not needed when using an RTOS... */
        xTraceTaskReady(TASK_MAIN);
    	xTraceTaskSwitch((void*)TASK_MAIN, 0);

    	/* Log the "trottle delay" as a user event */
    	xTracePrintF(chn, "%d", throttle_delay);

    	/* The throttle delay, allows for adjusting the data rate. */
    	for (volatile int counter=0; counter<throttle_delay; counter++);

    	/* Not needed when using an RTOS... */
        xTraceTaskSwitch((void*)TASK_IDLE, 0);
    }

    return 0;
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


