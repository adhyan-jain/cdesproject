// Differential fuzzer for strata::Table (libFuzzer entry point).
//
//   clang++ -std=c++14 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all
//           -o build/fuzz_strata tests/fuzz_strata.cpp      (one command line; see scripts/audit/fuzz.sh)
//   ./build/fuzz_strata -max_len=4096 -max_total_time=300 build/fuzz_corpus
//
// The input bytes choose a configuration (fixed or growable buffer, its size, name
// packing, index density, all keys in one cluster, an allocator that fails, the keyed
// hash, a static index with or without a probe limit) and then a sequence of operations. After every operation the table must agree with the reference
// model; after every refused operation its complete state must be unchanged; the
// structural invariants are re-checked throughout. Any disagreement aborts.
//
// With -DFUZZ_STANDALONE the same code is built as a normal program that replays the
// files given on the command line (used to keep crash inputs as regression tests where
// libFuzzer is not available).
#define STRATA_TEST_HOOKS
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "../include/strata/strata.hpp"
#include "reference_model.hpp"

namespace {

struct Input {
    const uint8_t* p;
    size_t n, i;
    bool done() const { return i >= n; }
    uint8_t byte() { return i < n ? p[i++] : 0; }
    uint32_t u16() { uint32_t a = byte(); return a | static_cast<uint32_t>(byte()) << 8; }
};

[[noreturn]] void fail(const char* what, size_t op) {
    std::fprintf(stderr, "FUZZ FAILURE: %s (operation %zu)\n", what, op);
    std::abort();
}

struct FailingAllocator {
    long remaining;   // allocations that still succeed; negative = never fails
    long live;
};
void* fa_alloc(size_t n, void* u) {
    FailingAllocator* f = static_cast<FailingAllocator*>(u);
    if (f->remaining == 0) return 0;
    if (f->remaining > 0) --f->remaining;
    void* p = std::malloc(n);
    if (p) ++f->live;
    return p;
}
void fa_free(void* p, void* u) {
    if (p) --static_cast<FailingAllocator*>(u)->live;
    std::free(p);
}

// A pool of names that collide, shadow and exercise both encodings.
std::string pool_name(uint32_t k) {
    static const char* stems[] = {"i", "n", "tmp", "count", "xTicksToWait", "mbedtls_ssl_context_struct",
                                  "a_really_long_identifier_name_used_for_testing_names_over_sixty_bytes_long"};
    char b[16];
    std::snprintf(b, sizeof b, "%u", k / 14);
    switch (k % 14) {
    case 7: return std::string("ns::") + b;                 // raw path
    case 8: return std::string(b) + std::string(1, '\0');   // raw, embedded NUL
    case 9: return std::string(1 + k % 5, 'a');             // exact multiples of the packing width
    case 10: return std::string(5 * (1 + k % 3), 'z');
    case 11: return std::string("x") + std::string(k % 4, '\0');   // raw names that differ only in trailing NULs
    case 12: return std::string(250 + k % 6, 'q');          // at the length limit
    case 13: return std::string("\xff\xfe") + b;
    default: return std::string(stems[k % 14]) + "_" + b;
    }
}

void run(const uint8_t* data, size_t size) {
    Input in = {data, size, 0};
    const uint8_t cfg = in.byte();
    const bool pack = cfg & 1, sparse = cfg & 2, degenerate = cfg & 4;
    const unsigned mode = (cfg >> 3) & 3;   // 0 fixed, 1 growable, 2 growable with budget, 3 growable with failing allocator
    const uint32_t size_sel = in.u16();
    const uint8_t cfg2 = in.byte();
    const bool keyed = cfg2 & 1, bounded = mode == 0 && (cfg2 & 2);
    const uint32_t probe_sel = cfg2 >> 5;

    strata::Table::degenerate_hash() = degenerate;
    std::vector<uint32_t> buffer;
    FailingAllocator fa = {-1, 0};
    strata::Options o;
    o.pack_names = pack;
    o.sparse_index = sparse;
    o.shrink = (cfg & 0x20) != 0;
    o.keyed = keyed;
    o.key[0] = 0x9E3779B9u * (cfg2 + 1u);
    o.key[1] = size_sel * 0x85EBCA6Bu;
    if (bounded) {
        o.index_slots = 16u << ((cfg2 >> 2) & 7);                 // 16 .. 2048 slots
        o.max_probe = probe_sel ? 1u << (probe_sel - 1) : 0;      // 0 (none), 1 .. 64
    } else if (mode == 0 && probe_sel == 7) {
        o.max_probe = 5;                                          // limit without a static index: must be rejected
    }
    strata::Table* t;
    if (mode == 0) {
        buffer.resize(size_sel & 0x0FFF);
        if (keyed || bounded || o.max_probe) t = new strata::Table(buffer.empty() ? 0 : &buffer[0], buffer.size() * 4, o);
        else t = new strata::Table(buffer.empty() ? 0 : &buffer[0], buffer.size() * 4, pack, sparse);
        if (o.max_probe && !o.index_slots && t->valid()) fail("probe limit accepted without a static index", 0);
    } else {
        o.initial_bytes = 64 + (size_sel & 0x3FF) * 4;
        if (mode == 2) o.max_bytes = 256 + (size_sel >> 4) * 4;
        if (mode == 3) {
            fa.remaining = 1 + (size_sel >> 12);
            o.alloc = fa_alloc;
            o.free = fa_free;
            o.user = &fa;
        }
        t = new strata::Table(o);
    }
    ReferenceModel ref;
    std::vector<std::string> seen;
    size_t op = 0;

    if (!t->valid()) {
        // A table without a usable buffer refuses everything and never crashes.
        if (t->enter_scope() != strata::kNoMemory || t->declare("a", 1, 1) != strata::kNoMemory ||
            t->exit_scope() != strata::kNoMemory || t->resolve("a", 1) || t->check_invariants())
            fail("invalid table accepted an operation", 0);
        delete t;
        strata::Table::degenerate_hash() = false;
        if (fa.live != 0) fail("leak from an invalid table", 0);
        return;
    }

    while (!in.done() && op < 4096) {
        ++op;
        const uint8_t code = in.byte();
        const unsigned kind = code & 7;
        if (kind == 0) {
            const uint64_t before = t->state_digest();
            const strata::Status s = t->enter_scope();
            if (s == strata::kOk) ref.enter();
            else if (s != strata::kNoMemory && s != strata::kTooDeep) fail("enter_scope: unexpected status", op);
            else if (t->state_digest() != before) fail("refused enter_scope changed the table", op);
        } else if (kind == 1) {
            const bool expect = ref.depth() > 0;
            const uint64_t before = t->state_digest();
            const strata::Status s = t->exit_scope();
            if (expect) {
                if (s != strata::kOk) fail("exit_scope refused inside a scope", op);
                ref.exit();
            } else if (s != strata::kNoScope || t->state_digest() != before) {
                fail("exit_scope at the outermost scope", op);
            }
        } else {
            std::string name;
            const uint8_t sel = in.byte();
            if (sel < 224) {
                name = pool_name(sel + (code >> 6) * 224u);
            } else {
                size_t len = in.byte();
                if (sel == 255) len += 200;                    // up to 455 bytes: past the limit
                for (size_t k = 0; k < len; ++k) name.push_back(static_cast<char>(in.byte()));
            }
            if (kind <= 4) {
                const int32_t value = static_cast<int32_t>(op * 2654435761u);
                const uint8_t type = static_cast<uint8_t>(code >> 3);
                const uint64_t before = t->state_digest();
                const strata::Status s = t->declare(name.data(), name.size(), value, type);
                const strata::Status want = name.empty() ? strata::kEmptyName
                                            : name.size() > 255 ? strata::kNameTooLong : strata::kOk;
                if (want != strata::kOk) {
                    if (s != want) fail("declare: wrong status for an invalid name", op);
                    if (t->state_digest() != before) fail("rejected name changed the table", op);
                } else if (s == strata::kNoMemory || s == strata::kProbeLimit) {
                    if (t->state_digest() != before) fail("refused declare changed the table", op);
                    if (s == strata::kProbeLimit && !(bounded && o.max_probe)) fail("kProbeLimit without a probe limit", op);
                } else if (s == strata::kOk || s == strata::kRedeclared) {
                    const int r = ref.declare(name, value, type);
                    if (r != static_cast<int>(s)) fail("declare: new/redeclared disagrees with the model", op);
                    seen.push_back(name);
                } else {
                    fail("declare: unexpected status", op);
                }
            } else if (kind <= 6) {
                int32_t a = -1, b = -1;
                uint8_t ta = 0, tb = 0;
                const bool fa_ = t->resolve(name.data(), name.size(), &a, &ta);
                const bool fb = !name.empty() && name.size() <= 255 && ref.resolve(name, &b, &tb);
                if (fa_ != fb || (fa_ && (a != b || ta != tb))) fail("resolve disagrees with the model", op);
            } else {
                // declared_in_current_scope is checked through declare's kRedeclared result;
                // here only that it never claims a name the model cannot resolve.
                if (t->declared_in_current_scope(name.data(), name.size()) &&
                    !(name.size() <= 255 && !name.empty() && ref.resolve(name))) fail("declared_in_current_scope", op);
            }
        }
        if (t->size() != ref.live() || t->depth() != ref.depth() || t->stats().live_identifiers != ref.distinct())
            fail("counters disagree with the model", op);
        if ((op & 15) == 0 && !t->check_invariants()) fail("invariant violated", op);
    }
    if (!t->check_invariants()) fail("invariant violated at the end", op);
    if (bounded) {
        const strata::Stats st = t->stats();
        if (st.rebuilds != 0 || st.index_bytes != static_cast<size_t>(o.index_slots) * 4) fail("static index was rebuilt", op);
        if (o.max_probe && st.longest_probe > o.max_probe) fail("a name was stored beyond the probe limit", op);
    }
    for (size_t k = 0; k < seen.size(); ++k) {
        int32_t a = -1, b = -1;
        uint8_t ta = 0, tb = 0;
        const bool x = t->resolve(seen[k].data(), seen[k].size(), &a, &ta), y = ref.resolve(seen[k], &b, &tb);
        if (x != y || (x && (a != b || ta != tb))) fail("final sweep disagrees with the model", op);
    }
    while (ref.depth() > 0) {
        if (t->exit_scope() != strata::kOk) fail("unwinding", op);
        ref.exit();
    }
    if (t->size() != ref.live() || !t->check_invariants()) fail("state after unwinding", op);
    delete t;
    strata::Table::degenerate_hash() = false;
    if (fa.live != 0) fail("memory leak through the supplied allocator", op);
}

}  // namespace

#ifdef FUZZ_STANDALONE
int main(int argc, char** argv) {
    for (int i = 1; i < argc; ++i) {
        FILE* f = std::fopen(argv[i], "rb");
        if (!f) { std::fprintf(stderr, "cannot open %s\n", argv[i]); return 2; }
        std::vector<uint8_t> d;
        int c;
        while ((c = std::fgetc(f)) != EOF) d.push_back(static_cast<uint8_t>(c));
        std::fclose(f);
        run(d.empty() ? 0 : &d[0], d.size());
    }
    std::printf("replayed %d input(s) without a failure\n", argc - 1);
    return 0;
}
#else
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    run(data, size);
    return 0;
}
#endif
