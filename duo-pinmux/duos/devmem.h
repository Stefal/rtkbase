#ifndef _DEVMEM_H_
#define _DEVMEM_H_

#include <stdint.h>

void *devm_map(unsigned long addr, int len);
void devm_unmap(void *virt_addr, int len);

uint32_t devmem_readl(unsigned long addr);
void devmem_writel(unsigned long addr, uint32_t val);

#endif
