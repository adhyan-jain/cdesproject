// Bounded exhaustive check of strata::Table.
//
// Enumerates EVERY sequence of at most DEPTH operations over a small alphabet
//   enter, exit, declare(a), declare(b), declare(c), declare(d)
// for a set of configurations chosen so that every kind of refusal occurs (tiny fixed
// buffers, static index with a load limit, probe limits, all keys in one cluster, raw and
// packed names, keyed hash). After every operation of every sequence:
//   * the result equals the reference model's (a refused operation is not applied to it);
//   * every name resolves as in the model;
//   * a refused operation leaves the state digest unchanged;
//   * the structural invariants hold.
// This is exhaustive only up to the stated depth and alphabet ("small scope"); it is not a
// proof. Usage: exhaustive_small [depth, default 8]
#define STRATA_TEST_HOOKS
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "../include/strata/strata.hpp"
#include "reference_model.hpp"

using strata::Table;

struct Config {
    const char* label;
    size_t bytes;            // fixed buffer size
    bool pack, degenerate, keyed;
    uint32_t index_slots, max_probe;
};

static const char* kNames[4] = {"a", "bb", "x::y", "long_identifier_name_0"};
static unsigned long long g_sequences = 0, g_operations = 0, g_refusals = 0, g_failures = 0;
static unsigned long long g_by_status[8];

static Table* make(const Config& c, std::vector<uint32_t>& buf) {
    buf.assign(c.bytes / 4, 0xDEADBEEFu);
    strata::Options o;
    o.pack_names = c.pack;
    o.keyed = c.keyed;
    o.key[0] = 0x1234u;
    o.key[1] = 0x5678u;
    o.index_slots = c.index_slots;
    o.max_probe = c.max_probe;
    return new Table(&buf[0], c.bytes, o);
}

// Applies op to both; returns false on any disagreement.
static bool apply(Table& t, ReferenceModel& ref, int op, int step) {
    const uint64_t before = t.state_digest();
    ++g_operations;
    if (op == 0) {
        strata::Status s = t.enter_scope();
        if (s == strata::kOk) ref.enter();
        else { ++g_refusals; ++g_by_status[-s]; if (t.state_digest() != before) return false; }
    } else if (op == 1) {
        strata::Status s = t.exit_scope();
        if (ref.depth() == 0) { if (s != strata::kNoScope || t.state_digest() != before) return false; }
        else { if (s != strata::kOk) return false; ref.exit(); }
    } else {
        const std::string nm = kNames[op - 2];
        strata::Status s = t.declare(nm.data(), nm.size(), step, static_cast<uint8_t>(step));
        if (s == strata::kOk || s == strata::kRedeclared) {
            if (ref.declare(nm, step, static_cast<uint8_t>(step)) != static_cast<int>(s)) return false;
        } else {
            ++g_refusals; ++g_by_status[-s];
            if (t.state_digest() != before) return false;
        }
    }
    for (int i = 0; i < 4; ++i) {
        int32_t a = -1, b = -1;
        uint8_t ta = 0, tb = 0;
        const std::string nm = kNames[i];
        bool fa = t.resolve(nm.data(), nm.size(), &a, &ta), fb = ref.resolve(nm, &b, &tb);
        if (fa != fb || (fa && (a != b || ta != tb))) return false;
    }
    return t.size() == ref.live() && t.depth() == ref.depth() && t.stats().live_identifiers == ref.distinct() &&
           t.check_invariants();
}

static void enumerate(const Config& c, int depth) {
    std::vector<int> seq(static_cast<size_t>(depth), 0);
    std::vector<uint32_t> buf;
    // Every sequence of length `depth` is replayed from an empty table; its prefixes are
    // thereby checked as well, so shorter sequences need no separate pass.
    for (;;) {
        Table* t = make(c, buf);
        ReferenceModel ref;
        bool ok = t->valid();
        for (int i = 0; ok && i < depth; ++i) ok = apply(*t, ref, seq[static_cast<size_t>(i)], i + 1);
        while (ok && ref.depth() > 0) { ok = t->exit_scope() == strata::kOk; ref.exit(); }
        if (ok) ok = t->size() == ref.live() && t->check_invariants();
        delete t;
        ++g_sequences;
        if (!ok) {
            ++g_failures;
            std::printf("FAIL [%s] sequence:", c.label);
            for (int i = 0; i < depth; ++i) std::printf(" %d", seq[static_cast<size_t>(i)]);
            std::printf("\n");
            if (g_failures > 20) return;
        }
        int i = depth - 1;
        while (i >= 0 && ++seq[static_cast<size_t>(i)] == 6) seq[static_cast<size_t>(i--)] = 0;
        if (i < 0) break;
    }
}

int main(int argc, char** argv) {
    const int depth = argc > 1 ? std::atoi(argv[1]) : 8;
    const Config configs[] = {
        //  label                          bytes pack   degen  keyed  slots probe
        {"fixed 128 B, packed",            128, true,  false, false, 0,    0},
        {"fixed 128 B, raw names",         128, false, false, false, 0,    0},
        {"fixed 160 B, one cluster",       160, true,  true,  false, 0,    0},
        {"fixed 136 B, keyed hash",        136, true,  false, true,  0,    0},
        {"static 16 slots, 144 B",         144, true,  false, false, 16,   0},
        {"static 16, limit 1, one cluster", 256, true, true,  false, 16,   1},
        {"static 16, limit 2, one cluster", 256, true, true,  false, 16,   2},
        {"static 16, limit 2, keyed, 152 B", 152, true, false, true, 16,   2},
    };
    for (size_t i = 0; i < sizeof configs / sizeof configs[0]; ++i) {
        Table::degenerate_hash() = configs[i].degenerate;
        unsigned long long s0 = g_sequences, r0 = g_refusals;
        enumerate(configs[i], depth);
        std::printf("%-34s %llu sequences, %llu refused operations\n", configs[i].label, g_sequences - s0, g_refusals - r0);
    }
    Table::degenerate_hash() = false;
    std::printf("depth %d: %llu sequences, %llu operations, %llu refusals "
                "(no memory %llu, too deep %llu, probe limit %llu), %llu failures\n",
                depth, g_sequences, g_operations, g_refusals, g_by_status[1], g_by_status[5], g_by_status[6], g_failures);
    return g_failures ? 1 : 0;
}
