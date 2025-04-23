#include "DEV_Config.h"

/**
 * GPIO read and write
**/
void DEV_Digital_Write(UWORD Pin, UBYTE Value)
{

	digitalWrite(Pin, Value);

}

UBYTE DEV_Digital_Read(UWORD Pin)
{
	UBYTE Read_value = 0;

	Read_value = digitalRead(Pin);

	return Read_value;
}

/**
 * SPI
**/
void DEV_SPI_WriteByte(uint8_t Value)
{
	wiringXSPIDataRW(SPI_PORT, &Value,1);
}

void DEV_SPI_Write_nByte(uint8_t *pData, uint32_t Len)
{
	wiringXSPIDataRW(SPI_PORT, pData,Len);
}

/**
 * GPIO Mode
**/
void DEV_GPIO_Mode(UWORD Pin, UWORD Mode)
{

	Debug("not support");

}

/**
 * delay x ms
**/
void DEV_Delay_ms(UDOUBLE xms)
{
	Debug("Sleep for :%d ms\n", xms);
	usleep(xms*1000);
}

static int DEV_Equipment_Testing(void)
{
	FILE *fp;
	char issue_str[64];

	fp = fopen("/etc/issue", "r");
	if (fp == NULL) {
		Debug("Unable to open /etc/issue");
		return -1;
	}
	if (fread(issue_str, 1, sizeof(issue_str), fp) <= 0) {
		Debug("Unable to read from /etc/issue");
		return -1;
	}
	issue_str[sizeof(issue_str)-1] = '\0';
	fclose(fp);

	printf("Current environment: ");

	char systems[][9] = {"Raspbian", "Debian", "NixOS"};
	int detected = 0;
	for(int i=0; i<3; i++) {
		if (strstr(issue_str, systems[i]) != NULL) {
			printf("%s\n", systems[i]);
			detected = 1;
		}
	}
	if (!detected) {
		printf("OS not recognized\n");
		printf("Built for Debian, but unable to detect environment.\n");
		return -1;
	}

	return 0;
}



void DEV_GPIO_Init(void)
{

	if(wiringXValidGPIO(EPD_RST_PIN) != 0) {
        printf("Invalid GPIO %d\n", EPD_RST_PIN);
    }
	pinMode(EPD_RST_PIN, PINMODE_OUTPUT);

	if(wiringXValidGPIO(EPD_DC_PIN) != 0) {
        printf("Invalid GPIO %d\n", EPD_DC_PIN);
    }
	pinMode(EPD_DC_PIN, PINMODE_OUTPUT);

	if(wiringXValidGPIO(EPD_CS_PIN) != 0) {
        printf("Invalid GPIO %d\n", EPD_CS_PIN);
    }
	pinMode(EPD_CS_PIN, PINMODE_OUTPUT);


	if(wiringXValidGPIO(EPD_BUSY_PIN) != 0) {
        printf("Invalid GPIO %d\n", EPD_BUSY_PIN);
    }
	pinMode(EPD_BUSY_PIN, PINMODE_INPUT);

	if(wiringXValidGPIO(EPD_PWR_PIN) != 0) {
        printf("Invalid GPIO %d\n", EPD_PWR_PIN);
    }
	pinMode(EPD_PWR_PIN, PINMODE_OUTPUT);
	

	DEV_Digital_Write(EPD_CS_PIN, HIGH);
    DEV_Digital_Write(EPD_PWR_PIN, HIGH);

	DEV_Delay_ms(100);
    
}

void DEV_SPI_SendnData(UBYTE *Reg)
{
    UDOUBLE size;
    size = sizeof(Reg);
    for(UDOUBLE i=0 ; i<size ; i++)
    {
        DEV_SPI_SendData(Reg[i]);
    }
}

void DEV_SPI_SendData(UBYTE Reg)
{
	UBYTE i,j=Reg;

	DEV_Digital_Write(EPD_CS_PIN, LOW);
	for(i = 0; i<8; i++)
    {
        DEV_Digital_Write(EPD_SCLK_PIN, LOW);     
        if (j & 0x80)
        {
            DEV_Digital_Write(EPD_MOSI_PIN, 1);
        }
        else
        {
            DEV_Digital_Write(EPD_MOSI_PIN, 0);
        }
        
        DEV_Digital_Write(EPD_SCLK_PIN, HIGH);
        j = j << 1;
    }
	DEV_Digital_Write(EPD_SCLK_PIN, LOW);
	DEV_Digital_Write(EPD_CS_PIN, HIGH);
}

UBYTE DEV_SPI_ReadData()
{
	UBYTE i,j=0xff;
	DEV_Digital_Write(EPD_CS_PIN, LOW);
	for(i = 0; i<8; i++)
	{
		DEV_Digital_Write(EPD_SCLK_PIN, LOW);
		j = j << 1;
		if (DEV_Digital_Read(EPD_MOSI_PIN))
		{
				j = j | 0x01;
		}
		else
		{
				j= j & 0xfe;
		}
		DEV_Digital_Write(EPD_SCLK_PIN, HIGH);
	}
	DEV_Digital_Write(EPD_SCLK_PIN, LOW);
	DEV_Digital_Write(EPD_CS_PIN, HIGH);
	return j;
}

/******************************************************************************
function:	Module Initialize, the library and initialize the pins, SPI protocol
parameter:
Info:
******************************************************************************/
UBYTE DEV_Module_Init(void)
{

	int fd_spi;

	if(DEV_Equipment_Testing() < 0) {
		return 1;
	}

    if(wiringXSetup("milkv_duos", NULL) == -1) {
        wiringXGC();
        return -1;
    }

	// GPIO Config
	DEV_GPIO_Init();

	// SPI Config
	if ((fd_spi = wiringXSPISetup(SPI_PORT, 1800000)) <0) {
        printf("SPI Setup failed: %d\n", fd_spi);
        wiringXGC();
        return -1;
    }

	return 0;
}

/******************************************************************************
function:	Module exits, closes SPI and BCM2835 library
parameter:
Info:
******************************************************************************/
void DEV_Module_Exit(void)
{
	
	DEV_Digital_Write(EPD_CS_PIN, LOW);
    DEV_Digital_Write(EPD_PWR_PIN, LOW);
	DEV_Digital_Write(EPD_DC_PIN, LOW);
	DEV_Digital_Write(EPD_RST_PIN, LOW);

}
