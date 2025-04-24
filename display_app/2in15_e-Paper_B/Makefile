DIR_Config	 = ./lib/Config
DIR_EPD		 = ./lib/e-Paper
DIR_FONTS	 = ./lib/Fonts
DIR_GUI		 = ./lib/GUI
DIR_SRC      = ./src
DIR_BIN		 = ./bin
DIR_DUOS	 = ../duos

EPD = NULL
OBJ_C = $(wildcard ${DIR_EPD}/*.c ${DIR_GUI}/*.c ${DIR_SRC}/*.c ${DIR_FONTS}/*.c ${DIR_DUOS}/*.c)

OBJ_O = $(patsubst %.c,${DIR_BIN}/%.o,$(notdir ${OBJ_C}))
DUO_DEV_C = $(wildcard $(DIR_BIN)/dev_hardware_SPI.o $(DIR_BIN)/DUO_sysfs_gpio.o $(DIR_BIN)/DEV_Config.o)

DEBUG = -D DEBUG

.PHONY : DUO clean

DUO:DUO_DEV DUO_epd 

TARGET = epd
CC = musl-gcc
MSG = -ffunction-sections -fdata-sections -Wall
CFLAGS += $(MSG) -D $(EPD)

debug_cflags=-g -O -ggdb3 -ggdb -g3 -ggdb2 -g1 -g0
#debug_cflags=-O3 -DNDEBUG
arch_cflags=-mcpu=c906fdv -mcmodel=medany
arch_ldflags=-D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64
sys_lib=../libs/system/musl_riscv64
sys_inc=../include/system
CFLAGS+=${debug_cflags} -I${sys_inc}

LDFLAGS=${arch_ldflags} -L${sys_lib}
LDFLAGS += -Wl,-rpath,../libs/system/musl_riscv64 -lwiringx


DUO_epd:${OBJ_O}
	echo $(@)
	$(CC) $(CFLAGS) -D DUO $(OBJ_O) $(DUO_DEV_C) -o $(TARGET) $(DEBUG) $(LDFLAGS)

$(shell mkdir -p $(DIR_BIN))

${DIR_BIN}/%.o:$(DIR_SRC)/%.c
	$(CC) $(CFLAGS) -c	$< -o $@ -I $(DIR_Config) -I $(DIR_GUI) -I $(DIR_EPD) -I $(DIR_DUOS) $(DEBUG) $(LDFLAGS)
	
${DIR_BIN}/%.o:$(DIR_EPD)/%.c
	$(CC) $(CFLAGS) -c	$< -o $@ -I $(DIR_Config) $(DEBUG) $(LDFLAGS)

${DIR_BIN}/%.o:$(DIR_FONTS)/%.c 
	$(CC) $(CFLAGS) -c	$< -o $@ $(DEBUG) $(LDFLAGS)
	
${DIR_BIN}/%.o:$(DIR_GUI)/%.c
	$(CC) $(CFLAGS) -c	$< -o $@ -I $(DIR_Config) $(DEBUG) $(LDFLAGS)

${DIR_BIN}/%.o:$(DIR_DUOS)/%.c
	$(CC) $(CFLAGS) -c	$< -o $@ -I $(DIR_Config) $(DEBUG) -static

DUO_DEV:
#	$(CC) $(CFLAGS) -c $(DIR_Config)/dev_hardware_SPI.c -o $(DIR_BIN)/dev_hardware_SPI.o $(DEBUG)
	$(CC) $(CFLAGS) -c $(DIR_Config)/DEV_Config.c -o $(DIR_BIN)/DEV_Config.o $(DEBUG)
	


clean :
	rm $(DIR_BIN)/*.* 
	rm $(TARGET) 