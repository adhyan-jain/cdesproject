// Replays one compiler trace on STRATA in fixed-buffer mode.
// The same file is built for the host (to obtain the expected checksum) and for a
// bare-metal Cortex-M3 (QEMU mps2-an385, 64 KiB RAM, no heap, no operating system).
#include <stdint.h>
#include <string.h>

#include "../../include/strata/strata.hpp"
#include "trace_data.h"

#ifndef BUFFER_BYTES
#define BUFFER_BYTES 24576
#endif
static uint32_t g_buffer[BUFFER_BYTES / 4];

struct Result { uint32_t checksum, refused, peak_used, lookups, hits, declares; };

inline void* operator new(size_t, void* p, int) noexcept { return p; }   // placement form without <new>

static Result replay() {
    Result r = {2166136261u, 0, 0, 0, 0, 0};
    alignas(strata::Table) static unsigned char room[sizeof(strata::Table)];
    strata::Table* t = new (room, 0) strata::Table(g_buffer, sizeof g_buffer);
    int32_t seq = 0;
    for (uint32_t i = 0; i < kOps; ++i) {
        const char* nm = kNames[kName[i]];
        switch (kKind[i]) {
        case 0:
            if (t->stats().peak_used_bytes > r.peak_used) r.peak_used = (uint32_t)t->stats().peak_used_bytes;
            t->~Table();
            t = new (room, 0) strata::Table(g_buffer, sizeof g_buffer);
            seq = 0;
            break;
        case 1: if (t->enter_scope() != strata::kOk) ++r.refused; break;
        case 2: t->exit_scope(); break;
        case 3: {
            int s = t->declare(nm, strlen(nm), seq++);
            if (s < 0) ++r.refused;
            ++r.declares;
            r.checksum = (r.checksum ^ (uint32_t)(s + 2)) * 16777619u;
            break;
        }
        default: {
            int32_t v = -1;
            bool ok = t->resolve(nm, strlen(nm), &v);
            ++r.lookups;
            r.hits += ok;
            r.checksum = (r.checksum ^ (uint32_t)(ok ? v : -1)) * 16777619u;
            break;
        }
        }
    }
    if (t->stats().peak_used_bytes > r.peak_used) r.peak_used = (uint32_t)t->stats().peak_used_bytes;
    t->~Table();
    return r;
}

#ifdef __arm__
// ---- semihosting output (no C library I/O) ----------------------------------------------
static int semihost(int op, void* arg) {
    register int r0 __asm__("r0") = op;
    register void* r1 __asm__("r1") = arg;
    __asm__ volatile("bkpt 0xAB" : "+r"(r0) : "r"(r1) : "memory");
    return r0;
}
static void put(const char* s) { semihost(0x04, (void*)s); }
static void put_u(const char* label, uint32_t v) {
    char b[12];
    int i = 11;
    b[i] = 0;
    do { b[--i] = (char)(48 + v % 10); v /= 10; } while (v);
    put(label);
    put(b + i);
    put("\n");
}
extern "C" uint32_t _stack_bottom, _stack_top, _sbss, _ebss, _sdata, _edata;
// The fixed-buffer mode must not need an allocator: these stubs fail on purpose.
extern "C" void* malloc(size_t) { return 0; }
extern "C" void free(void*) {}
extern "C" void* realloc(void*, size_t) { return 0; }

int main() {
    Result r = replay();
    uint32_t* p = &_stack_bottom;
    while (p < &_stack_top && *p == 0xA5A5A5A5u) ++p;   // first word the stack ever touched
    put("STRATA on bare-metal Cortex-M3 (QEMU mps2-an385)\n");
    put_u("operations          ", kOps);
    put_u("declares            ", r.declares);
    put_u("lookups             ", r.lookups);
    put_u("lookup hits         ", r.hits);
    put_u("refused operations  ", r.refused);
    put_u("buffer bytes        ", sizeof g_buffer);
    put_u("peak used bytes     ", r.peak_used);
    put_u("stack bytes used    ", (uint32_t)((char*)&_stack_top - (char*)p));
    put_u("static RAM bytes    ", (uint32_t)((char*)&_ebss - (char*)&_sbss) + (uint32_t)((char*)&_edata - (char*)&_sdata));
    put_u("checksum            ", r.checksum);
    put_u("expected (host run) ", EXPECTED_CHECKSUM);
    put(r.checksum == EXPECTED_CHECKSUM && r.refused == 0 ? "RESULT: PASS\n" : "RESULT: FAIL\n");
    semihost(0x18, (void*)0x20026);                     // SYS_EXIT, ADP_Stopped_ApplicationExit
    for (;;) {}
}
#else
#include <stdio.h>
int main() {
    Result r = replay();
    printf("%u %u %u\n", r.checksum, r.refused, r.peak_used);
    return 0;
}
#endif
