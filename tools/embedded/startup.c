/* Minimal bare-metal start-up for Cortex-M3: vector table, data/bss init, stack painting. */
#include <stdint.h>
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _stack_bottom, _stack_top;
int main(void);
void reset_handler(void);
static void fault(void) { for (;;) {} }

__attribute__((section(".vectors"), used))
static void (*const vectors[16])(void) = {
    (void (*)(void))&_stack_top, reset_handler, fault, fault, fault, fault, fault, 0, 0, 0, 0, fault, fault, 0, fault, fault};

void reset_handler(void)
{
    uint32_t *s = &_sidata, *d = &_sdata;
    while (d < &_edata) *d++ = *s++;
    for (d = &_sbss; d < &_ebss; ++d) *d = 0;
    /* paint the unused RAM below the current stack pointer so that main() can measure
       how deep the stack went */
    for (d = &_stack_bottom; d < &_stack_top - 16; ++d) *d = 0xA5A5A5A5u;
    main();
    for (;;) {}
}
