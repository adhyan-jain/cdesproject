// Fixed-memory experiments for STRATA.
//
//   budget --mode budget --trace FILE --name LABEL --out FILE.csv [--reps N]
//       Smallest caller-provided buffer (64-byte resolution) with which the whole trace
//       replays without a single refused operation, for packed and raw names, and the
//       replay time with 1x, 1.25x, 2x and 4x that buffer.
//
//   budget --mode units --trace FILE --name LABEL --out FILE.csv
//       The same bisection for every translation unit separately, for STRATA (packed)
//       and for the conventional arena table: how much buffer each unit needs.
//
//   budget --mode minbuf --trace FILE --name LABEL --out FILE.csv
//       Only the minimum buffers of the whole trace for both tables (no timing).
//
//   budget --mode worstcase --out FILE.csv
//       Lookup cost when every key is forced into one probe cluster, against the normal
//       hash, for growing table sizes. Shows the unprotected worst case honestly.
#define CDES_DEFINE_NEW
#define STRATA_TEST_HOOKS
#include <cstring>

#include "../include/strata/strata.hpp"
#include "baselines/arena_chain.hpp"
#include "common.hpp"

struct Outcome { bool ok; size_t refused, peak_used; double ns; };

// Replays the trace on a table living in `buf`; a new table per translation unit.
static size_t g_begin = 0, g_end = static_cast<size_t>(-1);   // operation range to replay (one unit, or everything)

static Outcome replay_fixed(const Trace& tr, uint32_t* buf, size_t bytes, int variant, bool timed) {
    const bool pack = variant != 0, sparse = variant == 2;   // 0 raw, 1 packed, 2 packed + sparse index
    Outcome o = {true, 0, 0, 0};
    alignas(strata::Table) unsigned char room[sizeof(strata::Table)];
    strata::Table* t = new (room) strata::Table(buf, bytes, pack, sparse);
    int32_t seq = 0, sink = 0;
    Clock::time_point t0 = Clock::now();
    for (size_t i = g_begin; i < tr.ops.size() && i < g_end; ++i) {
        const Op& op = tr.ops[i];
        const std::string& nm = tr.names[op.name];
        switch (op.kind) {
        case OP_ENTER: if (t->enter_scope() != strata::kOk) ++o.refused; break;
        case OP_EXIT: t->exit_scope(); break;
        case OP_DECLARE: if (t->declare(nm.data(), nm.size(), seq++) < 0) ++o.refused; break;
        case OP_LOOKUP: { int32_t v = 0; sink += t->resolve(nm.data(), nm.size(), &v) ? v : 0; break; }
        default:
            if (!timed && t->stats().peak_used_bytes > o.peak_used) o.peak_used = t->stats().peak_used_bytes;
            t->~Table();
            t = new (room) strata::Table(buf, bytes, pack, sparse);
            seq = 0;
            break;
        }
        if (o.refused && !timed) break;
    }
    o.ns = ns_since(t0);
    if (t->stats().peak_used_bytes > o.peak_used) o.peak_used = t->stats().peak_used_bytes;
    t->~Table();
    o.ok = o.refused == 0;
    volatile int32_t g = sink;
    (void)g;
    return o;
}

// The same replay for the conventional allocator-free baseline.
static Outcome replay_arena(const Trace& tr, uint32_t* buf, size_t bytes, bool timed) {
    Outcome o = {true, 0, 0, 0};
    alignas(arena_chain::Table) unsigned char room[sizeof(arena_chain::Table)];
    arena_chain::Table* t = new (room) arena_chain::Table(buf, bytes);
    int32_t seq = 0, sink = 0;
    Clock::time_point t0 = Clock::now();
    for (size_t i = g_begin; i < tr.ops.size() && i < g_end; ++i) {
        const Op& op = tr.ops[i];
        const std::string& nm = tr.names[op.name];
        switch (op.kind) {
        case OP_ENTER: if (!t->enter_scope()) ++o.refused; break;
        case OP_EXIT: t->exit_scope(); break;
        case OP_DECLARE: if (t->declare(nm.data(), nm.size(), seq++) < 0) ++o.refused; break;
        case OP_LOOKUP: { int32_t v = 0; sink += t->resolve(nm.data(), nm.size(), &v) ? v : 0; break; }
        default:
            if (!timed && t->peak_used_bytes() > o.peak_used) o.peak_used = t->peak_used_bytes();
            t->~Table();
            t = new (room) arena_chain::Table(buf, bytes);
            seq = 0;
            break;
        }
        if (o.refused && !timed) break;
    }
    o.ns = ns_since(t0);
    if (t->peak_used_bytes() > o.peak_used) o.peak_used = t->peak_used_bytes();
    t->~Table();
    o.ok = o.refused == 0;
    volatile int32_t g = sink;
    (void)g;
    return o;
}
static Outcome replay_any(const Trace& tr, uint32_t* buf, size_t bytes, int variant, bool timed) {
    return variant == 3 ? replay_arena(tr, buf, bytes, timed) : replay_fixed(tr, buf, bytes, variant, timed);
}

static int mode_budget(const std::string& path, const std::string& name, const std::string& out, int reps) {
    Trace tr;
    if (!load_trace(path, tr)) { std::fprintf(stderr, "cannot load %s\n", path.c_str()); return 2; }
    const size_t kMax = 64u << 20;
    std::vector<uint32_t> buf(kMax / 4);
    FILE* f = std::fopen(out.c_str(), "a");
    if (!f) return 3;
    if (std::ftell(f) == 0) std::fprintf(f, "trace,names,min_buffer_bytes,peak_used_bytes_at_min,budget_factor,buffer_bytes,replay_ns_median,replay_ns_min,replay_ns_max,reps\n");
    static const char* kVariant[] = {"raw", "packed", "packed_sparse", "arena_chain"};
    for (int pack = 3; pack >= 0; --pack) {
        size_t lo = 128, hi = kMax;                       // lo fails (or is too small), hi must pass
        if (!replay_any(tr, buf.data(), hi, pack, false).ok) { std::fprintf(stderr, "does not fit in 64 MiB\n"); return 4; }
        while (hi - lo > 64) {
            size_t mid = ((lo + hi) / 2) & ~static_cast<size_t>(63);
            if (mid <= lo) mid = lo + 64;
            if (replay_any(tr, buf.data(), mid, pack, false).ok) hi = mid; else lo = mid;
        }
        size_t used = replay_any(tr, buf.data(), hi, pack, false).peak_used;
        const double factors[] = {1.0, 1.25, 2.0, 4.0};
        for (int k = 0; k < 4; ++k) {
            size_t bytes = (static_cast<size_t>(static_cast<double>(hi) * factors[k]) + 63) & ~static_cast<size_t>(63);
            if (!replay_any(tr, buf.data(), bytes, pack, false).ok) {   // sizing is not perfectly monotonic: say so
                std::fprintf(f, "%s,%s,%zu,%zu,%.2f,%zu,REFUSED,,,%d\n", name.c_str(), kVariant[pack], hi, used, factors[k], bytes, reps);
                continue;
            }
            std::vector<double> ns;
            for (int r = -2; r < reps; ++r) { double v = replay_any(tr, buf.data(), bytes, pack, true).ns; if (r >= 0) ns.push_back(v); }
            std::sort(ns.begin(), ns.end());
            std::fprintf(f, "%s,%s,%zu,%zu,%.2f,%zu,%.0f,%.0f,%.0f,%d\n", name.c_str(), kVariant[pack], hi, used,
                         factors[k], bytes, ns[ns.size() / 2], ns.front(), ns.back(), reps);
        }
    }
    std::fclose(f);
    return 0;
}

// Smallest buffer (64-byte resolution) for the current operation range.
static size_t min_buffer(const Trace& tr, uint32_t* buf, size_t max_bytes, int variant) {
    size_t lo = 64, hi = max_bytes;
    if (!replay_any(tr, buf, hi, variant, false).ok) return 0;
    while (hi - lo > 64) {
        size_t mid = ((lo + hi) / 2) & ~static_cast<size_t>(63);
        if (mid <= lo) mid = lo + 64;
        if (replay_any(tr, buf, mid, variant, false).ok) hi = mid; else lo = mid;
    }
    return hi;
}

static int mode_units(const std::string& path, const std::string& name, const std::string& out, bool whole) {
    Trace tr;
    if (!load_trace(path, tr)) { std::fprintf(stderr, "cannot load %s\n", path.c_str()); return 2; }
    const size_t kMax = 32u << 20;
    std::vector<uint32_t> buf(kMax / 4);
    FILE* f = std::fopen(out.c_str(), "a");
    if (!f) return 3;
    if (std::ftell(f) == 0) std::fprintf(f, "trace,unit,operations,declares,strata_min_bytes,arena_chain_min_bytes\n");
    std::vector<size_t> starts(1, 0);
    if (!whole) for (size_t i = 0; i < tr.ops.size(); ++i) if (tr.ops[i].kind == OP_UNIT) starts.push_back(i + 1);
    starts.push_back(tr.ops.size() + 1);
    for (size_t u = 0; u + 1 < starts.size(); ++u) {
        g_begin = starts[u];
        g_end = whole ? tr.ops.size() : starts[u + 1] - 1;
        size_t decl = 0;
        for (size_t i = g_begin; i < g_end && i < tr.ops.size(); ++i) decl += tr.ops[i].kind == OP_DECLARE;
        size_t a = min_buffer(tr, buf.data(), kMax, 1), b = min_buffer(tr, buf.data(), kMax, 3);
        std::fprintf(f, "%s,%zu,%zu,%zu,%zu,%zu\n", name.c_str(), u, (g_end < tr.ops.size() ? g_end : tr.ops.size()) - g_begin, decl, a, b);
    }
    g_begin = 0;
    g_end = static_cast<size_t>(-1);
    std::fclose(f);
    return 0;
}

static int mode_worstcase(const std::string& out) {
    FILE* f = std::fopen(out.c_str(), "a");
    if (!f) return 3;
    if (std::ftell(f) == 0) std::fprintf(f, "live_names,hash,ns_per_lookup_hit,ns_per_lookup_miss,ns_per_declare\n");
    for (int n = 16; n <= 4096; n *= 4) {
        std::vector<std::string> names, missing;
        char b[32];
        for (int i = 0; i < n; ++i) { std::snprintf(b, sizeof b, "sym_%d", i); names.push_back(b); std::snprintf(b, sizeof b, "nope_%d", i); missing.push_back(b); }
        for (int degenerate = 0; degenerate <= 1; ++degenerate) {
            strata::Table::degenerate_hash() = degenerate != 0;
            double best[3] = {1e30, 1e30, 1e30};
            for (int round = 0; round < 7; ++round) {
                strata::Table t;
                Clock::time_point t0 = Clock::now();
                for (int i = 0; i < n; ++i) t.declare(names[i].data(), names[i].size(), i);
                double d = ns_since(t0) / n;
                int reps = 2000000 / n / (degenerate ? n / 16 + 1 : 1) + 1;
                int32_t sink = 0, v = 0;
                t0 = Clock::now();
                for (int r = 0; r < reps; ++r) for (int i = 0; i < n; ++i) sink += t.resolve(names[i].data(), names[i].size(), &v);
                double h = ns_since(t0) / (static_cast<double>(reps) * n);
                t0 = Clock::now();
                for (int r = 0; r < reps; ++r) for (int i = 0; i < n; ++i) sink += t.resolve(missing[i].data(), missing[i].size(), &v);
                double m = ns_since(t0) / (static_cast<double>(reps) * n);
                volatile int32_t g = sink; (void)g;
                if (h < best[0]) best[0] = h;
                if (m < best[1]) best[1] = m;
                if (d < best[2]) best[2] = d;
            }
            std::fprintf(f, "%d,%s,%.1f,%.1f,%.1f\n", n, degenerate ? "all_keys_one_cluster" : "normal", best[0], best[1], best[2]);
        }
    }
    strata::Table::degenerate_hash() = false;
    std::fclose(f);
    return 0;
}

int main(int argc, char** argv) {
    std::string mode, path, name, out;
    int reps = 9;
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string a = argv[i], v = argv[i + 1];
        if (a == "--mode") mode = v; else if (a == "--trace") path = v; else if (a == "--name") name = v;
        else if (a == "--out") out = v; else if (a == "--reps") reps = std::atoi(v.c_str());
        else { std::fprintf(stderr, "unknown option %s\n", a.c_str()); return 2; }
    }
    if (out.empty()) { std::fprintf(stderr, "--out is required\n"); return 2; }
    if (reps < 1) reps = 1;   // the median of zero timed replays does not exist
    if (mode == "budget") return mode_budget(path, name.empty() ? path : name, out, reps);
    if (mode == "worstcase") return mode_worstcase(out);
    if (mode == "units") return mode_units(path, name.empty() ? path : name, out, false);
    if (mode == "minbuf") return mode_units(path, name.empty() ? path : name, out, true);
    std::fprintf(stderr, "--mode budget|units|minbuf|worstcase\n");
    return 2;
}
