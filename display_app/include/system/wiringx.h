/*
	Copyright (c) 2016 CurlyMo <curlymoo1@gmail.com>

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
*/

#ifndef _WIRING_X_H_
#define _WIRING_X_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <errno.h>
#include <syslog.h>

#define wiringXLog(a, b, ...) _wiringXLog(a, __FILE__, __LINE__, b, ##__VA_ARGS__)

extern void (*_wiringXLog)(int, char *, int, const char *, ...);

#define EXPORT __attribute__((visibility("default")))

#if !defined(PATH_MAX)
    #if defined(_POSIX_PATH_MAX)
        #define PATH_MAX _POSIX_PATH_MAX
    #else
        #define PATH_MAX 1024
    #endif
#endif

enum function_t {
	FUNCTION_UNKNOWN = 0,
	FUNCTION_DIGITAL = 2,
	FUNCTION_ANALOG = 4,
	FUNCTION_I2C = 16,
	FUNCTION_INTERRUPT = 32
};

enum pinmode_t {
	PINMODE_NOT_SET = 0,
	PINMODE_INPUT = 2,
	PINMODE_OUTPUT = 4,
	PINMODE_INTERRUPT = 8
};

enum isr_mode_t {
	ISR_MODE_UNKNOWN = 0,
	ISR_MODE_RISING = 2,
	ISR_MODE_FALLING = 4,
	ISR_MODE_BOTH = 8,
	ISR_MODE_NONE = 16
};

enum digital_value_t {
	LOW,
	HIGH
};

typedef struct wiringXSerial_t {
	unsigned int baud;
	unsigned int databits;
	unsigned int parity;
	unsigned int stopbits;
	unsigned int flowcontrol;
} wiringXSerial_t;

void delayMicroseconds(unsigned int);
int pinMode(int, enum pinmode_t);
int wiringXSetup(char *name, void (*func)(int, char *, int, const char *, ...));
int wiringXGC(void);

// int analogRead(int channel);
int digitalWrite(int, enum digital_value_t);
int digitalRead(int);
int waitForInterrupt(int, int);
int wiringXISR(int, enum isr_mode_t);

int wiringXI2CRead(int);
int wiringXI2CReadReg8(int, int);
int wiringXI2CReadReg16(int, int);
int wiringXI2CWrite(int, int);
int wiringXI2CWriteReg8(int, int, int);
int wiringXI2CWriteReg16(int, int, int);
int wiringXI2CSetup(const char *, int);

int wiringXSPIGetFd(int channel);
int wiringXSPIDataRW(int channel, unsigned char *data, int len);
int wiringXSPISetup(int channel, int speed);

int wiringXSerialOpen(const char *, struct wiringXSerial_t);
void wiringXSerialFlush(int);
void wiringXSerialClose(int);
void wiringXSerialPutChar(int, unsigned char);
void wiringXSerialPuts(int, const char *);
void wiringXSerialPrintf(int, const char *, ...);
int wiringXSerialDataAvail(int);
int wiringXSerialGetChar(int);

int wiringXPWMSetPeriod(int, long);
int wiringXPWMSetDuty(int, long);
int wiringXPWMSetPolarity(int, int);
int wiringXPWMEnable(int, int);

char *wiringXPlatform(void);
int wiringXValidGPIO(int);
int wiringXSelectableFd(int);
int wiringXSupportedPlatforms(char ***);

#ifdef __cplusplus
}
#endif

#endif
