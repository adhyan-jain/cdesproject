// Trace-replay benchmark: every table on the same trace, four separate passes each.
//
//   bench --trace FILE --name LABEL [--reps N] [--warmup N] [--impls a,b,...]
//         [--summary FILE.csv] [--raw FILE.csv]
//
//   1. check    replay against the reference model; counts wrong results (not timed)
//   2. memory   replay inside a heap-accounting window: peak / final bytes, allocations
//   3. replay   N rounds; in each round every table replays the whole trace once, in an
//               order that rotates from round to round, so that slow drifts of the machine
//               hit all tables alike and the samples of a round can be compared as pairs
//   4. latency  one timer per operation (TSC), calibrated overhead subtracted (secondary)
//
// A "U" record ends a translation unit: the table is destroyed and a new one created.
#define CDES_DEFINE_NEW
#include <cstring>
#include <memory>
#include <sstream>

#include "../tests/reference_model.hpp"
#include "baselines/tables.hpp"

struct Expected {
    std::vector<int32_t> lookup;     // per LOOKUP op: resolved value or -1
    std::vector<uint8_t> declare;    // per DECLARE op: 0 new, 1 redeclared
    size_t peak_live, peak_distinct, max_depth, units;
};

static void reference_pass(const Trace& tr, Expected& ex) {
    std::unique_ptr<ReferenceModel> ref(new ReferenceModel());
    ex.peak_live = ex.peak_distinct = ex.max_depth = 0;
    ex.units = 1;
    int32_t seq = 0;
    for (size_t i = 0; i < tr.ops.size(); ++i) {
        const Op& op = tr.ops[i];
        switch (op.kind) {
        case OP_ENTER: ref->enter(); if (ref->depth() > ex.max_depth) ex.max_depth = ref->depth(); break;
        case OP_EXIT: ref->exit(); break;
        case OP_DECLARE:
            ex.declare.push_back(static_cast<uint8_t>(ref->declare(tr.names[op.name], seq++)));
            if (ref->live() > ex.peak_live) { ex.peak_live = ref->live(); ex.peak_distinct = ref->distinct(); }
            break;
        case OP_LOOKUP: { int32_t v = -1; if (!ref->resolve(tr.names[op.name], &v)) v = -1; ex.lookup.push_back(v); break; }
        default: ref.reset(new ReferenceModel()); seq = 0; ++ex.units; break;
        }
    }
}

struct Row {
    std::string impl;
    size_t wrong_lookups, wrong_declares, refused_declares;
    size_t peak_bytes, final_bytes, allocs, alloc_bytes, used_peak;
    std::vector<double> replay_ns;
    double lat[4][4];   // [lookup, declare, enter, exit] x [mean, p50, p95, p99], ns
};

template <class T>
static void run_impl(const Trace& tr, const Expected& ex, int reps, int warmup, double ns_per_tick,
                     double overhead_ticks, Row& row) {
    row.impl = T::id();
    const bool reports = std::strncmp(T::id(), "metis", 5) != 0;
    // 1. check
    {
        std::unique_ptr<T> t(new T());
        size_t li = 0, di = 0;
        int32_t seq = 0;
        row.wrong_lookups = row.wrong_declares = row.refused_declares = 0;
        for (size_t i = 0; i < tr.ops.size(); ++i) {
            const Op& op = tr.ops[i];
            switch (op.kind) {
            case OP_ENTER: t->enter(); break;
            case OP_EXIT: t->exit(); break;
            case OP_DECLARE: {
                int r = t->declare(tr.names[op.name], seq++);
                if (r < 0) ++row.refused_declares;
                else if (reports && r != ex.declare[di]) ++row.wrong_declares;
                ++di;
                break;
            }
            case OP_LOOKUP: {
                int32_t v = -1;
                if (!t->resolve(tr.names[op.name], &v)) v = -1;
                if (v != ex.lookup[li++]) ++row.wrong_lookups;
                break;
            }
            default: t.reset(); t.reset(new T()); seq = 0; break;
            }
        }
    }
    // 2. memory
    {
        row.used_peak = 0;
        size_t base = mem::open_window();
        std::unique_ptr<T> t(new T());
        int32_t seq = 0, sink = 0;
        for (size_t i = 0; i < tr.ops.size(); ++i) {
            const Op& op = tr.ops[i];
            switch (op.kind) {
            case OP_ENTER: t->enter(); break;
            case OP_EXIT: t->exit(); break;
            case OP_DECLARE: t->declare(tr.names[op.name], seq++); break;
            case OP_LOOKUP: t->resolve(tr.names[op.name], &sink); break;
            default: row.used_peak = std::max(row.used_peak, t->used_peak()); t.reset(); t.reset(new T()); seq = 0; break;
            }
        }
        row.used_peak = std::max(row.used_peak, t->used_peak());
        row.peak_bytes = mem::c().peak - base;
        row.final_bytes = mem::c().live - base;
        row.allocs = mem::c().allocs;
        row.alloc_bytes = mem::c().total;
    }
    // 3. whole-trace replay time: measured in main(), interleaved across tables
    volatile int32_t guard = 0;
    (void)reps; (void)warmup;
    // 4. per-operation latency (three replays; the median of each statistic is kept)
    double acc[4][4][3];
    for (int rep = 0; rep < 3; ++rep) {
        std::vector<uint32_t> s[4];
        for (int k = 0; k < 4; ++k) s[k].reserve(tr.count[k == 0 ? OP_LOOKUP : k == 1 ? OP_DECLARE : k == 2 ? OP_ENTER : OP_EXIT]);
        std::unique_ptr<T> t(new T());
        int32_t seq = 0, sink = 0;
        for (size_t i = 0; i < tr.ops.size(); ++i) {
            const Op& op = tr.ops[i];
            uint64_t a, b;
            switch (op.kind) {
            case OP_ENTER: a = ticks(); t->enter(); b = ticks(); s[2].push_back(static_cast<uint32_t>(b - a)); break;
            case OP_EXIT: a = ticks(); t->exit(); b = ticks(); s[3].push_back(static_cast<uint32_t>(b - a)); break;
            case OP_DECLARE: a = ticks(); sink += t->declare(tr.names[op.name], seq++); b = ticks(); s[1].push_back(static_cast<uint32_t>(b - a)); break;
            case OP_LOOKUP: { int32_t v = 0; a = ticks(); sink += t->resolve(tr.names[op.name], &v); b = ticks(); s[0].push_back(static_cast<uint32_t>(b - a)); break; }
            default: t.reset(); t.reset(new T()); seq = 0; break;
            }
        }
        guard = guard + sink;
        for (int k = 0; k < 4; ++k) {
            double sum = 0;
            for (size_t i = 0; i < s[k].size(); ++i) sum += s[k][i];
            double st[4] = {s[k].empty() ? 0 : sum / static_cast<double>(s[k].size()), percentile(s[k], 0.50),
                            percentile(s[k], 0.95), percentile(s[k], 0.99)};
            for (int q = 0; q < 4; ++q) {
                double v = (st[q] - overhead_ticks) * ns_per_tick;
                acc[k][q][rep] = s[k].empty() ? 0 : (v < 0 ? 0 : v);
            }
        }
    }
    for (int k = 0; k < 4; ++k)
        for (int q = 0; q < 4; ++q) { std::sort(acc[k][q], acc[k][q] + 3); row.lat[k][q] = acc[k][q][1]; }
}

// One timed replay of the whole trace on a fresh table (construction and destruction included).
template <class T>
static double replay_once(const Trace& tr) {
    static volatile int32_t guard = 0;
    Clock::time_point t0 = Clock::now();
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
    return ns_since(t0);
}

static bool want(const std::string& list, const char* id) {
    if (list.empty()) return true;
    std::stringstream ss(list);
    std::string item;
    while (std::getline(ss, item, ',')) if (item == id) return true;
    return false;
}

int main(int argc, char** argv) {
    std::string path, name, impls, summary, raw;
    int reps = 15, warmup = 2;
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string a = argv[i], v = argv[i + 1];
        if (a == "--trace") path = v; else if (a == "--name") name = v; else if (a == "--impls") impls = v;
        else if (a == "--reps") reps = std::atoi(v.c_str()); else if (a == "--warmup") warmup = std::atoi(v.c_str());
        else if (a == "--summary") summary = v; else if (a == "--raw") raw = v;
        else { std::fprintf(stderr, "unknown option %s\n", a.c_str()); return 2; }
    }
    Trace tr;
    if (path.empty() || !load_trace(path, tr)) { std::fprintf(stderr, "cannot load trace '%s'\n", path.c_str()); return 2; }
    if (name.empty()) name = path;
    Expected ex;
    reference_pass(tr, ex);
    double ns_per_tick = calibrate_ns_per_tick(), overhead = calibrate_overhead_ticks();

    std::vector<Row> rows;
    std::vector<double (*)(const Trace&)> timers;
#define RUN(T) if (want(impls, tables::T::id())) { rows.push_back(Row()); timers.push_back(&replay_once<tables::T>); \
        run_impl<tables::T>(tr, ex, reps, warmup, ns_per_tick, overhead, rows.back()); }
    RUN(Strata)
    RUN(StrataRaw)
    RUN(StrataNoShrink)
    RUN(StrataSparse)
    RUN(ArenaChain)
    RUN(ScopeMapStack)
    RUN(StdUndoLog)
#ifdef CDES_HAVE_PHMAP
    RUN(SwissUndoLog)
    RUN(SwissInterned)
#endif
#ifdef CDES_HAVE_METIS
    RUN(MetisX)
    RUN(MetisArenaLP)
    RUN(MetisScopeMaps)
#endif

    // Interleaved rounds: every table once per round, starting one position later each round.
    for (int round = -warmup; round < reps; ++round) {
        size_t n = timers.size(), first = static_cast<size_t>(round + warmup) % (n ? n : 1);
        for (size_t k = 0; k < n; ++k) {
            size_t i = (first + k) % n;
            double ns = timers[i](tr);
            if (round >= 0) rows[i].replay_ns.push_back(ns);
        }
    }

    FILE* fs = summary.empty() ? stdout : std::fopen(summary.c_str(), "a");
    FILE* fr = raw.empty() ? 0 : std::fopen(raw.c_str(), "a");
    if (!fs) return 3;
    if (summary.empty() || std::ftell(fs) == 0)
        std::fprintf(fs, "trace,impl,ops,declares,lookups,enters,exits,units,distinct_names,peak_live_decls,peak_live_distinct,max_depth,"
                         "wrong_lookups,wrong_declares,refused_declares,peak_bytes,final_bytes,allocs,alloc_bytes,table_used_peak_bytes,"
                         "replay_ns_median,replay_ns_min,replay_ns_max,reps,"
                         "lookup_mean_ns,lookup_p50_ns,lookup_p95_ns,lookup_p99_ns,declare_mean_ns,declare_p50_ns,declare_p95_ns,declare_p99_ns,"
                         "enter_mean_ns,enter_p50_ns,enter_p95_ns,enter_p99_ns,exit_mean_ns,exit_p50_ns,exit_p95_ns,exit_p99_ns,"
                         "timer_overhead_ns\n");
    if (fr && std::ftell(fr) == 0) std::fprintf(fr, "trace,impl,rep,replay_ns\n");
    for (size_t r = 0; r < rows.size(); ++r) {
        Row& w = rows[r];
        std::vector<double> t = w.replay_ns;
        std::sort(t.begin(), t.end());
        double med = t.empty() ? 0 : (t.size() % 2 ? t[t.size() / 2] : (t[t.size() / 2 - 1] + t[t.size() / 2]) / 2);
        std::fprintf(fs, "%s,%s,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%.0f,%.0f,%.0f,%d",
                     name.c_str(), w.impl.c_str(), tr.ops.size(), tr.count[OP_DECLARE], tr.count[OP_LOOKUP], tr.count[OP_ENTER],
                     tr.count[OP_EXIT], ex.units, tr.names.size(), ex.peak_live, ex.peak_distinct, ex.max_depth,
                     w.wrong_lookups, w.wrong_declares, w.refused_declares, w.peak_bytes, w.final_bytes, w.allocs, w.alloc_bytes, w.used_peak,
                     med, t.empty() ? 0 : t.front(), t.empty() ? 0 : t.back(), reps);
        for (int k = 0; k < 4; ++k) for (int q = 0; q < 4; ++q) std::fprintf(fs, ",%.1f", w.lat[k][q]);
        std::fprintf(fs, ",%.1f\n", overhead * ns_per_tick);
        if (fr) for (size_t i = 0; i < w.replay_ns.size(); ++i) std::fprintf(fr, "%s,%s,%zu,%.0f\n", name.c_str(), w.impl.c_str(), i, w.replay_ns[i]);
    }
    if (fs != stdout) std::fclose(fs);
    if (fr) std::fclose(fr);
    return 0;
}
