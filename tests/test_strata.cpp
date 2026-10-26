// Correctness tests for strata::Table. Each numbered block maps to one of the mandatory
// properties described in docs/CORRECTNESS.md. Exit code is non-zero if any check fails.
#define STRATA_TEST_HOOKS
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "../include/strata/strata.hpp"
#include "reference_model.hpp"

using strata::Table;

static int g_checks = 0, g_failed = 0;
#define CHECK(c) do { ++g_checks; if (!(c)) { ++g_failed; std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static uint64_t g_rng = 0x9E3779B97F4A7C15ull;
static uint32_t rnd() {
    g_rng ^= g_rng << 13; g_rng ^= g_rng >> 7; g_rng ^= g_rng << 17;
    return static_cast<uint32_t>(g_rng >> 16);
}
static int decl(Table& t, const std::string& s, int v, uint8_t ty = 0) { return t.declare(s.data(), s.size(), v, ty); }
static int look(const Table& t, const std::string& s) {
    int32_t v = -1;
    return t.resolve(s.data(), s.size(), &v) ? v : -1;
}
static std::string name_of(uint32_t i, int style) {
    static const char* stems[] = {"i", "n", "tmp", "buf", "count", "pxQueue", "xTicksToWait", "mbedtls_ssl_context",
                                  "sqlite3VdbeMemSetStr", "a_really_long_identifier_name_used_for_testing_names_over_60_bytes"};
    char b[32];
    std::snprintf(b, sizeof b, "%u", i);
    if (style == 1) return std::string("std::vector<") + b + ">";       // not packable: raw path
    if (style == 2) return std::string(stems[9]) + "_" + b;             // long
    return std::string(stems[i % 9]) + "_" + b;
}

// Compare a table with the reference model on every name in `pool`.
static bool agrees(const Table& t, const ReferenceModel& ref, const std::vector<std::string>& pool) {
    for (size_t i = 0; i < pool.size(); ++i) {
        int32_t a = -1, b = -1;
        uint8_t ta = 0, tb = 0;
        bool fa = t.resolve(pool[i].data(), pool[i].size(), &a, &ta), fb = ref.resolve(pool[i], &b, &tb);
        if (fa != fb || (fa && (a != b || ta != tb))) return false;
    }
    return t.size() == ref.live() && t.depth() == ref.depth() && t.stats().live_identifiers == ref.distinct();
}

// 1-3: innermost declaration wins, shadowing, restoration on scope exit
static void test_scoping(bool pack) {
    strata::Options o;
    o.pack_names = pack;
    Table t(o);
    CHECK(t.valid());
    CHECK(decl(t, "count", 10) == strata::kOk);
    CHECK(decl(t, "calculate", 11) == strata::kOk);
    CHECK(t.enter_scope() == strata::kOk);
    CHECK(look(t, "count") == 10);
    CHECK(decl(t, "count", 20) == strata::kOk);
    CHECK(look(t, "count") == 20);
    CHECK(t.enter_scope() == strata::kOk);
    CHECK(decl(t, "count", 30, 7) == strata::kOk);
    uint8_t ty = 0;
    int32_t v = 0;
    CHECK(t.resolve_cstr("count", &v, &ty) && v == 30 && ty == 7);
    CHECK(look(t, "calculate") == 11);
    CHECK(t.stats().live_identifiers == 2 && t.size() == 4);  // 'count' stored once, declared three times
    CHECK(t.exit_scope() == strata::kOk);
    CHECK(look(t, "count") == 20);
    CHECK(t.exit_scope() == strata::kOk);
    CHECK(look(t, "count") == 10);
    CHECK(look(t, "missing") == -1);
    CHECK(t.check_invariants());
}

// 4: same-scope redeclaration replaces value and type and reports kRedeclared
static void test_redeclaration() {
    Table t;
    CHECK(decl(t, "x", 1, 1) == strata::kOk);
    CHECK(decl(t, "x", 2, 9) == strata::kRedeclared);
    uint8_t ty = 0;
    int32_t v = 0;
    CHECK(t.resolve_cstr("x", &v, &ty) && v == 2 && ty == 9 && t.size() == 1);
    t.enter_scope();
    CHECK(!t.declared_in_current_scope("x", 1));
    CHECK(decl(t, "x", 3) == strata::kOk);       // shadowing is not a redeclaration
    CHECK(t.declared_in_current_scope("x", 1));
    CHECK(decl(t, "x", 4) == strata::kRedeclared);
    CHECK(look(t, "x") == 4);
    t.exit_scope();
    CHECK(look(t, "x") == 2 && t.check_invariants());
}

// 6: input rules for names
static void test_name_rules() {
    Table t;
    CHECK(t.declare("", 0, 1) == strata::kEmptyName);
    std::string ok(strata::kMaxNameLen, 'a'), too_long(strata::kMaxNameLen + 1, 'a');
    CHECK(decl(t, ok, 5) == strata::kOk && look(t, ok) == 5);
    CHECK(decl(t, too_long, 6) == strata::kNameTooLong && look(t, too_long) == -1);
    CHECK(t.size() == 1);
    // bytes outside [A-Za-z0-9_] are stored raw; embedded NUL and high bytes are fine
    std::string odd("a\0b", 3), utf8("na\xc3\xafve"), op("operator<<"), a5("abcde"), a5x("abcd?");
    CHECK(decl(t, odd, 7) == strata::kOk && decl(t, utf8, 8) == strata::kOk && decl(t, op, 9) == strata::kOk);
    CHECK(decl(t, a5, 10) == strata::kOk && decl(t, a5x, 11) == strata::kOk);
    CHECK(look(t, odd) == 7 && look(t, utf8) == 8 && look(t, op) == 9 && look(t, a5) == 10 && look(t, a5x) == 11);
    CHECK(look(t, std::string("a\0c", 3)) == -1 && look(t, "a") == -1 && look(t, "abcd") == -1);
    // names that differ only in length, case or last character stay distinct
    const char* fam[] = {"a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa", "A", "aaaaA", "aaaa_", "aaaa0", "_", "__", "0"};
    for (int i = 0; i < 13; ++i) CHECK(decl(t, fam[i], 100 + i) == strata::kOk);
    for (int i = 0; i < 13; ++i) CHECK(look(t, fam[i]) == 100 + i);
    CHECK(t.check_invariants());
    // packing really is used: a 10-character identifier takes 2 name words, raw takes 3
    strata::Key k;
    t.make_key("abcdefghij", 10, k);
    CHECK(k.n == 2 && ((k.meta >> 7) & 1) == 0);
    strata::Options raw;
    raw.pack_names = false;
    Table r(raw);
    r.make_key("abcdefghij", 10, k);
    CHECK(k.n == 3 && ((k.meta >> 7) & 1) == 1);
}

// 7: every key in one cluster (worst-case collisions) still resolves correctly
static void test_collisions() {
    Table::degenerate_hash() = true;
    {
        Table t;
        ReferenceModel ref;
        std::vector<std::string> pool;
        for (int i = 0; i < 400; ++i) pool.push_back(name_of(i, 0));
        for (int round = 0; round < 6; ++round) {
            t.enter_scope(); ref.enter();
            for (int i = round * 50; i < round * 50 + 120 && i < 400; ++i) { decl(t, pool[i], i + round); ref.declare(pool[i], i + round); }
            CHECK(agrees(t, ref, pool));
        }
        for (int round = 0; round < 6; ++round) { t.exit_scope(); ref.exit(); CHECK(agrees(t, ref, pool) && t.check_invariants()); }
    }
    Table::degenerate_hash() = false;
}

// layout promise: 4 bytes of undo per fresh declaration, 12 per shadowing declaration,
// and the type tag travels with the declaration through shadowing and restoration
static void test_layout() {
    Table t;
    size_t u0 = t.stats().undo_bytes, i0 = t.stats().ident_bytes;
    CHECK(decl(t, "alpha", 1, 11) == strata::kOk);
    CHECK(t.stats().undo_bytes - u0 == 4 && t.stats().ident_bytes - i0 == 12);   // 2 header words + 1 name word
    t.enter_scope();
    size_t u1 = t.stats().undo_bytes, i1 = t.stats().ident_bytes;
    CHECK(decl(t, "alpha", 2, 22) == strata::kOk);
    CHECK(t.stats().undo_bytes - u1 == 12 && t.stats().ident_bytes == i1);       // the name is not stored again
    uint8_t ty = 0; int32_t v = 0;
    CHECK(t.resolve_cstr("alpha", &v, &ty) && v == 2 && ty == 22);
    t.exit_scope();
    CHECK(t.resolve_cstr("alpha", &v, &ty) && v == 1 && ty == 11 && t.check_invariants());
}

// 9: invalid scope operations fail safely
static void test_invalid_scope_ops() {
    Table t;
    CHECK(t.exit_scope() == strata::kNoScope);
    decl(t, "g", 1);
    CHECK(t.exit_scope() == strata::kNoScope && look(t, "g") == 1 && t.depth() == 0);
    for (int i = 0; i < 2000; ++i) CHECK(t.enter_scope() == strata::kOk);   // deep nesting
    decl(t, "g", 2);
    for (int i = 0; i < 2000; ++i) CHECK(t.exit_scope() == strata::kOk);
    CHECK(t.exit_scope() == strata::kNoScope && look(t, "g") == 1 && t.check_invariants());
    for (int i = 0; i < strata::kMaxDepth; ++i) CHECK(t.enter_scope() == strata::kOk);
    CHECK(t.enter_scope() == strata::kTooDeep && t.depth() == strata::kMaxDepth);   // documented depth limit
    CHECK(decl(t, "g", 3) == strata::kOk && look(t, "g") == 3 && t.check_invariants());
    for (int i = 0; i < strata::kMaxDepth; ++i) t.exit_scope();
    CHECK(look(t, "g") == 1 && t.depth() == 0);
    char small[64];
    Table bad(small, sizeof small);                                         // below the minimum size
    CHECK(!bad.valid() && bad.declare_cstr("a", 1) == strata::kNoMemory && bad.enter_scope() == strata::kNoMemory);
}

// 5, 8, 10, 12: random operation sequences against the reference model, with index
// rebuilds, buffer growth and shrinking happening along the way
static void test_random(int style, bool pack, size_t initial_bytes, int steps, int pool_size, int max_depth, bool sparse = false) {
    strata::Options o;
    o.pack_names = pack;
    o.sparse_index = sparse;
    o.initial_bytes = initial_bytes;
    Table t(o);
    ReferenceModel ref;
    std::vector<std::string> pool;
    for (int i = 0; i < pool_size; ++i) pool.push_back(name_of(i, style == 3 ? static_cast<int>(rnd() % 3) : style));
    size_t peak_cap = 0, peak_live = 0;
    for (int s = 0; s < steps; ++s) {
        uint32_t r = rnd() % 100;
        const std::string& nm = pool[rnd() % pool.size()];
        if (r < 9 && ref.depth() < static_cast<size_t>(max_depth)) { CHECK(t.enter_scope() == strata::kOk); ref.enter(); }
        else if (r < 17) { bool a = t.exit_scope() == strata::kOk, b = ref.exit(); CHECK(a == b); }
        else if (r < 55) { int v = static_cast<int>(rnd()); uint8_t ty = static_cast<uint8_t>(rnd()); CHECK(decl(t, nm, v, ty) == ref.declare(nm, v, ty)); }
        else {
            int32_t a = -1, b = -1;
            bool fa = t.resolve(nm.data(), nm.size(), &a), fb = ref.resolve(nm, &b);
            CHECK(fa == fb && a == b);
        }
        if (t.stats().capacity_bytes > peak_cap) peak_cap = t.stats().capacity_bytes;
        if (ref.live() > peak_live) peak_live = ref.live();
        if (s % 997 == 0) CHECK(t.check_invariants() && agrees(t, ref, pool));
    }
    while (ref.exit()) CHECK(t.exit_scope() == strata::kOk);
    CHECK(agrees(t, ref, pool) && t.check_invariants());
    CHECK(t.stats().rebuilds > 0);                         // rehash happened and kept every declaration
    CHECK(peak_live < 64 || t.stats().capacity_bytes <= peak_cap);
}

// 10: memory is reclaimed; the growable buffer shrinks after a large scope closes
static void test_reclamation() {
    strata::Options o;
    o.initial_bytes = 256;
    Table t(o);
    decl(t, "keep", 1);
    size_t base_stacks = t.stats().ident_bytes + t.stats().undo_bytes;
    t.enter_scope();
    for (int i = 0; i < 20000; ++i) decl(t, name_of(i, 0), i);
    size_t big_cap = t.stats().capacity_bytes, big_used = t.stats().used_bytes;
    CHECK(t.stats().live_identifiers == 20001 && big_used > 400000);
    t.exit_scope();
    CHECK(t.stats().capacity_bytes == big_cap);            // not given back at once ...
    for (int i = 0; i < 64; ++i) { t.enter_scope(); t.exit_scope(); }   // ... but after 64 calm scope exits
    strata::Stats s = t.stats();
    CHECK(s.live_identifiers == 1 && s.live_declarations == 1 && look(t, "keep") == 1);
    CHECK(s.ident_bytes + s.undo_bytes == base_stacks);     // both stacks are back where they were
    CHECK(s.capacity_bytes < big_cap / 100);               // buffer was given back
    CHECK(s.peak_used_bytes >= big_used && t.check_invariants());
    // without shrinking the capacity stays, but the stacks are still popped
    o.shrink = false;
    Table u(o);
    u.enter_scope();
    for (int i = 0; i < 5000; ++i) decl(u, name_of(i, 0), i);
    size_t cap = u.stats().capacity_bytes;
    u.exit_scope();
    CHECK(u.stats().capacity_bytes == cap && u.stats().live_identifiers == 0 && u.stats().ident_bytes == 4);
    // enter/exit churn must not accumulate anything (no tombstones, no leaks)
    Table c;
    decl(c, "g", 0);
    size_t used0 = c.stats().used_bytes;
    for (int i = 0; i < 20000; ++i) {
        c.enter_scope();
        decl(c, name_of(i % 37, 0), i);
        decl(c, "g", i);
        c.exit_scope();
    }
    CHECK(c.stats().used_bytes == used0 && look(c, "g") == 0 && c.check_invariants());
}

// 11: fixed buffer - exhaustion is reported, nothing is half-done, and the table keeps working
static void test_fixed_capacity() {
    static uint32_t buf[1024];   // 4096 bytes
    Table t(buf, sizeof buf);
    ReferenceModel ref;
    std::vector<std::string> pool;
    for (int i = 0; i < 600; ++i) pool.push_back(name_of(i, i % 5 == 0 ? 2 : 0));
    CHECK(t.valid() && t.stats().capacity_bytes == 4096);
    t.enter_scope(); ref.enter();
    int stored = 0, refused = 0;
    for (size_t i = 0; i < pool.size(); ++i) {
        strata::Stats before = t.stats();
        int r = decl(t, pool[i], static_cast<int>(i));
        if (r == strata::kOk) { ref.declare(pool[i], static_cast<int>(i)); ++stored; }
        else {
            ++refused;
            strata::Stats after = t.stats();
            CHECK(r == strata::kNoMemory);
            CHECK(after.live_declarations == before.live_declarations && after.live_identifiers == before.live_identifiers);
            CHECK(after.ident_bytes == before.ident_bytes && after.undo_bytes == before.undo_bytes);
        }
    }
    CHECK(stored > 50 && refused > 0);
    CHECK(agrees(t, ref, pool) && t.check_invariants());            // everything stored is intact
    CHECK(t.stats().used_bytes <= 4096);
    while (t.enter_scope() == strata::kOk) ref.enter();             // scope marks also hit the limit cleanly
    CHECK(agrees(t, ref, pool) && t.check_invariants());
    while (ref.exit()) CHECK(t.exit_scope() == strata::kOk);
    CHECK(t.size() == 0 && t.stats().live_identifiers == 0);
    for (int i = 0; i < 40; ++i) CHECK(decl(t, pool[i], i) == strata::kOk);  // usable again after exhaustion
    CHECK(t.check_invariants());

    // a larger fixed buffer: the index has to grow in place (identifier stack is moved up)
    static uint32_t big[16384];   // 64 KiB
    Table b(big, sizeof big);
    ReferenceModel bref;
    std::vector<std::string> names;
    for (int i = 0; i < 4000; ++i) { char nm[8]; std::snprintf(nm, sizeof nm, "v%d", i); names.push_back(nm); }
    int kept = 0;
    for (size_t i = 0; i < names.size(); ++i) {
        if (i % 500 == 0 && b.enter_scope() == strata::kOk) bref.enter();
        if (decl(b, names[i], static_cast<int>(i)) == strata::kOk) { bref.declare(names[i], static_cast<int>(i)); ++kept; }
    }
    CHECK(kept > 2000 && kept < 4000 && b.stats().rebuilds > 0 && b.stats().capacity_bytes == 65536);
    CHECK(agrees(b, bref, names) && b.check_invariants());
    while (bref.exit()) { CHECK(b.exit_scope() == strata::kOk); CHECK(agrees(b, bref, names)); }
    CHECK(b.check_invariants());
}

// 11: growable mode with a budget, and with an allocator that starts failing
static int g_alloc_budget = 1 << 30, g_live_blocks = 0;
static void* counting_alloc(size_t n, void*) {
    if (g_alloc_budget <= 0) return 0;
    --g_alloc_budget;
    ++g_live_blocks;
    return std::malloc(n);
}
static void counting_free(void* p, void*) { --g_live_blocks; std::free(p); }

static void test_allocation_failure() {
    for (int allowed = 1; allowed <= 10; ++allowed) {
        g_alloc_budget = allowed;
        {
            strata::Options o;
            o.initial_bytes = 128;
            o.alloc = counting_alloc;
            o.free = counting_free;
            Table t(o);
            ReferenceModel ref;
            std::vector<std::string> pool;
            for (int i = 0; i < 3000; ++i) pool.push_back(name_of(i, 0));
            int failures = 0;
            for (size_t i = 0; i < pool.size(); ++i) {
                if (i % 200 == 0 && t.enter_scope() == strata::kOk) ref.enter();
                int r = decl(t, pool[i], static_cast<int>(i));
                if (r == strata::kOk) ref.declare(pool[i], static_cast<int>(i));
                else { CHECK(r == strata::kNoMemory); ++failures; }
            }
            CHECK(failures > 0);
            CHECK(agrees(t, ref, pool) && t.check_invariants());   // strong guarantee: no declaration lost
            while (ref.exit()) CHECK(t.exit_scope() == strata::kOk);
            CHECK(agrees(t, ref, pool));
        }
        CHECK(g_live_blocks == 0);                                 // nothing leaked
    }
    g_alloc_budget = 1 << 30;
    strata::Options o;
    o.initial_bytes = 256;
    o.max_bytes = 8192;                                            // explicit memory budget
    Table t(o);
    int ok = 0;
    std::vector<bool> stored(5000, false);
    for (int i = 0; i < 5000; ++i) if (decl(t, name_of(i, 0), i) == strata::kOk) { stored[i] = true; ++ok; }
    CHECK(ok > 100 && ok < 5000 && t.stats().capacity_bytes <= 8192 && t.check_invariants());
    for (int i = 0; i < 5000; ++i) CHECK(look(t, name_of(i, 0)) == (stored[i] ? i : -1));
}

// All-or-nothing: in a fixed buffer, EVERY refused operation must leave the complete state
// (index, both stacks, counters) bit-for-bit unchanged, and everything accepted before must
// still resolve correctly. Checked with the normal hash and with every key forced into one
// probe cluster, for random mixes, deep shadowing and deep nesting, at five buffer sizes.
static void test_all_or_nothing() {
    static uint32_t buf[8192];
    const size_t sizes[] = {256, 1024, 2048, 8192, 32768};
    for (int degenerate = 0; degenerate <= 1; ++degenerate) {
        Table::degenerate_hash() = degenerate != 0;
        for (int si = 0; si < 5; ++si) {
            for (int mix = 0; mix < 3; ++mix) {       // 0 random, 1 deep shadowing, 2 deep nesting
                Table t(buf, sizes[si]);
                ReferenceModel ref;
                std::vector<std::string> pool;
                int pool_size = mix == 1 ? 3 : (degenerate ? 120 : 600);
                for (int i = 0; i < pool_size; ++i) pool.push_back(name_of(i, i % 7 == 0 ? 2 : (i % 11 == 0 ? 1 : 0)));
                int refused = 0, steps = degenerate ? 6000 : 20000;
                for (int s = 0; s < steps; ++s) {
                    uint32_t r = rnd() % 100;
                    const std::string& nm = pool[rnd() % pool.size()];
                    uint64_t before = t.state_digest();
                    int enter_cut = mix == 0 ? 10 : 30, exit_cut = mix == 0 ? 18 : (mix == 1 ? 36 : 33);
                    if (r < static_cast<uint32_t>(enter_cut)) {
                        strata::Status st = t.enter_scope();
                        if (st == strata::kOk) ref.enter();
                        else { ++refused; CHECK(st == strata::kNoMemory); CHECK(t.state_digest() == before); }
                    } else if (r < static_cast<uint32_t>(exit_cut)) {
                        bool a = t.exit_scope() == strata::kOk, b = ref.exit();
                        CHECK(a == b);
                        if (!a) CHECK(t.state_digest() == before);
                    } else if (r < 70) {
                        int v = static_cast<int>(rnd());
                        int st = decl(t, nm, v, 3);
                        if (st >= 0) CHECK(st == ref.declare(nm, v, 3));
                        else { ++refused; CHECK(st == strata::kNoMemory); CHECK(t.state_digest() == before); }
                    } else {
                        int32_t a = -1, b = -1;
                        bool fa = t.resolve(nm.data(), nm.size(), &a), fb = ref.resolve(nm, &b);
                        CHECK(fa == fb && a == b);
                        CHECK(t.state_digest() == before);          // lookups never modify the table
                    }
                    if (s % 499 == 0) CHECK(t.check_invariants() && agrees(t, ref, pool));
                }
                CHECK(sizes[si] > 2048 || refused > 0);             // the small buffers really were exhausted
                CHECK(agrees(t, ref, pool) && t.check_invariants());
                while (ref.exit()) { CHECK(t.exit_scope() == strata::kOk); }
                CHECK(agrees(t, ref, pool) && t.check_invariants());   // unwinding after exhaustion is exact
            }
        }
    }
    Table::degenerate_hash() = false;
    // other refusals are also no-ops
    Table t(buf, 4096);
    decl(t, "a", 1);
    uint64_t d = t.state_digest();
    std::string too_long(300, 'x');
    CHECK(decl(t, too_long, 2) == strata::kNameTooLong && t.declare("", 0, 3) == strata::kEmptyName);
    CHECK(t.exit_scope() == strata::kNoScope && t.state_digest() == d);
}

// Scope exit when all keys share one probe cluster and the index is rebuilt while scopes are
// open: the recorded slots must follow the keys through every rebuild.
static void test_exit_under_collisions_and_rebuilds() {
    for (int degenerate = 0; degenerate <= 1; ++degenerate) {
        Table::degenerate_hash() = degenerate != 0;
        strata::Options o;
        o.initial_bytes = 128;
        Table t(o);
        ReferenceModel ref;
        std::vector<std::string> pool;
        for (int i = 0; i < 300; ++i) pool.push_back(name_of(i, 0));
        for (int depth = 0; depth < 30; ++depth) {             // each level adds names and shadows older ones
            t.enter_scope(); ref.enter();
            for (int i = 0; i < 10; ++i) { int k = depth * 10 + i; decl(t, pool[k], k); ref.declare(pool[k], k); }
            for (int i = 0; i < depth; ++i) { int k = i * 7 % (depth * 10); decl(t, pool[k], -k); ref.declare(pool[k], -k); }
            CHECK(agrees(t, ref, pool) && t.check_invariants());
        }
        CHECK(t.stats().rebuilds > 3);
        for (int depth = 0; depth < 30; ++depth) {
            CHECK(t.exit_scope() == strata::kOk); ref.exit();
            CHECK(agrees(t, ref, pool) && t.check_invariants());
        }
        CHECK(t.size() == 0 && t.stats().live_identifiers == 0);
    }
    Table::degenerate_hash() = false;
}

// deep shadowing: one name declared in 5000 nested scopes (the case METIS-X rejects after 250)
static void test_deep_shadowing() {
    Table t;
    for (int d = 0; d < 5000; ++d) { CHECK(decl(t, "x", d) == strata::kOk); CHECK(t.enter_scope() == strata::kOk); }
    CHECK(t.stats().live_identifiers == 1 && t.size() == 5000);
    for (int d = 4999; d >= 0; --d) { CHECK(t.exit_scope() == strata::kOk); CHECK(look(t, "x") == d); }
    CHECK(t.check_invariants());
}

// 14: keyed hash. Same behaviour as the default hash under every key; different keys place
// names differently; rebuilds (which re-hash stored names) keep the table consistent.
static void test_keyed_hash() {
    const uint32_t keys[4][2] = {{0, 0}, {1, 0}, {0x01234567u, 0x89abcdefu}, {0xffffffffu, 0xffffffffu}};
    uint32_t first_hash[4];
    for (int ki = 0; ki < 4; ++ki) {
        strata::Options o;
        o.initial_bytes = 64;
        o.keyed = true;
        o.key[0] = keys[ki][0];
        o.key[1] = keys[ki][1];
        Table t(o);
        strata::Key k;
        CHECK(t.make_key("count", 5, k) == strata::kOk);
        first_hash[ki] = k.hash;
        ReferenceModel ref;
        std::vector<std::string> pool;
        for (uint32_t i = 0; i < 600; ++i) pool.push_back(name_of(i, static_cast<int>(i % 3)));
        for (int step = 0; step < 60000; ++step) {
            uint32_t r = rnd() % 100;
            const std::string& nm = pool[rnd() % pool.size()];
            if (r < 12 && ref.depth() < 10) { CHECK(t.enter_scope() == strata::kOk); ref.enter(); }
            else if (r < 24) { CHECK((t.exit_scope() == strata::kOk) == ref.exit()); }
            else if (r < 60) { CHECK(decl(t, nm, step, static_cast<uint8_t>(step)) == ref.declare(nm, step, static_cast<uint8_t>(step))); }
            else { int32_t b = -1; if (!ref.resolve(nm, &b)) b = -1; CHECK(look(t, nm) == b); }
            if (step % 5000 == 0) CHECK(t.check_invariants() && agrees(t, ref, pool));
        }
        CHECK(t.stats().rebuilds > 0);
        CHECK(t.check_invariants() && agrees(t, ref, pool));
    }
    CHECK(first_hash[0] != first_hash[1] && first_hash[1] != first_hash[2] && first_hash[2] != first_hash[3]);
    // the default hash is unchanged by the presence of the option
    strata::Options plain;
    Table a(plain), b;
    strata::Key ka, kb;
    a.make_key("mbedtls_ssl_context", 19, ka);
    b.make_key("mbedtls_ssl_context", 19, kb);
    CHECK(ka.hash == kb.hash);
}

// 15: bounded mode (static index, optional probe limit).
static void test_bounded_mode() {
    std::vector<uint32_t> buf(4096);
    {   // configurations that must be rejected, not silently unbounded
        strata::Options o;
        o.max_probe = 8;                                   // probe limit without a static index
        Table t1(&buf[0], buf.size() * 4, o);
        CHECK(!t1.valid() && t1.declare("a", 1, 1) == strata::kNoMemory);
        o.index_slots = 48;                                // not a power of two
        Table t2(&buf[0], buf.size() * 4, o);
        CHECK(!t2.valid());
        o.index_slots = 8;                                 // too small
        Table t3(&buf[0], buf.size() * 4, o);
        CHECK(!t3.valid());
        o.index_slots = 4096;                              // does not fit the buffer
        Table t4(&buf[0], buf.size() * 4, o);
        CHECK(!t4.valid());
        o.index_slots = 64;
        Table t5(&buf[0], buf.size() * 4, o);
        CHECK(t5.valid() && t5.check_invariants() && t5.stats().index_bytes == 256);
        strata::Options g;                                 // growable mode ignores both fields
        g.index_slots = 64;
        g.max_probe = 1;
        Table t6(g);
        CHECK(t6.valid());
        for (uint32_t i = 0; i < 200; ++i) CHECK(decl(t6, name_of(i, 0), 1) == strata::kOk);
    }
    {   // the static index is never rebuilt; the load limit refuses with nothing changed
        strata::Options o;
        o.index_slots = 16;
        Table t(&buf[0], buf.size() * 4, o);
        for (uint32_t i = 0; i < 12; ++i) CHECK(decl(t, name_of(i, 0), static_cast<int>(i)) == strata::kOk);
        uint64_t d = t.state_digest();
        CHECK(decl(t, name_of(12, 0), 12) == strata::kNoMemory && t.state_digest() == d);
        CHECK(t.enter_scope() == strata::kOk);
        CHECK(decl(t, name_of(3, 0), 99) == strata::kOk);          // shadowing needs no index slot
        CHECK(look(t, name_of(3, 0)) == 99);
        CHECK(t.exit_scope() == strata::kOk && look(t, name_of(3, 0)) == 3);
        CHECK(t.stats().rebuilds == 0 && t.stats().index_bytes == 64 && t.check_invariants());
    }
    {   // probe limit with every key in one cluster
        Table::degenerate_hash() = true;
        strata::Options o;
        o.index_slots = 64;
        o.max_probe = 4;
        Table t(&buf[0], buf.size() * 4, o);
        for (uint32_t i = 0; i < 4; ++i) CHECK(decl(t, name_of(i, 0), static_cast<int>(i)) == strata::kOk);
        uint64_t d = t.state_digest();
        CHECK(decl(t, name_of(4, 0), 4) == strata::kProbeLimit);
        CHECK(t.state_digest() == d && t.check_invariants());
        CHECK(look(t, name_of(4, 0)) == -1 && look(t, name_of(3, 0)) == 3 && look(t, name_of(0, 0)) == 0);
        CHECK(t.enter_scope() == strata::kOk);
        CHECK(decl(t, name_of(1, 0), 77) == strata::kOk && look(t, name_of(1, 0)) == 77);   // shadowing still works
        CHECK(decl(t, name_of(5, 0), 5) == strata::kProbeLimit);
        CHECK(t.exit_scope() == strata::kOk && look(t, name_of(1, 0)) == 1);
        CHECK(t.stats().longest_probe == 4);
        Table::degenerate_hash() = false;
        // scope exit frees the slots, so the limit refuses only while the cluster is full
        Table::degenerate_hash() = true;
        Table u(&buf[0], buf.size() * 4, o);
        CHECK(u.enter_scope() == strata::kOk);
        for (uint32_t i = 0; i < 4; ++i) CHECK(decl(u, name_of(i, 0), 1) == strata::kOk);
        CHECK(decl(u, name_of(9, 0), 1) == strata::kProbeLimit);
        CHECK(u.exit_scope() == strata::kOk);
        CHECK(decl(u, name_of(9, 0), 1) == strata::kOk && u.check_invariants());
        Table::degenerate_hash() = false;
    }
    // randomized differential runs: refusals of either kind leave the state untouched and
    // are not applied to the model; everything else must agree with it
    for (int cfg = 0; cfg < 12; ++cfg) {
        const bool degenerate = cfg & 1, keyed = cfg & 2;
        const uint32_t limits[3] = {0, 3, 16};
        Table::degenerate_hash() = degenerate;
        strata::Options o;
        o.index_slots = 256;
        o.max_probe = limits[cfg / 4];
        o.keyed = keyed;
        o.key[0] = 0xC0FFEEu + static_cast<uint32_t>(cfg);
        o.key[1] = 0x5EEDu;
        Table t(&buf[0], 6000, o);
        ReferenceModel ref;
        std::vector<std::string> pool;
        for (uint32_t i = 0; i < 400; ++i) pool.push_back(name_of(i, static_cast<int>(i % 3)));
        size_t refused_probe = 0, refused_memory = 0;
        for (int step = 0; step < 40000; ++step) {
            uint32_t r = rnd() % 100;
            const std::string& nm = pool[rnd() % pool.size()];
            if (r < 10 && ref.depth() < 8) {
                uint64_t d = t.state_digest();
                if (t.enter_scope() == strata::kOk) ref.enter();
                else CHECK(t.state_digest() == d);
            } else if (r < 20) {
                CHECK((t.exit_scope() == strata::kOk) == ref.exit());
            } else if (r < 60) {
                uint64_t d = t.state_digest();
                int s = decl(t, nm, step);
                if (s == strata::kProbeLimit || s == strata::kNoMemory) {
                    CHECK(t.state_digest() == d);
                    CHECK(s == strata::kNoMemory || o.max_probe != 0);
                    if (s == strata::kProbeLimit) ++refused_probe; else ++refused_memory;
                } else {
                    CHECK(s == ref.declare(nm, step));
                }
            } else {
                int32_t b = -1;
                if (!ref.resolve(nm, &b)) b = -1;
                CHECK(look(t, nm) == b);
            }
            if (step % 4000 == 0) CHECK(t.check_invariants() && agrees(t, ref, pool));
        }
        CHECK(t.check_invariants() && agrees(t, ref, pool));
        CHECK(t.stats().rebuilds == 0);
        CHECK(o.max_probe == 0 || t.stats().longest_probe <= o.max_probe);
        if (degenerate && o.max_probe) CHECK(refused_probe > 0);
        if (o.max_probe == 0) CHECK(refused_memory > 0);   // without a probe limit the 6000-byte buffer runs out
        while (ref.depth() > 0) { CHECK(t.exit_scope() == strata::kOk); ref.exit(); }
        CHECK(agrees(t, ref, pool));
    }
    Table::degenerate_hash() = false;
}

// 16: canonical state. With a static index, the complete state after ANY sequence of
// operations is bit-for-bit the state of a fresh table into which only the declarations
// that are still live were made, in their original order. Scope exits leave no trace
// (no tombstones, no moved keys), so the table cannot degrade with use, and results about
// insertion-only linear probing apply to it at every moment.
static void test_canonical_state() {
    struct LiveDecl { std::string name; int32_t value; uint8_t type; };
    for (int cfg = 0; cfg < 6; ++cfg) {
        const bool degenerate = cfg & 1;
        Table::degenerate_hash() = degenerate;
        strata::Options o;
        o.index_slots = 512;
        o.keyed = cfg >= 4;
        o.key[0] = 77u + static_cast<uint32_t>(cfg);
        o.pack_names = cfg != 2;
        std::vector<uint32_t> a(8192), b(8192);
        Table t(&a[0], a.size() * 4, o);
        std::vector<std::vector<LiveDecl> > live(1);
        std::vector<std::string> pool;
        for (uint32_t i = 0; i < 300; ++i) pool.push_back(name_of(i, static_cast<int>(i % 3)));
        for (int step = 1; step <= 30000; ++step) {
            uint32_t r = rnd() % 100;
            if (r < 14 && live.size() < 12) {
                if (t.enter_scope() == strata::kOk) live.push_back(std::vector<LiveDecl>());
            } else if (r < 30) {
                if (live.size() > 1) { CHECK(t.exit_scope() == strata::kOk); live.pop_back(); }
            } else {
                const std::string& nm = pool[rnd() % pool.size()];
                const uint8_t ty = static_cast<uint8_t>(step);
                int st = decl(t, nm, step, ty);
                if (st == strata::kOk) {
                    LiveDecl d = {nm, step, ty};
                    live.back().push_back(d);
                } else if (st == strata::kRedeclared) {
                    for (size_t i = 0; i < live.back().size(); ++i)
                        if (live.back()[i].name == nm) { live.back()[i].value = step; live.back()[i].type = ty; }
                }
            }
            if (step % 500 == 0) {
                Table fresh(&b[0], b.size() * 4, o);
                bool ok = true;
                for (size_t sc = 0; sc < live.size(); ++sc) {
                    if (sc) ok = ok && fresh.enter_scope() == strata::kOk;
                    for (size_t i = 0; i < live[sc].size(); ++i)
                        ok = ok && decl(fresh, live[sc][i].name, live[sc][i].value, live[sc][i].type) == strata::kOk;
                }
                CHECK(ok);
                CHECK(fresh.state_digest() == t.state_digest());
                CHECK(std::memcmp(&a[0], &b[0], t.stats().index_bytes + t.stats().ident_bytes) == 0);
            }
        }
    }
    Table::degenerate_hash() = false;
}

int main() {
    test_scoping(true);
    test_scoping(false);
    test_redeclaration();
    test_name_rules();
    test_layout();
    test_collisions();
    test_invalid_scope_ops();
    test_random(0, true, 64, 200000, 800, 12);     // ordinary identifiers
    test_random(0, false, 64, 100000, 800, 12);    // raw (unpacked) names
    test_random(1, true, 128, 100000, 500, 6);     // names that cannot be packed
    test_random(2, true, 128, 100000, 300, 40);    // long names, deep nesting
    test_random(3, true, 4096, 300000, 5000, 8);   // mixed, many live names
    test_random(0, true, 64, 100000, 12, 60);      // heavy shadowing of very few names
    test_random(3, true, 64, 200000, 3000, 10, true);   // sparse index option
    test_reclamation();
    test_fixed_capacity();
    test_allocation_failure();
    test_all_or_nothing();
    test_exit_under_collisions_and_rebuilds();
    test_deep_shadowing();
    test_keyed_hash();
    test_bounded_mode();
    test_canonical_state();
    std::printf("%d checks, %d failed\n", g_checks, g_failed);
    return g_failed ? 1 : 0;
}
