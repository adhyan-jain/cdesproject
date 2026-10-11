// Correctness tests for strata::Table. Each numbered block maps to one of the mandatory
// properties in docs/METHODOLOGY.md. Exit code is non-zero if any check fails.
#define STRATA_TEST_HOOKS
#include <cstdio>
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
static void test_random(int style, bool pack, size_t initial_bytes, int steps, int pool_size, int max_depth) {
    strata::Options o;
    o.pack_names = pack;
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

// deep shadowing: one name declared in 5000 nested scopes (the case METIS-X rejects after 250)
static void test_deep_shadowing() {
    Table t;
    for (int d = 0; d < 5000; ++d) { CHECK(decl(t, "x", d) == strata::kOk); CHECK(t.enter_scope() == strata::kOk); }
    CHECK(t.stats().live_identifiers == 1 && t.size() == 5000);
    for (int d = 4999; d >= 0; --d) { CHECK(t.exit_scope() == strata::kOk); CHECK(look(t, "x") == d); }
    CHECK(t.check_invariants());
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
    test_reclamation();
    test_fixed_capacity();
    test_allocation_failure();
    test_deep_shadowing();
    std::printf("%d checks, %d failed\n", g_checks, g_failed);
    return g_failed ? 1 : 0;
}
