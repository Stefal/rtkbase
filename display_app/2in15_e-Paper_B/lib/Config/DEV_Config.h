#ifndef _DEV_CONFIG_H_
#define _DEV_CONFIG_H_

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "Debug.h"

/* Support for MilkV Duo S*/
#include "wiringx.h"

/**
 * GPIO
**/

/* SPI2 is routed to J3 B13-B15 */
#define SPI_PORT    0
#define EPD_DC_PIN (3) //26
#define EPD_CS_PIN (5) //21
#define EPD_RST_PIN (7)
#define EPD_BUSY_PIN (24)
#define EPD_PWR_PIN (15)
#define EPD_SCLK_PIN (23)
#define EPD_MOSI_PIN (19)

/**
 * data
**/
#define UBYTE   uint8_t
#define UWORD   uint16_t
#define UDOUBLE uint32_t

/*------------------------------------------------------------------------------------------------------*/
void DEV_Digital_Write(UWORD Pin, UBYTE Value);
UBYTE DEV_Digital_Read(UWORD Pin);

void DEV_SPI_WriteByte(UBYTE Value);
void DEV_SPI_Write_nByte(uint8_t *pData, uint32_t Len);
void DEV_Delay_ms(UDOUBLE xms);

void DEV_SPI_SendData(UBYTE Reg);
void DEV_SPI_SendnData(UBYTE *Reg);
UBYTE DEV_SPI_ReadData();

UBYTE DEV_Module_Init(void);
void DEV_Module_Exit(void);


#endif
