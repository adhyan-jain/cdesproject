// Reviewer experiments R14/R15: (a) sizes of the control structures that live OUTSIDE the
// caller's buffer, (b) cost of an empty timed interval for the timers the benchmarks use.
//   review_aux sizes | timer
#include <time.h>
#include <cstdio>
#include <cstring>
#include "../include/strata/strata.hpp"
#include "baselines/arena_chain.hpp"
#include "baselines/arena_chain_nohash.hpp"
#include "common.hpp"

static double med(std::vector<double>& v) { std::sort(v.begin(), v.end()); return v[v.size() / 2]; }
static void sorted(std::vector<double>& v) { std::sort(v.begin(), v.end()); }

int main(int argc, char** argv) {
    std::string m = argc > 1 ? argv[1] : "";
    if (m == "sizes") {
        std::printf("sizeof(strata::Table)            = %zu bytes (control struct, outside the buffer)\n", sizeof(strata::Table));
        std::printf("sizeof(strata::Key)              = %zu bytes (stack, one per operation)\n", sizeof(strata::Key));
        std::printf("sizeof(arena_chain::Table)       = %zu bytes (control struct, outside the buffer)\n", sizeof(arena_chain::Table));
        std::printf("sizeof(arena_chain_nohash::Table)= %zu bytes (control struct, outside the buffer)\n", sizeof(arena_chain_nohash::Table));
        std::printf("arena tables: uint32_t key[64] on the stack per declare/resolve = 256 bytes\n");
        return 0;
    }
    if (m == "timer") {
        // Empty interval = two back-to-back reads. steady_clock is libstdc++'s clock_gettime(CLOCK_MONOTONIC).
        const int N = 200001;
        std::vector<double> a, b, c;
        for (int i = 0; i < N; ++i) { Clock::time_point t0 = Clock::now(); Clock::time_point t1 = Clock::now();
            a.push_back(static_cast<double>(std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count())); }
        for (int i = 0; i < N; ++i) { timespec x, y; clock_gettime(CLOCK_MONOTONIC, &x); clock_gettime(CLOCK_MONOTONIC, &y);
            b.push_back((y.tv_sec - x.tv_sec) * 1e9 + (y.tv_nsec - x.tv_nsec)); }
        double nspt = calibrate_ns_per_tick();
        for (int i = 0; i < N; ++i) { uint64_t x = ticks(), y = ticks(); c.push_back(static_cast<double>(y - x) * nspt); }
        sorted(a); sorted(b); sorted(c);
        timespec res; clock_getres(CLOCK_MONOTONIC, &res);
        std::printf("clock_getres(CLOCK_MONOTONIC) = %ld ns\n", res.tv_nsec);
        std::printf("empty interval, std::chrono::steady_clock (the replay timer): median %.1f ns, min %.1f, p99 %.1f\n", med(a), a.front(), a[static_cast<size_t>(0.99 * N)]);
        std::printf("empty interval, raw clock_gettime(CLOCK_MONOTONIC):           median %.1f ns, min %.1f, p99 %.1f\n", med(b), b.front(), b[static_cast<size_t>(0.99 * N)]);
        std::printf("empty interval, rdtscp (the per-operation latency timer):     median %.1f ns, min %.1f, p99 %.1f (%.4f ns/tick)\n", med(c), c.front(), c[static_cast<size_t>(0.99 * N)], nspt);
        return 0;
    }
    std::fprintf(stderr, "usage: review_aux sizes|timer\n");
    return 2;
}
