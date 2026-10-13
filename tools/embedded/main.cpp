// Replays one compiler trace on STRATA (or, with -DTABLE_ARENA, on the conventional arena
// table) in fixed-buffer mode.
// The same file is built for the host (to obtain the expected checksum) and for a
// bare-metal Cortex-M3 (QEMU mps2-an385, 64 KiB RAM, no heap, no operating system).
#include <stdint.h>
#include <string.h>

#include "../../include/strata/strata.hpp"
#include "../../benchmarks/baselines/arena_chain.hpp"
#include "trace_data.h"

// One interface over the two bounded tables.
#ifdef TABLE_ARENA
struct Tab {
    arena_chain::Table t;
    Tab(void* b, size_t n) : t(b, n) {}
    bool enter() { return t.enter_scope(); }
    void leave() { t.exit_scope(); }
    int declare(const char* s, size_t n, int32_t v) { return t.declare(s, n, v); }
    bool resolve(const char* s, size_t n, int32_t* v) { return t.resolve(s, n, v); }
    uint32_t peak() const { return (uint32_t)t.peak_used_bytes(); }
};
#define TABLE_NAME "arena_chain"
#elif defined(TABLE_BOUNDED)
// STRATA with a static index (-DINDEX_SLOTS), a probe limit (-DMAX_PROBE) and the keyed hash.
static strata::Options bounded_options() {
    strata::Options o;
    o.index_slots = INDEX_SLOTS;
    o.max_probe = MAX_PROBE;
    o.keyed = true;
    o.key[0] = 0x0a1b2c3du;      // a device would draw this from its entropy source
    o.key[1] = 0x4e5f6071u;
    return o;
}
struct Tab {
    strata::Table t;
    Tab(void* b, size_t n) : t(b, n, bounded_options()) {}
    bool enter() { return t.enter_scope() == strata::kOk; }
    void leave() { t.exit_scope(); }
    int declare(const char* s, size_t n, int32_t v) { return t.declare(s, n, v); }
    bool resolve(const char* s, size_t n, int32_t* v) { return t.resolve(s, n, v); }
    uint32_t peak() const { return (uint32_t)t.stats().peak_used_bytes; }
};
#define TABLE_NAME "STRATA bounded (static index, probe limit, keyed hash)"
#else
struct Tab {
    strata::Table t;
    Tab(void* b, size_t n) : t(b, n) {}
    bool enter() { return t.enter_scope() == strata::kOk; }
    void leave() { t.exit_scope(); }
    int declare(const char* s, size_t n, int32_t v) { return t.declare(s, n, v); }
    bool resolve(const char* s, size_t n, int32_t* v) { return t.resolve(s, n, v); }
    uint32_t peak() const { return (uint32_t)t.stats().peak_used_bytes; }
};
#define TABLE_NAME "STRATA"
#endif

#ifndef BUFFER_BYTES
#define BUFFER_BYTES 24576
#endif
static uint32_t g_buffer[BUFFER_BYTES / 4];

struct Result { uint32_t checksum, refused, peak_used, lookups, hits, declares; };

inline void* operator new(size_t, void* p, int) noexcept { return p; }   // placement form without <new>

static Result replay() {
    Result r = {2166136261u, 0, 0, 0, 0, 0};
    alignas(Tab) static unsigned char room[sizeof(Tab)];
    Tab* t = new (room, 0) Tab(g_buffer, sizeof g_buffer);
    int32_t seq = 0;
    for (uint32_t i = 0; i < kOps; ++i) {
        const char* nm = kNames[kName[i]];
        switch (kKind[i]) {
        case 0:
            if (t->peak() > r.peak_used) r.peak_used = t->peak();
            t->~Tab();
            t = new (room, 0) Tab(g_buffer, sizeof g_buffer);
            seq = 0;
            break;
        case 1: if (!t->enter()) ++r.refused; break;
        case 2: t->leave(); break;
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
    if (t->peak() > r.peak_used) r.peak_used = t->peak();
    t->~Tab();
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
    put(TABLE_NAME " on bare-metal Cortex-M3 (QEMU mps2-an385)\n");
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
    put(r.refused ? "RESULT: DOES NOT FIT\n" : (r.checksum == EXPECTED_CHECKSUM ? "RESULT: PASS\n" : "RESULT: FAIL\n"));
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
