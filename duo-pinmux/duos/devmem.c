/*
 ** read/write phy addr in userspace
 ** open /dev/mem
 ** taiqiang.cao@bitmain.com
 */

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <termios.h>
#include <unistd.h>

#include "devmem.h"

// DEBUG_SET_LEVEL(DEBUG_LEVEL_ERR);
#define ERR printf
#define DEBUG printf

static int devmem_fd;

void *devm_map(unsigned long addr, int len)
{
	off_t offset;
	void *map_base;

	devmem_fd = open("/dev/mem", O_RDWR | O_SYNC);
	if (devmem_fd == -1) {
		ERR("cannot open '/dev/mem'\n");
		goto open_err;
	}
	//    DEBUG("/dev/mem opened.\n");

	offset = addr & ~(sysconf(_SC_PAGE_SIZE) - 1);

	map_base = mmap(NULL, len + addr - offset, PROT_READ | PROT_WRITE, MAP_SHARED, devmem_fd, offset);
	if (map_base == MAP_FAILED) {
		ERR("mmap failed\n");
		goto mmap_err;
	}

	// DEBUG("Memory mapped at address %p.\n", map_base + addr - offset);

	return map_base + addr - offset;

mmap_err:
	close(devmem_fd);

open_err:
	return NULL;
}

void devm_unmap(void *virt_addr, int len)
{
	unsigned long addr;

	if (devmem_fd == -1) {
		ERR("'/dev/mem' is closed\n");
		return;
	}

	/* page align */
	addr = (((unsigned long)virt_addr) & ~(sysconf(_SC_PAGE_SIZE) - 1));
	munmap((void *)addr, len + (unsigned long)virt_addr - addr);
	close(devmem_fd);
}

/* read/write 32bit data*/
uint32_t devmem_readl(unsigned long addr)
{
	uint32_t val;
	void *virt_addr;

	virt_addr = devm_map(addr, 4);
	if (virt_addr == NULL) {
		ERR("readl addr map failed\n");
		return 0;
	}

	val = *(uint32_t *)virt_addr;

	devm_unmap(virt_addr, 4);

	return val;
}

void devmem_writel(unsigned long addr, uint32_t val)
{
	void *virt_addr;

	virt_addr = devm_map(addr, 4);
	if (virt_addr == NULL) {
		ERR("writel addr map failed\n");
		return;
	}

	*(uint32_t *)virt_addr = val;

	devm_unmap(virt_addr, 4);
}
