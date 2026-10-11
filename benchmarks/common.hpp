// Shared benchmark plumbing: heap accounting, trace loading, timers. Linux/glibc.
#ifndef CDES_BENCH_COMMON_HPP
#define CDES_BENCH_COMMON_HPP

#include <malloc.h>
#include <x86intrin.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <new>
#include <string>
#include <unordered_map>
#include <vector>

// ---- heap accounting ---------------------------------------------------------
// Every allocation made through operator new or through mem::alloc is counted with
// malloc_usable_size, so allocator rounding is included. Tables that call malloc
// directly are given mem::alloc / mem::dealloc as their allocator.
namespace mem {
struct Counters { size_t live, peak, allocs, total; };
inline Counters& c() { static Counters k = {0, 0, 0, 0}; return k; }
inline void* alloc(size_t n) {
    void* p = std::malloc(n ? n : 1);
    if (p) {
        size_t u = malloc_usable_size(p);
        Counters& k = c();
        k.live += u; k.total += u; ++k.allocs;
        if (k.live > k.peak) k.peak = k.live;
    }
    return p;
}
inline void dealloc(void* p) {
    if (!p) return;
    c().live -= malloc_usable_size(p);
    std::free(p);
}
// realloc is charged pessimistically: if the block moved, old and new are assumed to
// have existed at the same time.
inline void* resize(void* p, size_t n) {
    Counters& k = c();
    size_t old = malloc_usable_size(p);
    void* q = std::realloc(p, n);
    if (!q) return 0;
    size_t now = malloc_usable_size(q);
    if (q != p && k.live + now > k.peak) k.peak = k.live + now;
    k.live = k.live - old + now;
    if (now > old) k.total += now - old;
    ++k.allocs;
    if (k.live > k.peak) k.peak = k.live;
    return q;
}
// Start a measurement window: peak restarts from the current live size.
inline size_t open_window() { Counters& k = c(); k.peak = k.live; k.allocs = 0; k.total = 0; return k.live; }
}  // namespace mem

#ifdef CDES_DEFINE_NEW
void* operator new(size_t n) { void* p = mem::alloc(n); if (!p) throw std::bad_alloc(); return p; }
void* operator new[](size_t n) { void* p = mem::alloc(n); if (!p) throw std::bad_alloc(); return p; }
void* operator new(size_t n, const std::nothrow_t&) noexcept { return mem::alloc(n); }
void* operator new[](size_t n, const std::nothrow_t&) noexcept { return mem::alloc(n); }
void operator delete(void* p) noexcept { mem::dealloc(p); }
void operator delete[](void* p) noexcept { mem::dealloc(p); }
void operator delete(void* p, size_t) noexcept { mem::dealloc(p); }
void operator delete[](void* p, size_t) noexcept { mem::dealloc(p); }
#endif

// ---- traces ------------------------------------------------------------------
enum OpKind { OP_ENTER = 0, OP_EXIT = 1, OP_DECLARE = 2, OP_LOOKUP = 3, OP_UNIT = 4 };
struct Op { uint32_t kind; uint32_t name; };

struct Trace {
    std::vector<Op> ops;
    std::vector<std::string> names;   // distinct names; ops refer to them by index
    size_t count[5];
    size_t ignored;
};

// Accepts the compact compiler-trace format (U / E / X / D name / L name / G name) and
// the format of the earlier METIS repository (ENTER_SCOPE / EXIT_SCOPE / DECLARE / USE).
inline bool load_trace(const std::string& path, Trace& t) {
    std::ifstream in(path.c_str());
    if (!in) return false;
    std::unordered_map<std::string, uint32_t> ids;
    for (int i = 0; i < 5; ++i) t.count[i] = 0;
    t.ignored = 0;
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line[line.size() - 1] == '\r') line.erase(line.size() - 1);
        if (line.empty()) continue;
        size_t sp = line.find(' ');
        std::string tag = line.substr(0, sp), arg = sp == std::string::npos ? "" : line.substr(sp + 1);
        int kind;
        if (tag == "E" || tag == "ENTER_SCOPE") kind = OP_ENTER;
        else if (tag == "X" || tag == "EXIT_SCOPE") kind = OP_EXIT;
        else if (tag == "D" || tag == "DECLARE") kind = OP_DECLARE;
        else if (tag == "L" || tag == "USE" || tag == "LOOKUP") kind = OP_LOOKUP;
        else if (tag == "U") kind = OP_UNIT;
        else { ++t.ignored; continue; }
        Op op = {static_cast<uint32_t>(kind), 0};
        if (kind == OP_DECLARE || kind == OP_LOOKUP) {
            size_t e = arg.find(' ');
            if (e != std::string::npos) arg.erase(e);
            if (arg.empty() || arg.size() > 255) { ++t.ignored; continue; }
            std::unordered_map<std::string, uint32_t>::iterator it = ids.find(arg);
            if (it == ids.end()) {
                it = ids.insert(std::make_pair(arg, static_cast<uint32_t>(t.names.size()))).first;
                t.names.push_back(arg);
            }
            op.name = it->second;
        }
        if (kind == OP_UNIT && t.ops.empty()) continue;   // the first unit needs no reset
        t.ops.push_back(op);
        ++t.count[kind];
    }
    return !t.ops.empty();
}

// ---- time ----------------------------------------------------------------------
typedef std::chrono::steady_clock Clock;
inline double ns_since(Clock::time_point a) {
    return static_cast<double>(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - a).count());
}
inline uint64_t ticks() { unsigned aux; return __rdtscp(&aux); }
// Nanoseconds per TSC tick, measured against steady_clock over ~100 ms.
inline double calibrate_ns_per_tick() {
    Clock::time_point t0 = Clock::now();
    uint64_t c0 = ticks();
    while (ns_since(t0) < 1e8) {}
    return ns_since(t0) / static_cast<double>(ticks() - c0);
}
// Cost of one timed interval (two back-to-back counter reads), in ticks: median of 4001.
inline double calibrate_overhead_ticks() {
    std::vector<uint64_t> d;
    for (int i = 0; i < 4001; ++i) { uint64_t a = ticks(); uint64_t b = ticks(); d.push_back(b - a); }
    std::nth_element(d.begin(), d.begin() + 2000, d.end());
    return static_cast<double>(d[2000]);
}
inline double percentile(std::vector<uint32_t>& v, double p) {
    if (v.empty()) return 0.0;
    size_t k = static_cast<size_t>(p * static_cast<double>(v.size() - 1));
    std::nth_element(v.begin(), v.begin() + k, v.end());
    return static_cast<double>(v[k]);
}

#endif
