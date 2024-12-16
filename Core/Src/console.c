/**
  **********************************************************************************************************************
  * @file    console.c
  * @author  MCD Application Team
  * @brief   This file implements the web server console services.
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
#include "console.h"

#include "trcRecorder.h"

#if defined(__ICCARM__)
#include <LowLevelIOInterface.h>
#endif /* __ICCARM__ */

/** @addtogroup STM32U5xx_Demonstration
  * @{
  */

/** @addtogroup IOT_HTTP_WebServer
  * @{
  */

/* Private typedef ---------------------------------------------------------------------------------------------------*/
/* Private define ----------------------------------------------------------------------------------------------------*/
/* Private macro -----------------------------------------------------------------------------------------------------*/
/* Private variables -------------------------------------------------------------------------------------------------*/
/* Console handle declaration */
UART_HandleTypeDef Console_UARTHandle;
/* Console buffer declaration */
char console_buffer[CONSOLE_BUFFER_SIZE];

/* Private function prototypes ---------------------------------------------------------------------------------------*/

int console_config(void)
{
  /* Set parameter to be configured */
  Console_UARTHandle.Instance                    = USART1;
  Console_UARTHandle.Init.BaudRate               = 1000000;
  Console_UARTHandle.Init.WordLength             = UART_WORDLENGTH_8B;
  Console_UARTHandle.Init.StopBits               = UART_STOPBITS_1;
  Console_UARTHandle.Init.Parity                 = UART_PARITY_NONE;
  Console_UARTHandle.Init.Mode                   = UART_MODE_TX_RX;
  Console_UARTHandle.Init.HwFlowCtl              = UART_HWCONTROL_NONE;
  Console_UARTHandle.Init.OverSampling           = UART_OVERSAMPLING_16;
  Console_UARTHandle.Init.OneBitSampling         = UART_ONE_BIT_SAMPLE_DISABLE;
  Console_UARTHandle.Init.ClockPrescaler         = UART_PRESCALER_DIV1;
  Console_UARTHandle.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;

  /* Initialize the UART mode */
  if (HAL_UART_Init(&Console_UARTHandle) != HAL_OK)
  {
    return -1;
  }

  /* Disable the UART FIFO mode */
  if (HAL_UARTEx_DisableFifoMode(&Console_UARTHandle) != HAL_OK)
  {
    return -2;
  }

  return 0;
}

/**
  * @brief  Print web server application header in hyperterminal
  * @param  None
  * @retval None
  */
void webserver_console_print_header(void)
{
  printf("\r\n");
  printf("=======================================================================================================\r\n");
  printf("============================       STM32U5 Webserver Demonstration        =============================\r\n");
  printf("=======================================================================================================\r\n");
}

/**
  * @brief  Get wifi SSID (LOGIN) via hyperterminal
  * @param  None
  * @retval Web Server status
  */

char _char_from_kbhit = 0;

int kbhit(void)
{
	char ch;
	if (HAL_UART_Receive(&Console_UARTHandle, (uint8_t *) &ch, 1, 0) != HAL_OK)
	{
	    return 0;
	}
	_char_from_kbhit = ch;
	return ch;
}

extern volatile int demo_isrs_enabled;



extern TraceStateMachineStateHandle_t reader_idle;
extern TraceStateMachineHandle_t reader_jobs;
extern TraceStateMachineStateHandle_t reader_gets;

int get_string(char *buf)
{
  char ch;
  uint32_t count = 0;

  // Disable demo ISRs to pause the demo app during printf calls (avoids overload)...
  demo_isrs_enabled = 0;

  xTraceStateMachineSetState(reader_jobs, reader_gets);

  /* Clear pending characters */
  if (HAL_UART_AbortReceive(&Console_UARTHandle) != HAL_OK)
  {
    return -1;
  }

  if (_char_from_kbhit != 0)
  {
	  printf("%c", _char_from_kbhit);
	  buf[0] = _char_from_kbhit;
	  count++;
  }

  if (buf[0] != '\n' && buf[0] != '\r')
  {
	  /* Repeat receiving character  */
	  do
	  {
		/* Get entered character */
		if (HAL_UART_Receive(&Console_UARTHandle, (uint8_t *) &ch, 1, HAL_MAX_DELAY) != HAL_OK)
		{
		  return -2;
		}

		/* Store entered character */
		buf[count] = ch;
		count++;

		/* Print entered character */
		if (ch != 0)
		{
		  printf("%c",ch);
		}

	  }
	  while ((ch != '\r') && (ch != 0) && (ch !='\n'));
  }
  /* Clear end of characters symbols */
  do
  {
    buf[count] = 0;
    count--;
  }
  while((buf[count] == '\r') || (buf[count] == '\n'));

  demo_isrs_enabled = 1;

  xTraceStateMachineSetState(reader_jobs, reader_idle);

  return count;
}

#if (0)
/**
  * @brief  Get wifi PWD (PASSWORD) via hyperterminal
  * @param  None
  * @retval Web Server status
  */
int webserver_console_get_password(ap_t *net_wifi_registred_hotspot,
                                                       char *PassWord)
{
  char ch;
  uint32_t count = 0;

  /* Print get PWD message */
  printf("\r\n");
  printf("*** Please enter your wifi password : =================================================================\r\n");

  /* Clear pending characters */
  if (HAL_UART_AbortReceive(&Console_UARTHandle) != HAL_OK)
  {
    return -1;
  }

  /* Repeat receiving character until getting all SSID */
  do
  {
    if (HAL_UART_Receive(&Console_UARTHandle, (uint8_t *) &ch, 1, HAL_MAX_DELAY) != HAL_OK)
    {
      return -2;
    }

    PassWord[count] = ch;
    count++;

    /* Print entered character */
    if ((ch != '\n') && (ch != 0) && (ch != '\r'))
    {
      printf("*");
    }

  }
  while ((ch != '\n') && (ch != '\r') && (ch != 0));

  /* Clear end of characters symbols */
  do
  {
    PassWord[count] = 0;
    count--;

  }
  while ((PassWord[count] == '\n') || (PassWord[count] == ' ') || (PassWord[count] == '\r'));

  /* Store user PWD */
  net_wifi_registred_hotspot->pwd = PassWord;

  return 0;
}
#endif

/**
  * @brief  Retargets the C library __write function to the IAR function iar_fputc.
  * @param  file: file descriptor.
  * @param  ptr: pointer to the buffer where the data is stored.
  * @param  len: length of the data to write in bytes.
  * @retval length of the written data in bytes.
  */
#if defined(__ICCARM__)
size_t __write(int file, unsigned char const *ptr, size_t len)
{
  size_t idx;
  unsigned char const *pdata = ptr;

  for (idx = 0; idx < len; idx++)
  {
    iar_fputc((int)*pdata);
    pdata++;
  }
  return len;
}
#endif /* __ICCARM__ */

/**
  * @brief  Retargets the C library printf function to the USART.
  */
PUTCHAR_PROTOTYPE
{
  while (HAL_OK != HAL_UART_Transmit(&Console_UARTHandle, (uint8_t *) &ch, 1, 30000))
  {
    ;
  }
  return ch;
}

/**
  * @brief  Retargets the C library scanf function to the USART.
  * @param  None
  * @retval None
  */
GETCHAR_PROTOTYPE
{
  char ch;

  while (HAL_OK != HAL_UART_Receive(&Console_UARTHandle, (uint8_t *) &ch, 1, HAL_MAX_DELAY))
  {
    ;
  }

  return ch;
}
