// Deterministic cost of replaying a trace: user-space instructions and branch misses
// from the CPU's performance counters, one replay per measurement, repeated to show
// that the count does not move. Counts do not depend on clock frequency or load.
//   instr_count --trace FILE --name LABEL [--reps N]    (CSV on stdout)
#define CDES_DEFINE_NEW
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <memory>
#include "baselines/tables.hpp"

static int open_counter(uint32_t type, uint64_t config) {
    perf_event_attr a;
    std::memset(&a, 0, sizeof a);
    a.type = type; a.size = sizeof a; a.config = config;
    a.disabled = 1; a.exclude_kernel = 1; a.exclude_hv = 1;
    return static_cast<int>(syscall(__NR_perf_event_open, &a, 0, -1, -1, 0));
}

template <class T>
static void measure(const Trace& tr, const char* name, const char* impl, int reps, int fi, int fb) {
    for (int r = 0; r < reps + 1; ++r) {
        static volatile int32_t guard = 0;
        ioctl(fi, PERF_EVENT_IOC_RESET, 0); ioctl(fb, PERF_EVENT_IOC_RESET, 0);
        ioctl(fi, PERF_EVENT_IOC_ENABLE, 0); ioctl(fb, PERF_EVENT_IOC_ENABLE, 0);
        {
            std::unique_ptr<T> t(new T());
            int32_t seq = 0, sink = 0;
            for (size_t i = 0; i < tr.ops.size(); ++i) {
                const Op& op = tr.ops[i];
                switch (op.kind) {
                case OP_ENTER: t->enter(); break;
                case OP_EXIT: t->exit(); break;
                case OP_DECLARE: sink += t->declare(tr.names[op.name], seq++); break;
                case OP_LOOKUP: { int32_t v = 0; sink += t->resolve(tr.names[op.name], &v) ? v : 0; break; }
                default: t.reset(); t.reset(new T()); seq = 0; break;
                }
            }
            guard = guard + sink;
        }
        ioctl(fi, PERF_EVENT_IOC_DISABLE, 0); ioctl(fb, PERF_EVENT_IOC_DISABLE, 0);
        uint64_t ins = 0, brm = 0;
        if (read(fi, &ins, sizeof ins) != sizeof ins || read(fb, &brm, sizeof brm) != sizeof brm) return;
        if (r > 0) std::printf("%s,%s,%d,%llu,%llu\n", name, impl, r, (unsigned long long)ins, (unsigned long long)brm);
    }
}

int main(int argc, char** argv) {
    std::string path, name; int reps = 5;
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string a = argv[i], v = argv[i + 1];
        if (a == "--trace") path = v; else if (a == "--name") name = v; else if (a == "--reps") reps = std::atoi(v.c_str());
    }
    Trace tr;
    if (path.empty() || !load_trace(path, tr)) { std::fprintf(stderr, "cannot load trace\n"); return 2; }
    int fi = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS);
    int fb = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES);
    if (fi < 0 || fb < 0) { std::fprintf(stderr, "performance counters unavailable\n"); return 3; }
    measure<tables::Strata>(tr, name.c_str(), "strata", reps, fi, fb);
    measure<tables::ArenaChain>(tr, name.c_str(), "c0_stored_hash", reps, fi, fb);
    measure<tables::ArenaChainNoHash>(tr, name.c_str(), "c1_no_hash", reps, fi, fb);
    measure<tables::StrataKeyed>(tr, name.c_str(), "strata_keyed", reps, fi, fb);
    return 0;
}
