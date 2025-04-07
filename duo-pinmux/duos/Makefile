CC = riscv64-unknown-linux-musl-gcc

source  = duo_pinmux.c devmem.c
object  = $(source:%.cc=%.o)

CFLAGS += -mcpu=c906fdv -march=rv64imafdcv0p7xthead -mcmodel=medany -mabi=lp64d -static

all: $(object)
	$(CC) $(CFLAGS) $(object) -o duo-pinmux

%.o: %.c
	$(CC) $(CFLAGS) -c $<

clean:
	$(RM) *.o duo-pinmux
