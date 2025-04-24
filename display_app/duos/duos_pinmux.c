#include "devmem.h"
#include "func.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "Debug.h"

#define NELEMS(x) (sizeof(x) / sizeof((x)[0]))
#define PINMUX_BASE 0x03001000
#define INVALID_PIN 9999

struct pinlist {
	char name[32];
	uint32_t offset;
} pinlist_st;

struct pinlist cv181x_pin[] = {
	{ "A16", 0x40 },	// UART0_TX
	{ "A17", 0x44 },	// UART0_RX
	{ "A19", 0x64 },	// JTAG_CPU_TMS
	{ "A18", 0x68 },	// JTAG_CPU_TCK
	{ "A20", 0x6c },	// JTAG_CPU_TRST
	{ "A28", 0x70 },	// IIC0_SCL
	{ "A29", 0x74 },	// IIC0_SDA
	{ "E0", 0xa4 },		// PWR_GPIO0
	{ "E1", 0xa8 },		// PWR_GPIO1
	{ "E2", 0xac },		// PWR_GPIO2
	{ "B1", 0xf0 },		// ADC3
	{ "B2", 0xf4 },		// ADC2
	{ "B3", 0xf8 },		// ADC1
	{ "B11", 0x134 },	// VIVO_D10
	{ "B12", 0x138 },	// VIVO_D9
	{ "B13", 0x13c },	// VIVO_D8
	{ "B14", 0x140 },	// VIVO_D7
	{ "B15", 0x144 },	// VIVO_D6
	{ "B16", 0x148 },	// VIVO_D5
	{ "B17", 0x14c },	// VIVO_D4
	{ "B18", 0x150 },	// VIVO_D3
	{ "B19", 0x154 },	// VIVO_D2
	{ "B20", 0x158 },	// VIVO_D1
	{ "B21", 0x15c },	// VIVO_D0
	{ "B22", 0x160 },	// VIVO_CLK
	{ "C18", 0x194 },	// PAD_MIPI_TXM4
	{ "C19", 0x198 },	// PAD_MIPI_TXP4
	{ "C20", 0x19c },	// PAD_MIPI_TXM3
	{ "C21", 0x1a0 },	// PAD_MIPI_TXP3
	{ "C16", 0x1a4 },	// PAD_MIPI_TXM2
	{ "C17", 0x1a8 },	// PAD_MIPI_TXP2
	{ "C14", 0x1ac },	// PAD_MIPI_TXM1
	{ "C15", 0x1b0 },	// PAD_MIPI_TXP1
	{ "C12", 0x1b4 },	// PAD_MIPI_TXM0
	{ "C13", 0x1b8 },	// PAD_MIPI_TXP0
};

uint32_t convert_func_to_value(char *pin, char *func)
{
	uint32_t i = 0;
	uint32_t max_fun_num = NELEMS(cv181x_pin_func);
	char v;

	for (i = 0; i < max_fun_num; i++) {
		if (strcmp(cv181x_pin_func[i].func, func) == 0) {
			if (strncmp(cv181x_pin_func[i].name, pin, strlen(pin)) == 0) {
				v = cv181x_pin_func[i].name[strlen(cv181x_pin_func[i].name) - 1];
				break;
			}
		}
	}

	if (i == max_fun_num) {
		Debug("ERROR: invalid pin or func\n");
		return INVALID_PIN;
	}

	return (v - 0x30);
}

int duos_pinmux(char *pin, char *func)
{
	int opt = 0;
	uint32_t i = 0;
	uint32_t value;
	uint32_t f_val;

	Debug("pin %s\n", pin);
	Debug("func %s\n", func);

	for (i = 0; i < NELEMS(cv181x_pin); i++) {
		if (strcmp(pin, cv181x_pin[i].name) == 0)
			break;
	}

	if (i != NELEMS(cv181x_pin)) {
		f_val = convert_func_to_value(pin, func);
		if (f_val == INVALID_PIN)
				return 1;
		devmem_writel(PINMUX_BASE + cv181x_pin[i].offset, f_val);

		Debug("register: %x\n", PINMUX_BASE + cv181x_pin[i].offset);
		Debug("value: %d\n", f_val);

	} else {
		Debug("\nInvalid option: %s\n", optarg);
	}

	return 0;
}
