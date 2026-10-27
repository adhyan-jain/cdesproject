// Reviewer-requested tests for strata::Table (see docs/EVIDENCE.md, section 4).
//
//   T1  whole-buffer state equality after every scope exit, against a fresh table that
//       replays only the still-live declarations; reports what may legitimately differ
//   T2  refusal atomicity at every reservation boundary (entire buffer compared with memcmp)
//       plus the status precedence table
//   T3  encoding tests: packed / raw round trips, padding, NUL, high-bit bytes, limits,
//       and the bit layout of every stored word
//
// Exit code is non-zero if an asserted property fails; measured (non-asserted) facts are
// printed. Usage: test_review [seed]
#define STRATA_TEST_HOOKS
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "../include/strata/strata.hpp"
#include "reference_model.hpp"

using strata::Table;
using strata::Options;
using strata::Stats;

static int g_checks = 0, g_failed = 0;
#define CHECK(c) do { ++g_checks; if (!(c)) { ++g_failed; std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static uint64_t g_rng = 0x9E3779B97F4A7C15ull;
static uint32_t rnd() {
    g_rng ^= g_rng << 13; g_rng ^= g_rng >> 7; g_rng ^= g_rng << 17;
    return static_cast<uint32_t>(g_rng >> 16);
}
static const uint32_t kFill = 0xDEADBEEFu;

// ---------------------------------------------------------------------------------------
// A growable table's block, as seen through the allocation hooks.
struct Tracker {
    uint32_t* cur;
    size_t bytes;
    long calls;
    long fail_at;   // the call with this ordinal (1-based) fails; 0 = never
    Tracker() : cur(0), bytes(0), calls(0), fail_at(0) {}
};
static void fill_words(uint32_t* p, size_t from_bytes, size_t to_bytes) {
    for (size_t i = from_bytes / 4; i < to_bytes / 4; ++i) p[i] = kFill;
}
static void* tr_alloc(size_t n, void* u) {
    Tracker* t = static_cast<Tracker*>(u);
    if (++t->calls == t->fail_at) return 0;
    uint32_t* p = static_cast<uint32_t*>(std::malloc(n));
    if (!p) return 0;
    fill_words(p, 0, n);
    t->cur = p; t->bytes = n;
    return p;
}
static void tr_free(void* p, void*) { std::free(p); }
static void* tr_realloc(void* p, size_t ob, size_t nb, void* u) {
    Tracker* t = static_cast<Tracker*>(u);
    if (++t->calls == t->fail_at) return 0;
    uint32_t* np = static_cast<uint32_t*>(std::malloc(nb));
    if (!np) return 0;
    fill_words(np, 0, nb);
    std::memcpy(np, p, ob < nb ? ob : nb);
    std::free(p);
    t->cur = np; t->bytes = nb;
    return np;
}

// One table plus the memory it lives in.
struct Inst {
    std::vector<uint32_t> buf;   // fixed mode: the supplied buffer (+ tail word if bytes % 4 != 0)
    size_t bytes;
    Tracker tr;
    Table* t;
    bool growable;
    Inst() : bytes(0), t(0), growable(false) {}
    ~Inst() { delete t; }
    const uint32_t* base() const { return growable ? tr.cur : &buf[0]; }
    size_t total_words() const { return growable ? tr.bytes / 4 : buf.size(); }
    size_t cap_words() const { return t->stats().capacity_bytes / 4; }
private:
    Inst(const Inst&);
    Inst& operator=(const Inst&);
};
static void make_fixed(Inst& in, size_t bytes, const Options& o) {
    in.growable = false;
    in.bytes = bytes;
    in.buf.assign((bytes + 3) / 4, kFill);
    in.t = new Table(&in.buf[0], bytes, o);
}
static void make_growable(Inst& in, const Options& base) {
    in.growable = true;
    Options o = base;
    o.alloc = tr_alloc; o.free = tr_free; o.realloc = tr_realloc; o.user = &in.tr;
    in.t = new Table(o);
}

// ---------------------------------------------------------------------------------------
// Names
static std::vector<std::string> make_pool() {
    std::vector<std::string> p;
    char b[64];
    for (int i = 0; i < 18; ++i) { std::snprintf(b, sizeof b, "v%d", i); p.push_back(b); }
    for (int i = 0; i < 6; ++i) { std::snprintf(b, sizeof b, "identifier_number_%d_with_tail", i); p.push_back(b); }
    for (int i = 0; i < 6; ++i) { std::snprintf(b, sizeof b, "ns::member%d", i); p.push_back(b); }
    for (int i = 0; i < 4; ++i) { std::string s("z\0", 2); s += static_cast<char>('0' + i); p.push_back(s); }
    for (int i = 0; i < 4; ++i) { std::string s("\xC3\xA9", 2); s += static_cast<char>('a' + i); p.push_back(s); }
    p.push_back("a"); p.push_back("a_"); p.push_back("abcde"); p.push_back("abcdef");
    return p;
}

struct Op { int kind; std::string name; int32_t value; uint8_t type; };   // kind 0 enter, 1 declare

static strata::Status do_op(Table& t, const Op& o) {
    return o.kind == 0 ? t.enter_scope() : t.declare(o.name.data(), o.name.size(), o.value, o.type);
}

// ---------------------------------------------------------------------------------------
// T1
struct T1Counts {
    unsigned long exits, refused;
    unsigned long a1_ok;                       // accessors + every name resolves like the model
    unsigned long a2_digest_eq;                // state_digest equal to a natural fresh replay
    unsigned long idx_differs, cap_differs;    // natural fresh replay has another index / buffer size
    unsigned long b_app, b_eq, b_ident_eq;     // allocated region (index, identifiers, undo) vs natural fresh
    unsigned long c_app, c_eq;                 // every supplied word vs natural fresh (same buffer size)
    unsigned long d_digest_eq, d_region_eq, d_literal_eq, d_diff_outside_gap;   // vs fresh with the same index size
    unsigned long d_total;
    unsigned long gap_words, gap_residue, exits_with_residue, reserved_ok, tail_ok, freed_index_zero;
    unsigned long peak_differs, rebuilds_differs, longest_differs;
    T1Counts() { std::memset(this, 0, sizeof *this); }
};
static T1Counts g_all;

static void t1_compare(Inst& a, const std::vector<Op>& script, const Options& opt, const ReferenceModel& model,
                       const std::vector<std::string>& pool, T1Counts& c) {
    ++c.exits;
    const Stats sa = a.t->stats();
    const size_t cap_a = sa.capacity_bytes / 4;
    const size_t idx_a = sa.index_bytes / 4, itop_a = sa.ident_bytes / 4, undo_a = sa.undo_bytes / 4;
    const uint32_t* pa = a.base();

    // fresh table #1: natural replay with the same Options and the same starting buffer
    Inst n;
    if (a.growable) make_growable(n, opt); else make_fixed(n, a.bytes, opt);
    bool ok = n.t->valid();
    for (size_t i = 0; ok && i < script.size(); ++i) {
        strata::Status s = do_op(*n.t, script[i]);
        ok = (s == strata::kOk || s == strata::kRedeclared);
    }
    CHECK(ok);
    // fresh table #2: same buffer size, index forced to the original's size (bounded, never rebuilt)
    Inst d;
    Options od = opt;
    od.index_slots = static_cast<uint32_t>(idx_a);
    od.max_probe = opt.max_probe;
    od.alloc = 0; od.free = 0; od.realloc = 0; od.user = 0;
    make_fixed(d, cap_a * 4, od);
    bool okd = d.t->valid();
    for (size_t i = 0; okd && i < script.size(); ++i) {
        strata::Status s = do_op(*d.t, script[i]);
        okd = (s == strata::kOk || s == strata::kRedeclared);
    }
    CHECK(okd);
    if (!ok || !okd) return;

    // (a) logical equality
    bool a1 = a.t->size() == model.live() && a.t->depth() == model.depth() && sa.live_identifiers == model.distinct() &&
              n.t->size() == a.t->size() && n.t->depth() == a.t->depth() &&
              n.t->stats().live_identifiers == sa.live_identifiers &&
              n.t->stats().ident_bytes == sa.ident_bytes && n.t->stats().undo_bytes == sa.undo_bytes;
    for (size_t i = 0; a1 && i < pool.size(); ++i) {
        int32_t v1 = -1, v2 = -1, v3 = -1; uint8_t t1 = 0, t2 = 0, t3 = 0;
        bool f1 = a.t->resolve(pool[i].data(), pool[i].size(), &v1, &t1);
        bool f2 = n.t->resolve(pool[i].data(), pool[i].size(), &v2, &t2);
        bool f3 = model.resolve(pool[i], &v3, &t3);
        if (f1 != f2 || f1 != f3 || (f1 && (v1 != v2 || v1 != v3 || t1 != t2 || t1 != t3))) a1 = false;
    }
    CHECK(a1); c.a1_ok += a1;
    CHECK(a.t->check_invariants());
    if (a.t->state_digest() == n.t->state_digest()) ++c.a2_digest_eq;
    const Stats sn = n.t->stats();
    if (sa.peak_used_bytes != sn.peak_used_bytes) ++c.peak_differs;
    if (sa.rebuilds != sn.rebuilds) ++c.rebuilds_differs;
    if (sa.longest_probe != sn.longest_probe) ++c.longest_differs;

    // (b) allocated region
    const size_t cap_n = sn.capacity_bytes / 4, idx_n = sn.index_bytes / 4;
    const uint32_t* pn = n.base();
    const bool same_idx = idx_n == idx_a, same_cap = cap_n == cap_a;
    if (!same_idx) ++c.idx_differs;
    if (!same_cap) ++c.cap_differs;
    // identifier stack (without its reserved word 0): relative references only, so it never depends on idx or cap
    bool ident_eq = std::memcmp(pa + idx_a + 1, pn + idx_n + 1, (itop_a - 1) * 4) == 0;
    if (ident_eq) ++c.b_ident_eq;
    if (same_idx) {
        ++c.b_app;
        bool eq = std::memcmp(pa, pn, idx_a * 4) == 0 && ident_eq &&
                  std::memcmp(pa + cap_a - undo_a, pn + cap_n - undo_a, undo_a * 4) == 0;
        if (eq) ++c.b_eq;
    }
    // (c) every supplied word
    if (same_cap) {
        ++c.c_app;
        if (a.total_words() == n.total_words() && std::memcmp(pa, pn, a.total_words() * 4) == 0) ++c.c_eq;
    }
    // (d) forced index size
    ++c.d_total;
    const uint32_t* pd = d.base();
    if (a.t->state_digest() == d.t->state_digest()) ++c.d_digest_eq;
    bool region = std::memcmp(pa, pd, idx_a * 4) == 0 && std::memcmp(pa + idx_a + 1, pd + idx_a + 1, (itop_a - 1) * 4) == 0 &&
                  std::memcmp(pa + cap_a - undo_a, pd + cap_a - undo_a, undo_a * 4) == 0;
    CHECK(region); c.d_region_eq += region;
    bool literal = a.total_words() == d.total_words() && std::memcmp(pa, pd, a.total_words() * 4) == 0;
    if (literal) ++c.d_literal_eq;
    size_t outside = 0;
    for (size_t i = 0; i < a.total_words() && i < d.total_words(); ++i)
        if (pa[i] != pd[i] && !(i >= idx_a + itop_a && i < cap_a - undo_a)) ++outside;
    CHECK(outside == 0); c.d_diff_outside_gap += outside != 0;
    CHECK(a.t->state_digest() == d.t->state_digest());

    // dead data: is the gap between the identifier stack and the undo stack cleared?
    size_t residue = 0, gap = cap_a - idx_a - itop_a - undo_a;
    for (size_t i = idx_a + itop_a; i < cap_a - undo_a; ++i) if (pa[i] != kFill) ++residue;
    c.gap_words += gap; c.gap_residue += residue; c.exits_with_residue += residue != 0;
    // the reserved word (identifier region word 0) is never written; the tail bytes beyond cap are never touched
    if (pa[idx_a] == kFill) ++c.reserved_ok;
    bool tail = true;
    for (size_t i = cap_a; i < a.total_words(); ++i) if (pa[i] != kFill) tail = false;
    if (!a.growable && tail) ++c.tail_ok;
    if (a.growable) ++c.tail_ok;
}

static void t1_run(const char* label, bool growable, size_t bytes, const Options& opt, int seqs, int ops) {
    const std::vector<std::string> pool = make_pool();
    T1Counts c;
    for (int sq = 0; sq < seqs; ++sq) {
        Inst a;
        if (growable) make_growable(a, opt); else make_fixed(a, bytes, opt);
        CHECK(a.t->valid());
        ReferenceModel model;
        std::vector<Op> script;
        std::vector<size_t> scope_start;
        for (int i = 0; i < ops; ++i) {
            const uint32_t r = rnd() % 100;
            const size_t depth = model.depth();
            if (r < 22 && depth < 14) {
                Op o = {0, "", 0, 0};
                if (a.t->enter_scope() == strata::kOk) { model.enter(); scope_start.push_back(script.size()); script.push_back(o); }
                else ++c.refused;
            } else if (r < 44 && depth > 0) {
                CHECK(a.t->exit_scope() == strata::kOk);
                model.exit();
                script.resize(scope_start.back());
                scope_start.pop_back();
                t1_compare(a, script, opt, model, pool, c);
            } else {
                Op o = {1, pool[rnd() % pool.size()], static_cast<int32_t>(rnd()), static_cast<uint8_t>(rnd())};
                strata::Status s = do_op(*a.t, o);
                if (s == strata::kOk || s == strata::kRedeclared) {
                    CHECK(model.declare(o.name, o.value, o.type) == static_cast<int>(s));
                    script.push_back(o);
                } else {
                    ++c.refused;
                }
            }
        }
        while (model.depth() > 0) {
            CHECK(a.t->exit_scope() == strata::kOk);
            model.exit();
            script.resize(scope_start.back());
            scope_start.pop_back();
            t1_compare(a, script, opt, model, pool, c);
        }
    }
    std::printf("  %-34s exits %-6lu refused ops %-6lu | (a1) %lu/%lu  (a2) %lu/%lu | (b) idx-equal %lu/%lu, ident-only %lu/%lu |"
                " (c) %lu/%lu | (d) digest %lu/%lu region %lu/%lu literal %lu/%lu\n",
                label, c.exits, c.refused, c.a1_ok, c.exits, c.a2_digest_eq, c.exits, c.b_eq, c.b_app, c.b_ident_eq, c.exits,
                c.c_eq, c.c_app, c.d_digest_eq, c.d_total, c.d_region_eq, c.d_total, c.d_literal_eq, c.d_total);
    std::printf("  %-34s natural replay has another index size at %lu exits, another buffer size at %lu; peak/rebuilds/longest_probe differ at %lu/%lu/%lu;"
                " gap residue %lu of %lu words (%lu exits); reserved word intact %lu/%lu; bytes beyond cap intact %lu/%lu; diffs outside gap in (d): %lu\n",
                "", c.idx_differs, c.cap_differs, c.peak_differs, c.rebuilds_differs, c.longest_differs, c.gap_residue, c.gap_words,
                c.exits_with_residue, c.reserved_ok, c.exits, c.tail_ok, c.exits, c.d_diff_outside_gap);
    // sums
    T1Counts& g = g_all;
    g.exits += c.exits; g.refused += c.refused; g.a1_ok += c.a1_ok; g.a2_digest_eq += c.a2_digest_eq;
    g.idx_differs += c.idx_differs; g.cap_differs += c.cap_differs;
    g.b_app += c.b_app; g.b_eq += c.b_eq; g.b_ident_eq += c.b_ident_eq; g.c_app += c.c_app; g.c_eq += c.c_eq;
    g.d_total += c.d_total; g.d_digest_eq += c.d_digest_eq; g.d_region_eq += c.d_region_eq; g.d_literal_eq += c.d_literal_eq;
    g.d_diff_outside_gap += c.d_diff_outside_gap; g.gap_words += c.gap_words; g.gap_residue += c.gap_residue;
    g.exits_with_residue += c.exits_with_residue; g.reserved_ok += c.reserved_ok; g.tail_ok += c.tail_ok;
    CHECK(c.a1_ok == c.exits);
    CHECK(c.b_eq == c.b_app);            // allocated region equal whenever the index has the same size
    CHECK(c.b_ident_eq == c.exits);      // the identifier stack never depends on index or buffer size
    CHECK(c.d_digest_eq == c.d_total && c.d_region_eq == c.d_total);
    CHECK(c.reserved_ok == c.exits && c.tail_ok == c.exits);
}

static void t1_dead_bytes_demo() {
    std::printf("  dead-byte demonstration (bounded, 16 slots, 64 words):\n");
    std::vector<uint32_t> buf(64, kFill);
    Options o; o.index_slots = 16;
    Table t(&buf[0], 256, o);
    t.declare("x", 1, 1, 0);                 // depth 0: record at ident ref 1 (3 words), undo word buf[63]
    t.enter_scope();                         // mark at buf[61..62]
    t.declare("x", 1, 2, 2);                 // shadow: 3-word undo entry at buf[58..60], record updated in place
    t.declare("abc", 3, 3, 3);               // new name: record at ref 4 (buf[20..22]) + 1-word undo entry buf[57]
    uint32_t slot = 99;
    for (uint32_t i = 0; i < 16; ++i) if ((buf[i] & 0xFFFFFFu) == 4) slot = i;
    CHECK(slot != 99 && buf[57] == slot);
    uint32_t rec[3], und[7];
    for (int i = 0; i < 3; ++i) rec[i] = buf[20 + i];
    for (int i = 0; i < 7; ++i) und[i] = buf[57 + i];
    t.exit_scope();
    CHECK(buf[slot] == 0);                                                   // the index slot is emptied
    for (int i = 0; i < 3; ++i) CHECK(buf[20 + i] == rec[i]);                // dead record not cleared
    for (int i = 0; i < 7; ++i) CHECK(buf[57 + i] == und[i]);                // dead undo entries and mark not cleared
    CHECK(rec[0] == 3u && und[0] == slot);
    std::printf("    after exit_scope(): freed index slot -> 0 (cleared); dead identifier record words [%08x %08x %08x] kept;\n"
                "    dead undo words (slot entry, shadow entry x3, mark x2, earlier slot entry) kept: %08x %08x %08x %08x %08x %08x %08x -> freed bytes are NOT cleared\n",
                rec[0], rec[1], rec[2], und[0], und[1], und[2], und[3], und[4], und[5], und[6]);
}

static void test_T1() {
    std::printf("T1 whole-buffer state equality after every scope exit\n");
    Options o;
    t1_run("fixed 4096 B, packed", false, 4096, o, 60, 500);
    Options r; r.pack_names = false;
    t1_run("fixed 4099 B, raw, 3 tail bytes", false, 4099, r, 60, 500);
    Options sp; sp.sparse_index = true;
    t1_run("fixed 6000 B, sparse index", false, 6000, sp, 60, 500);
    Options b1; b1.index_slots = 64;
    t1_run("bounded 64 slots, 2048 B", false, 2048, b1, 60, 500);
    Options sm;
    t1_run("fixed 640 B (refusals occur)", false, 640, sm, 80, 500);
    Options sm2; sm2.index_slots = 16; sm2.max_probe = 3;
    t1_run("bounded 16 slots, probe 3, 512 B", false, 512, sm2, 80, 500);
    Options b2; b2.index_slots = 32; b2.max_probe = 6; b2.keyed = true; b2.key[0] = 0xA1B2C3D4u; b2.key[1] = 0x01234567u;
    t1_run("bounded 32 slots, probe 6, keyed", false, 2048, b2, 60, 500);
    Options g1; g1.initial_bytes = 128;
    t1_run("growable 128 B, shrink on", true, 0, g1, 60, 500);
    Options g2; g2.initial_bytes = 64; g2.shrink = false; g2.sparse_index = true; g2.pack_names = false;
    t1_run("growable 64 B, no shrink, sparse, raw", true, 0, g2, 60, 500);
    Options g3; g3.initial_bytes = 128; g3.max_bytes = 8192; g3.keyed = true; g3.key[0] = 7; g3.key[1] = 9;
    t1_run("growable <= 8 KiB, keyed", true, 0, g3, 60, 500);
    t1_dead_bytes_demo();
    const T1Counts& g = g_all;
    std::printf("  TOTAL exits %lu\n", g.exits);
    std::printf("  (a) logical state (size, depth, distinct names, every name resolves as in the model and in the fresh table; invariants): holds %lu/%lu  -> ALWAYS\n", g.a1_ok, g.exits);
    std::printf("      digest equal to the natural fresh replay: %lu/%lu  (differs exactly when index or buffer size differs: index differs at %lu, buffer differs at %lu)\n",
                g.a2_digest_eq, g.exits, g.idx_differs, g.cap_differs);
    std::printf("  (b) allocated region (index + identifier stack + undo stack, reserved word excluded): equal in %lu/%lu exits where the index has the same size -> ALWAYS then;\n"
                "      the identifier stack alone is equal in %lu/%lu exits regardless of index or buffer size; index words and slot undo entries are not comparable across index sizes\n",
                g.b_eq, g.b_app, g.b_ident_eq, g.exits);
    std::printf("  (c) literally every supplied word vs the natural fresh table (same buffer size only): equal in %lu/%lu -> NOT always (dead data in the free gap)\n", g.c_eq, g.c_app);
    std::printf("  (d) vs fresh bounded table with the same index size and buffer size: digest %lu/%lu, allocated region %lu/%lu -> ALWAYS; literal every word %lu/%lu;\n"
                "      words that differ outside the free gap between the stacks: %lu exits\n",
                g.d_digest_eq, g.d_total, g.d_region_eq, g.d_total, g.d_literal_eq, g.d_total, g.d_diff_outside_gap);
    std::printf("  free gap after exits: %lu of %lu words still hold non-fill (dead) data (%.1f%%), in %lu of %lu exits; reserved identifier word 0 never written: %lu/%lu; bytes beyond the used words untouched: %lu/%lu\n",
                g.gap_residue, g.gap_words, g.gap_words ? 100.0 * static_cast<double>(g.gap_residue) / static_cast<double>(g.gap_words) : 0.0,
                g.exits_with_residue, g.exits, g.reserved_ok, g.exits, g.tail_ok, g.exits);
}

// ---------------------------------------------------------------------------------------
// T2
struct Image {
    std::vector<uint32_t> w;
    Stats s;
    uint64_t digest;
    size_t depth, size;
    bool valid;
};
static bool stats_eq(const Stats& a, const Stats& b) {
    return a.capacity_bytes == b.capacity_bytes && a.used_bytes == b.used_bytes && a.peak_used_bytes == b.peak_used_bytes &&
           a.index_bytes == b.index_bytes && a.ident_bytes == b.ident_bytes && a.undo_bytes == b.undo_bytes &&
           a.live_declarations == b.live_declarations && a.live_identifiers == b.live_identifiers && a.depth == b.depth &&
           a.rebuilds == b.rebuilds && a.longest_probe == b.longest_probe;
}
static void snap(const Inst& in, Image& im) {
    const uint32_t* p = in.base();
    im.w.assign(p, p + in.total_words());
    im.s = in.t->stats();
    im.digest = in.t->state_digest();
    im.depth = in.t->depth(); im.size = in.t->size(); im.valid = in.t->valid();
}
static bool unchanged(const Inst& in, const Image& im) {
    if (in.total_words() != im.w.size()) return false;
    return std::memcmp(in.base(), &im.w[0], im.w.size() * 4) == 0 && stats_eq(in.t->stats(), im.s) &&
           in.t->state_digest() == im.digest && in.t->depth() == im.depth && in.t->size() == im.size && in.t->valid() == im.valid;
}

static unsigned long g_refusals_checked = 0, g_status_seen[8];
static void note_refusal(strata::Status s) { ++g_refusals_checked; if (s < 0 && -s < 8) ++g_status_seen[-s]; }

static std::vector<std::string> t2_pool() {
    std::vector<std::string> p;
    for (int n = 1; n <= 9; ++n) {                       // packed names of 1..9 words
        std::string s;
        for (int i = 0; i < 5 * n; ++i) s += static_cast<char>('a' + (i + n) % 26);
        p.push_back(s);
        p.push_back(s.substr(0, s.size() - 2 > 0 ? s.size() - 2 : 1));
    }
    p.push_back(std::string());                          // empty
    p.push_back(std::string(256, 'q'));                  // too long
    p.push_back(std::string(255, 'r'));                  // longest
    p.push_back("x::y"); p.push_back(std::string("n\0l", 3));
    return p;
}

static void t2_random_sweep(const char* label, const Options& base, size_t cap_from, size_t cap_to, bool degenerate) {
    const std::vector<std::string> pool = t2_pool();
    unsigned long refusals = 0, nomem = 0, other = 0, ops = 0;
    Table::degenerate_hash() = degenerate;
    for (size_t cap = cap_from; cap <= cap_to; ++cap) {
        for (int sc = 0; sc < 24; ++sc) {
            Inst in;
            make_fixed(in, cap * 4 + (sc % 4), base);    // odd byte counts too
            if (!in.t->valid()) continue;
            Image im;
            for (int i = 0; i < 70; ++i) {
                snap(in, im);
                const uint32_t r = rnd() % 100;
                strata::Status s;
                if (r < 22) s = in.t->enter_scope();
                else if (r < 40) s = in.t->exit_scope();
                else { const std::string& nm = pool[rnd() % pool.size()]; s = in.t->declare(nm.data(), nm.size(), static_cast<int32_t>(i), static_cast<uint8_t>(i)); }
                ++ops;
                if (s < 0) {
                    ++refusals; if (s == strata::kNoMemory) ++nomem; else ++other;
                    note_refusal(s);
                    CHECK(unchanged(in, im));
                }
            }
            CHECK(in.t->check_invariants());
        }
    }
    Table::degenerate_hash() = false;
    std::printf("  %-44s caps %zu..%zu words: %lu ops, %lu refusals (no memory %lu, other %lu), all atomic\n", label, cap_from, cap_to, ops, refusals, nomem, other);
}

// exact thresholds in bounded mode: the verdict of each probe is predicted from the stats alone
static void t2_exact_thresholds() {
    Options o; o.index_slots = 16;
    unsigned long probes = 0, exact_fit = 0, one_short = 0, refused = 0, accepted = 0;
    for (size_t cap = 32; cap <= 150; ++cap) {
        for (int k = 0; k <= 45; ++k) {
            for (int cls = 0; cls < 13; ++cls) {
                Inst in;
                make_fixed(in, cap * 4, o);
                // fill script: decl s0; enter; then a mix of enters and declarations of 1..4 name words
                in.t->declare("s0", 1, 0, 0);
                in.t->enter_scope();
                for (int i = 0; i < k; ++i) {
                    if (i % 4 == 3) { in.t->enter_scope(); continue; }
                    std::string nm;
                    const int len = 1 + (i * 7) % 20;
                    for (int j = 0; j < len; ++j) nm += static_cast<char>('a' + (i + j) % 26);
                    in.t->declare(nm.data(), nm.size(), i, 0);
                }
                const Stats st = in.t->stats();
                const long free_w = static_cast<long>((st.capacity_bytes - st.used_bytes) / 4);
                const bool load_ok = (st.live_identifiers + 1) * 4 <= 16 * 3;
                long need = 0; bool must_succeed_regardless = false;
                std::string nm;
                strata::Status s;
                Image im; snap(in, im);
                if (cls == 0) { need = 2; s = in.t->enter_scope(); }
                else if (cls <= 8) {                      // new name of `cls` words
                    nm.assign(static_cast<size_t>(cls) * 5, 'Z');
                    for (size_t j = 0; j < nm.size(); ++j) nm[j] = static_cast<char>('A' + (j * 3 + static_cast<size_t>(cls)) % 26);
                    nm += "_";  nm.resize(static_cast<size_t>(cls) * 5);
                    nm[0] = 'U';
                    need = 2 + cls + 1;
                    s = in.t->declare(nm.data(), nm.size(), 5, 0);
                } else if (cls == 9) { need = 3; s = in.t->declare("s0", 1, 77, 0); }                          // shadow
                else if (cls == 10) { must_succeed_regardless = true; s = in.t->declare("s0", 1, 78, 0); in.t->exit_scope(); s = strata::kOk; }   // placeholder
                else if (cls == 11) { s = in.t->declare("", 0, 1, 0); need = -1; }
                else { s = in.t->declare(std::string(256, 'k').data(), 256, 1, 0); need = -1; }
                if (cls == 10) continue;
                ++probes;
                if (need > 0) {
                    const bool ok_expected = free_w >= need && (cls == 0 || cls == 9 || load_ok);
                    // a name that is already visible (class 9) needs no index slot; the new-name classes do
                    CHECK((s == strata::kOk) == ok_expected);
                    if (!ok_expected) CHECK(s == strata::kNoMemory);
                    if (free_w == need) ++exact_fit;
                    if (free_w == need - 1) ++one_short;
                }
                if (s < 0) { ++refused; note_refusal(s); CHECK(unchanged(in, im)); } else ++accepted;
                (void)must_succeed_regardless;
            }
        }
    }
    std::printf("  exact thresholds (bounded 16 slots): %lu probes at caps 32..150 words, %lu accepted, %lu refused (all atomic); "
                "probes with free == need: %lu (all accepted), free == need-1: %lu (all refused)\n", probes, accepted, refused, exact_fit, one_short);
}

static void t2_growable() {
    const std::vector<std::string> pool = t2_pool();
    unsigned long refusals = 0, ops = 0, injected = 0;
    for (size_t maxb = 128; maxb <= 1500; maxb += 4) {
        for (int sc = 0; sc < 3; ++sc) {
            Options o; o.initial_bytes = 128; o.max_bytes = maxb; o.shrink = sc != 1; o.sparse_index = sc == 2;
            Inst in;
            make_growable(in, o);
            if (!in.t->valid()) continue;
            Image im;
            for (int i = 0; i < 90; ++i) {
                snap(in, im);
                const uint32_t r = rnd() % 100;
                strata::Status s;
                if (r < 20) s = in.t->enter_scope();
                else if (r < 38) s = in.t->exit_scope();
                else { const std::string& nm = pool[rnd() % pool.size()]; s = in.t->declare(nm.data(), nm.size(), i, static_cast<uint8_t>(i)); }
                ++ops;
                if (s < 0) { ++refusals; note_refusal(s); CHECK(unchanged(in, im)); }
            }
            CHECK(in.t->check_invariants());
        }
    }
    // allocator failure injected at every call ordinal
    for (long fail = 1; fail <= 12; ++fail) {
        Options o; o.initial_bytes = 128; o.shrink = true;
        Inst in;
        in.tr.fail_at = 0;
        make_growable(in, o);
        in.tr.fail_at = in.tr.calls + fail;      // fail the fail-th later allocation call
        Image im;
        for (int i = 0; i < 200; ++i) {
            snap(in, im);
            const uint32_t* before = in.tr.cur;
            const std::string& nm = pool[static_cast<size_t>(i) % pool.size()];
            strata::Status s = (i % 5 == 4) ? in.t->enter_scope() : in.t->declare(nm.data(), nm.size(), i, 0);
            ++ops;
            if (s < 0) { ++refusals; ++injected; note_refusal(s); CHECK(in.tr.cur == before); CHECK(unchanged(in, im)); }
        }
    }
    std::printf("  growable (budget sweep 128..1500 B step 4, 3 variants, + allocator failure at call 1..12): %lu ops, %lu refusals (%lu from injected failures), all atomic\n", ops, refusals, injected);
}

static const char* sname(strata::Status s) {
    switch (s) {
    case strata::kOk: return "kOk"; case strata::kRedeclared: return "kRedeclared"; case strata::kNoMemory: return "kNoMemory";
    case strata::kNameTooLong: return "kNameTooLong"; case strata::kEmptyName: return "kEmptyName"; case strata::kNoScope: return "kNoScope";
    case strata::kTooDeep: return "kTooDeep"; case strata::kProbeLimit: return "kProbeLimit";
    }
    return "?";
}

static strata::Status atomic_call(Inst& in, int what, const std::string& nm) {
    Image im; snap(in, im);
    strata::Status s = what == 0 ? in.t->enter_scope() : what == 1 ? in.t->exit_scope() : in.t->declare(nm.data(), nm.size(), 1, 1);
    if (s < 0) { note_refusal(s); CHECK(unchanged(in, im)); }
    return s;
}

static void t2_depth_and_precedence() {
    std::printf("  status precedence when several limits apply at once (each row: observed status; refusals verified atomic by memcmp):\n");
    std::printf("    %-62s %s\n", "situation", "status");
    // memory exhaustion helper: bounded 16 slots, 32 words: idx 16, itop 1, free 15 -> 'a' (4 words) + 5 enters (10) leaves 1
    Options bo; bo.index_slots = 16;
    {   // roomy and exhausted tables
        Inst full; make_fixed(full, 128, bo);
        for (int i = 0; i < 5; ++i) full.t->enter_scope();
        full.t->declare("a", 1, 1, 0);
        const Stats st = full.t->stats();
        CHECK(st.capacity_bytes - st.used_bytes == 4);     // 1 word free
        Inst roomy; make_fixed(roomy, 4096, bo);
        roomy.t->declare("a", 1, 1, 0);
        struct Row { const char* label; strata::Status s; } rows[20]; int nr = 0;
        rows[nr].label = "empty name, memory available"; rows[nr++].s = atomic_call(roomy, 2, "");
        rows[nr].label = "empty name AND no memory"; rows[nr++].s = atomic_call(full, 2, "");
        rows[nr].label = "name of 256 bytes, memory available"; rows[nr++].s = atomic_call(roomy, 2, std::string(256, 'a'));
        rows[nr].label = "name of 256 bytes AND no memory"; rows[nr++].s = atomic_call(full, 2, std::string(256, 'a'));
        rows[nr].label = "new valid name AND no memory"; rows[nr++].s = atomic_call(full, 2, "bb");
        rows[nr].label = "redeclare in current scope AND no memory (needs nothing)"; rows[nr++].s = atomic_call(full, 2, "a");
        rows[nr].label = "enter_scope AND no memory (needs 2 words, 1 free)"; rows[nr++].s = atomic_call(full, 0, "");
        {   // shadowing needs 3 words
            Inst sh; make_fixed(sh, 132, bo);
            sh.t->declare("a", 1, 1, 0); sh.t->enter_scope();
            while (true) { const Stats s2 = sh.t->stats(); if ((s2.capacity_bytes - s2.used_bytes) / 4 <= 2) break; sh.t->enter_scope(); }
            const Stats s2 = sh.t->stats();
            rows[nr].label = "shadow declaration, 2 words free (needs 3)"; rows[nr++].s = atomic_call(sh, 2, "a");
            CHECK((s2.capacity_bytes - s2.used_bytes) / 4 == 2);
        }
        {   // invalid table
            Inst bad; make_fixed(bad, 124, bo);
            CHECK(!bad.t->valid());
            rows[nr].label = "invalid table (31 words) AND empty name"; rows[nr++].s = atomic_call(bad, 2, "");
            rows[nr].label = "invalid table AND exit_scope"; rows[nr++].s = atomic_call(bad, 1, "");
        }
        rows[nr].label = "exit_scope at the outermost scope"; rows[nr++].s = atomic_call(roomy, 1, "");
        for (int i = 0; i < nr; ++i) std::printf("    %-62s %s\n", rows[i].label, sname(rows[i].s));
        CHECK(rows[0].s == strata::kEmptyName && rows[1].s == strata::kEmptyName);
        CHECK(rows[2].s == strata::kNameTooLong && rows[3].s == strata::kNameTooLong);
        CHECK(rows[4].s == strata::kNoMemory && rows[5].s == strata::kRedeclared && rows[6].s == strata::kNoMemory && rows[7].s == strata::kNoMemory);
        CHECK(rows[8].s == strata::kNoMemory && rows[9].s == strata::kNoMemory && rows[10].s == strata::kNoScope);
    }
    // probe limit: every name hashes to slot 0 (test hook), limit 1
    {
        Options po; po.index_slots = 16; po.max_probe = 1;
        Table::degenerate_hash() = true;
        Inst room; make_fixed(room, 4096, po);
        room.t->declare("a", 1, 1, 0);
        strata::Status roomy_s = atomic_call(room, 2, "bb");
        Inst tight; make_fixed(tight, 128, po);
        tight.t->declare("a", 1, 1, 0);
        for (int i = 0; i < 5; ++i) tight.t->enter_scope();
        strata::Status tight_s = atomic_call(tight, 2, "bb");
        Inst shadow; make_fixed(shadow, 4096, po);
        shadow.t->declare("a", 1, 1, 0); shadow.t->enter_scope();
        strata::Status shadow_s = atomic_call(shadow, 2, "a");
        // load limit (12 of 16 slots) reached with the probe limit also exhausted
        Options po2; po2.index_slots = 16; po2.max_probe = 16;
        Inst load; make_fixed(load, 4096, po2);
        for (int i = 0; i < 12; ++i) { char b[16]; std::snprintf(b, sizeof b, "n%d", i); load.t->declare(b, std::strlen(b), i, 0); }
        strata::Status load_s = atomic_call(load, 2, "n99");
        Table::degenerate_hash() = false;
        std::printf("    %-62s %s\n", "probe limit hit, memory available", sname(roomy_s));
        std::printf("    %-62s %s\n", "probe limit hit AND no memory (needs 4 words, 1 free)", sname(tight_s));
        std::printf("    %-62s %s\n", "shadow declaration of a visible name under a probe limit", sname(shadow_s));
        std::printf("    %-62s %s\n", "index load limit (12 of 16 slots), memory available", sname(load_s));
        CHECK(roomy_s == strata::kProbeLimit && tight_s == strata::kNoMemory && shadow_s == strata::kOk && load_s == strata::kNoMemory);
    }
    // nesting depth
    {
        const size_t exact = 16 + 1 + 2 * static_cast<size_t>(strata::kMaxDepth);   // words: index + reserved + 16383 marks
        for (int variant = 0; variant < 3; ++variant) {
            const size_t words = variant == 0 ? exact - 1 : variant == 1 ? exact : exact + 100;
            Options o;
            Inst in; make_fixed(in, words * 4, o);
            int entered = 0;
            strata::Status s = strata::kOk;
            while (entered < strata::kMaxDepth + 2) {
                s = in.t->enter_scope();
                if (s != strata::kOk) break;
                ++entered;
            }
            // one more refused call, checked for atomicity
            strata::Status again = atomic_call(in, 0, "");
            std::printf("    depth sweep, buffer %zu words (%s): entered %d scopes, then %s (repeat: %s)\n", words,
                        variant == 0 ? "one word short of 16383 marks" : variant == 1 ? "exactly 16383 marks, 0 free" : "100 spare words",
                        entered, sname(s), sname(again));
            if (variant == 0) CHECK(entered == strata::kMaxDepth - 1 + 0 && s == strata::kNoMemory);
            if (variant == 1) CHECK(entered == strata::kMaxDepth && s == strata::kTooDeep);   // too deep AND no memory
            if (variant == 2) CHECK(entered == strata::kMaxDepth && s == strata::kTooDeep);
            CHECK(in.t->check_invariants());
            // a declaration at maximum depth, if memory allows, reports that depth; then unwind
            if (variant == 2) {
                CHECK(in.t->declare("deep", 4, 99, 3) == strata::kOk);
                CHECK(in.t->declared_in_current_scope("deep", 4));
                for (int i = 0; i < strata::kMaxDepth; ++i) CHECK(in.t->exit_scope() == strata::kOk);
                CHECK(in.t->depth() == 0 && in.t->size() == 0 && in.t->check_invariants());
            }
        }
        std::printf("    (the 16383rd enter needs 2 words: with exactly 16383 marks of room, the 16384th enter is both too deep and out of memory -> kTooDeep)\n");
    }
}

static void test_T2() {
    std::printf("T2 refusal atomicity at every reservation boundary\n");
    Options o;
    t2_random_sweep("fixed packed", o, 32, 220, false);
    Options r; r.pack_names = false;
    t2_random_sweep("fixed raw", r, 32, 220, false);
    Options sp; sp.sparse_index = true;
    t2_random_sweep("fixed sparse index", sp, 32, 220, false);
    Options b; b.index_slots = 16;
    t2_random_sweep("bounded 16 slots", b, 32, 220, false);
    Options bp; bp.index_slots = 16; bp.max_probe = 2;
    t2_random_sweep("bounded 16 slots, probe 2, all names collide", bp, 32, 220, true);
    Options bk; bk.index_slots = 32; bk.max_probe = 3; bk.keyed = true; bk.key[0] = 11; bk.key[1] = 13;
    t2_random_sweep("bounded 32 slots, probe 3, keyed", bk, 48, 240, false);
    t2_exact_thresholds();
    t2_growable();
    t2_depth_and_precedence();
    std::printf("  refusals checked in T2 by direct memcmp of the whole buffer + Options/accessors: %lu (no memory %lu, name too long %lu, empty %lu, no scope %lu, too deep %lu, probe limit %lu)\n",
                g_refusals_checked, g_status_seen[1], g_status_seen[2], g_status_seen[3], g_status_seen[4], g_status_seen[5], g_status_seen[6]);
}

// ---------------------------------------------------------------------------------------
// T3
static int code_of(unsigned char c) {      // independent re-statement of the 6-bit alphabet
    if (c >= 'a' && c <= 'z') return 1 + (c - 'a');
    if (c >= 'A' && c <= 'Z') return 27 + (c - 'A');
    if (c >= '0' && c <= '9') return 53 + (c - '0');
    if (c == '_') return 63;
    return 0;
}
static bool all_ident(const std::string& s) {
    for (size_t i = 0; i < s.size(); ++i) if (!code_of(static_cast<unsigned char>(s[i]))) return false;
    return true;
}
static std::string unpack(const strata::Key& k, size_t len) {
    static const char alpha[] = "\0abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
    std::string s;
    for (size_t i = 0; i < len; ++i) s += alpha[(k.w[i / 5] >> (6 * (i % 5))) & 63u];
    return s;
}

static void t3_roundtrip(bool pack) {
    Options o; o.pack_names = pack; o.shrink = false;
    Table t(o);
    strata::Key k;
    unsigned long n = 0;
    for (size_t len = 1; len <= 255; ++len) {
        std::string s;
        for (size_t i = 0; i < len; ++i) s += static_cast<char>("abcXYZ019_"[(i * 7 + len) % 10]);
        CHECK(t.make_key(s.data(), s.size(), k) == strata::kOk);
        if (pack) {
            CHECK(k.n == (len + 4) / 5 && ((k.meta >> 7) & 1) == 0 && ((k.meta >> 8) & 3) == 0 && (k.meta & 0x7F) == k.n);
            CHECK(unpack(k, len) == s);
            // unused code slots of the last word are 0, and bits 30-31 are 0
            const size_t used = len - 5 * (k.n - 1);
            CHECK((k.w[k.n - 1] >> (6 * used)) == 0 && (k.w[k.n - 1] >> 30) == 0);
        } else {
            CHECK(k.n == (len + 3) / 4 && ((k.meta >> 7) & 1) == 1 && ((k.meta >> 8) & 3) == (len & 3) && (k.meta & 0x7F) == k.n);
            std::string back(len, '\0');
            std::memcpy(&back[0], k.w, len);
            CHECK(back == s);
            for (size_t i = len; i < k.n * 4; ++i) CHECK(reinterpret_cast<const unsigned char*>(k.w)[i] == 0);
        }
        CHECK(t.declare(s.data(), s.size(), static_cast<int32_t>(len), static_cast<uint8_t>(len)) == strata::kOk);
        ++n;
    }
    for (size_t len = 1; len <= 255; ++len) {
        std::string s;
        for (size_t i = 0; i < len; ++i) s += static_cast<char>("abcXYZ019_"[(i * 7 + len) % 10]);
        int32_t v = 0; uint8_t ty = 0;
        CHECK(t.resolve(s.data(), s.size(), &v, &ty) && v == static_cast<int32_t>(len) && ty == static_cast<uint8_t>(len));
    }
    CHECK(t.size() == n && t.check_invariants());
}

static void t3_special() {
    for (int pack = 0; pack < 2; ++pack) {
        Options o; o.pack_names = pack != 0; o.shrink = false;
        Table t(o);
        // names that differ only by trailing padding / length
        std::vector<std::string> names;
        const char* fam[] = {"a", "a_", "a__", "a___", "a____", "a_____", "aa", "aaaa", "aaaaa", "aaaaaa", "_", "__", "___", "____", "_____", "______"};
        for (size_t i = 0; i < sizeof fam / sizeof fam[0]; ++i) names.push_back(fam[i]);
        // raw: trailing NUL bytes, and every string over {NUL, 'a'} up to length 8
        for (int len = 1; len <= 8; ++len)
            for (int m = 0; m < (1 << len); ++m) {
                std::string s;
                for (int i = 0; i < len; ++i) s += (m >> i & 1) ? 'a' : '\0';
                bool dup = false;
                for (size_t j = 0; j < sizeof fam / sizeof fam[0]; ++j) if (s == fam[j]) dup = true;
                if (!dup) names.push_back(s);
            }
        // high-bit bytes
        for (int c = 1; c < 256; ++c) { std::string s(1, static_cast<char>(c)); if (!all_ident(s) || true) { bool dup = false; for (size_t j = 0; j < names.size(); ++j) if (names[j] == s) dup = true; if (!dup) names.push_back(s); } }
        for (int c = 128; c < 256; ++c) { std::string s("ab"); s += static_cast<char>(c); s += "de"; names.push_back(s); s = std::string(1, static_cast<char>(c)) + "abcdefghi"; names.push_back(s); }
        size_t expect = 0;
        for (size_t i = 0; i < names.size(); ++i) {
            strata::Status st = t.declare(names[i].data(), names[i].size(), static_cast<int32_t>(i), 0);
            CHECK(st == strata::kOk);   // every one of them is a distinct name
            expect += st == strata::kOk;
        }
        for (size_t i = 0; i < names.size(); ++i) {
            int32_t v = -1;
            CHECK(t.resolve(names[i].data(), names[i].size(), &v) && v == static_cast<int32_t>(i));
        }
        CHECK(t.size() == expect && t.stats().live_identifiers == expect && t.check_invariants());
        if (pack == 0) std::printf("  %zu distinct names (padding families, every string over {NUL,'a'} up to 8 bytes, all single bytes 1..255, high-bit bytes in the middle/front) are all distinct, packed mode\n", names.size());
        else std::printf("  same %zu names, raw mode: all distinct\n", names.size());
        // character code 0 does not exist for identifier characters: every non-identifier byte forces raw
        strata::Key k;
        t.make_key("ab\0de", 5, k);
        if (pack == 0) CHECK(((k.meta >> 7) & 1) == 1);
        t.make_key("abcd\xFF", 5, k);
        if (pack == 0) CHECK(((k.meta >> 7) & 1) == 1);
        // non-identifier byte at every position (full word, partial word) of a 12-byte name -> raw
        if (pack == 0)
            for (size_t pos = 0; pos < 12; ++pos) {
                std::string s(12, 'a'); s[pos] = '-';
                t.make_key(s.data(), s.size(), k);
                CHECK(((k.meta >> 7) & 1) == 1 && k.n == 3 && ((k.meta >> 8) & 3) == 0);
                std::string back(12, '\0'); std::memcpy(&back[0], k.w, 12); CHECK(back == s);
            }
    }
    // maximum length, packed and raw
    for (int pack = 0; pack < 2; ++pack) {
        Options o; o.pack_names = pack != 0;
        Table t(o);
        std::string mx(255, 'M');
        strata::Key k;
        CHECK(t.make_key(mx.data(), 255, k) == strata::kOk);
        CHECK(pack ? (k.n == 51 && ((k.meta >> 7) & 1) == 0) : (k.n == 64 && ((k.meta >> 7) & 1) == 1 && ((k.meta >> 8) & 3) == 3));
        std::string rawmax(255, '\xFE');
        CHECK(t.make_key(rawmax.data(), 255, k) == strata::kOk && k.n == 64 && (k.meta & 0x7F) == 64);
        CHECK(t.declare(mx.data(), 255, 1, 255) == strata::kOk && t.declare(rawmax.data(), 255, 2, 254) == strata::kOk);
        int32_t v = 0; uint8_t ty = 0;
        CHECK(t.resolve(mx.data(), 255, &v, &ty) && v == 1 && ty == 255 && t.resolve(rawmax.data(), 255, &v, &ty) && v == 2 && ty == 254);
        CHECK(t.make_key(mx.data(), 256, k) == strata::kNameTooLong && t.make_key(mx.data(), 0, k) == strata::kEmptyName);
        // type tag 0..255 and extreme values
        for (int ty2 = 0; ty2 < 256; ++ty2) {
            char b[16]; std::snprintf(b, sizeof b, "t%d", ty2);
            const int32_t val = ty2 % 2 ? INT32_MIN + ty2 : INT32_MAX - ty2;
            CHECK(t.declare(b, std::strlen(b), val, static_cast<uint8_t>(ty2)) == strata::kOk);
            int32_t rv = 0; uint8_t rt = 0;
            CHECK(t.resolve(b, std::strlen(b), &rv, &rt) && rv == val && rt == ty2);
        }
        CHECK(t.check_invariants());
    }
}

static void t3_depth() {
    Options o;
    Inst in; make_fixed(in, (16 + 1 + 2 * strata::kMaxDepth + 3 * strata::kMaxDepth + 4 * strata::kMaxDepth + 64) * 4, o);
    CHECK(in.t->valid());
    // at every depth shadow the same name; type = depth & 255; verify all depths and the unwinding
    CHECK(in.t->declare("x", 1, 0, 0) == strata::kOk);
    for (int d = 1; d <= strata::kMaxDepth; ++d) {
        CHECK(in.t->enter_scope() == strata::kOk);
        CHECK(in.t->declare("x", 1, d, static_cast<uint8_t>(d)) == strata::kOk);
        if (d % 2000 == 0) { char b[16]; std::snprintf(b, sizeof b, "d%d", d); CHECK(in.t->declare(b, std::strlen(b), -d, 1) == strata::kOk); }
    }
    CHECK(in.t->depth() == static_cast<size_t>(strata::kMaxDepth));
    CHECK(in.t->enter_scope() == strata::kTooDeep);
    int32_t v = 0; uint8_t ty = 0;
    CHECK(in.t->resolve("x", 1, &v, &ty) && v == strata::kMaxDepth && ty == static_cast<uint8_t>(strata::kMaxDepth));
    CHECK(in.t->declared_in_current_scope("x", 1) && in.t->check_invariants());
    // depth field is 14 bits: the identifier record at maximum depth stores 0x3FFF in meta bits 18-31
    const uint32_t* p = in.base();
    const Stats st = in.t->stats();
    bool found = false;
    for (size_t r = 1; r < st.ident_bytes / 4;) { const uint32_t* rec = p + st.index_bytes / 4 + r; if ((rec[1] >> 18) == 0x3FFFu) found = true; r += 2 + (rec[1] & 0x7F); }
    CHECK(found);
    for (int d = strata::kMaxDepth; d >= 1; --d) {
        CHECK(in.t->exit_scope() == strata::kOk);
        if (d % 3000 == 0) { CHECK(in.t->resolve("x", 1, &v, &ty) && v == d - 1); }
    }
    CHECK(in.t->resolve("x", 1, &v, &ty) && v == 0 && in.t->depth() == 0 && in.t->check_invariants());
    std::printf("  maximum depth %d: 16383 nested scopes with a shadowing declaration at each, kTooDeep at 16384, unwinds exactly; depth field 0x3FFF stored in bits 18-31\n", strata::kMaxDepth);
}

static void t3_layout() {
    std::printf("  stored-word layout verified in a bounded table (16 slots, buffer words %s):\n", "0..63");
    std::vector<uint32_t> buf(64, kFill);
    Options o; o.index_slots = 16;
    Table t(&buf[0], 256, o);
    for (uint32_t i = 0; i < 16; ++i) CHECK(buf[i] == 0);               // index zeroed
    CHECK(buf[16] == kFill);                                              // reserved identifier word 0 never written
    // 1: first declaration of "abc", type 0xA5, value -2, at depth 0
    CHECK(t.declare("abc", 3, -2, 0xA5) == strata::kOk);
    strata::Key k; t.make_key("abc", 3, k);
    uint32_t fp = k.hash >> 24; if (!fp) fp = 1;
    uint32_t slot = k.hash & 15, found = 99;
    for (uint32_t i = 0; i < 16; ++i) if (buf[i]) { CHECK(found == 99); found = i; }
    CHECK(found == slot && buf[slot] == (fp << 24 | 1u));                 // fingerprint | reference (1 = first record)
    CHECK(buf[17] == static_cast<uint32_t>(-2));                          // record word 0: value
    CHECK(buf[18] == (1u | 0xA5u << 10 | 0u << 18));                      // record word 1: 1 name word, packed, len%4 = 0, type, depth 0
    CHECK(buf[19] == static_cast<uint32_t>(code_of('a') | code_of('b') << 6 | code_of('c') << 12));   // record word 2..: packed name
    CHECK(buf[63] == slot);                                               // undo: 1-word entry = index slot of the new name
    std::printf("    index word  = fingerprint(hash>>24, 0 mapped to 1) << 24 | identifier reference (1 = first record), at slot hash & 15: 0x%08x at slot %u\n", buf[slot], slot);
    std::printf("    record      = [value][meta][name words]; meta = n | raw<<7 | (len&3)<<8 | type<<10 | depth<<18: 0x%08x; packed 'abc' = 0x%08x\n", buf[18], buf[19]);
    std::printf("    undo, new name (1 word): index slot %u\n", buf[63]);
}

static void t3_layout_final() {
    std::vector<uint32_t> buf(64, kFill);
    Options o; o.index_slots = 16;
    Table t(&buf[0], 256, o);
    t.declare("abc", 3, -2, 0xA5);          // ident ref 1, 3 words -> itop 4; undo 1 word (slot) at buf[63]
    t.enter_scope();                         // undo 3 words; mark m[0] at buf[61], m[1] at buf[62]
    const uint32_t m0 = buf[61], m1 = buf[62];
    CHECK(m0 == 4u);                         // identifier-stack top at entry
    CHECK(m1 == 0u);                         // previous mark: none
    // shadowing: undo entry is 3 words at buf[58..60]
    t.declare("abc", 3, 55, 0x11);
    // depth is now 1: record meta carries depth 1 in bits 18+, type 0x11 in bits 10-17
    CHECK(buf[17] == 55u && buf[18] == (1u | 0x11u << 10 | 1u << 18));
    CHECK(buf[58] == (1u | 0x01000000u));            // reference | shadow bit (bit 24)
    CHECK(buf[59] == static_cast<uint32_t>(-2));      // hidden value
    CHECK(buf[60] == (0xA5u << 10));                  // hidden type/depth bits (key bits cleared)
    // second scope: previous mark = undo position of the first mark
    t.enter_scope();
    CHECK(buf[56] == 4u && buf[57] == 3u);            // itop at entry (unchanged), previous mark = undo position of mark 1 (3 words from the end)
    std::printf("    shadow undo entry (3 words, lowest address first): [ref | 1<<24 = 0x%08x][hidden value = %d][hidden type<<10|depth<<18 = 0x%08x]\n",
                buf[58], static_cast<int>(buf[59]), buf[60]);
    std::printf("    scope marks: first [itop 4][prev 0]; second [itop %u][prev = undo position of first mark = %u]\n", buf[56], buf[57]);
    // exit restores
    t.exit_scope(); t.exit_scope();
    int32_t v = 0; uint8_t ty = 0;
    CHECK(t.resolve("abc", 3, &v, &ty) && v == -2 && ty == 0xA5 && t.check_invariants());
}

static void t3_max_buffer() {
    // 128 MiB of caller memory offered: only 2^24 - 1 words are used
    const size_t bytes = size_t(128) << 20;
    std::vector<uint32_t> big(bytes / 4, kFill);
    Options o;
    Table t(&big[0], bytes, o);
    const Stats s0 = t.stats();
    CHECK(s0.capacity_bytes == (size_t(0x00FFFFFF)) * 4);
    char b[16];
    unsigned long n = 0;
    strata::Status st = strata::kOk;
    for (uint32_t i = 0; (st = t.declare(b, static_cast<size_t>(std::snprintf(b, sizeof b, "n%07x", i)), static_cast<int32_t>(i), 0)) == strata::kOk; ++i) ++n;
    CHECK(st == strata::kNoMemory);
    const Stats s = t.stats();
    CHECK(s.used_bytes <= s.capacity_bytes);
    CHECK(s.ident_bytes / 4 <= 0x00FFFFFFu);
    bool beyond = true;
    for (size_t i = 0x00FFFFFFu; i < big.size(); ++i) if (big[i] != kFill) { beyond = false; break; }
    CHECK(beyond);
    CHECK(t.check_invariants());
    {   // the 24-bit identifier reference: fill an identifier stack with maximal raw names under a large static index
        Options bo; bo.index_slots = 1u << 19; bo.pack_names = false;
        Table u(&big[0], bytes, bo);
        std::string nm(255, '\x80');
        unsigned long m = 0;
        strata::Status s2 = strata::kOk;
        for (uint32_t i = 0; s2 == strata::kOk; ++i) { std::memcpy(&nm[0], &i, 4); s2 = u.declare(nm.data(), nm.size(), 1, 0); if (s2 == strata::kOk) ++m; }
        const Stats su = u.stats();
        CHECK(s2 == strata::kNoMemory && su.ident_bytes / 4 < 0x00FFFFFFu && u.check_invariants());
        std::printf("  reference range: static index of 2^19 slots, 255-byte raw names (66 words each): %lu names, identifier stack ends at word %zu of the 0xFFFFFF reference range"
                    " (refusal is kNoMemory from the buffer, not from the 24-bit field)\n", m, static_cast<size_t>(su.ident_bytes / 4));
    }
    // smallest buffer that is valid: 32 words; 31 words is not
    std::vector<uint32_t> small(32, kFill);
    Table ok(&small[0], 32 * 4, o), bad(&small[0], 31 * 4, o);
    CHECK(ok.valid() && !bad.valid());
    std::printf("  64 MiB limit: 128 MiB offered, capacity used = %zu bytes = 0x%X words (2^24 - 1, i.e. 64 MiB - 4 B); filled with %lu distinct names until kNoMemory;"
                " identifier stack %zu words (max reference reached %zu of 0xFFFFFF); %zu words beyond the limit untouched\n",
                s.capacity_bytes, 0x00FFFFFFu, n, static_cast<size_t>(s.ident_bytes / 4), static_cast<size_t>(s.ident_bytes / 4), big.size() - 0x00FFFFFFu);
}

static void test_T3() {
    std::printf("T3 encoding tests\n");
    const uint32_t one = 1;
    CHECK(*reinterpret_cast<const unsigned char*>(&one) == 1);   // the raw-name and keyed-hash paths assume little endian
    std::printf("  host is %s-endian (raw names are copied with memcpy; HalfSipHash agreement is claimed for little-endian hosts only)\n",
                *reinterpret_cast<const unsigned char*>(&one) == 1 ? "little" : "big");
    t3_roundtrip(true);
    t3_roundtrip(false);
    std::printf("  round trip of lengths 1..255, packed and raw: encoding, padding bits, declare/resolve, type and value\n");
    t3_special();
    t3_depth();
    t3_layout();
    t3_layout_final();
    t3_max_buffer();
}

// T4: a name prepared once with make_key() gives the same results as the plain call, in every mode.
static void test_T4() {
    const char* names[] = {"a", "count", "counter_1", "long_identifier_name_x", "x-y", "caf\xc3\xa9", "A9_", "zz"};
    for (int mode = 0; mode < 3; ++mode) {
        std::vector<uint32_t> b1(4096), b2(4096);
        strata::Options o;
        if (mode == 1) { o.index_slots = 256; o.max_probe = 64; }
        if (mode == 2) { o.keyed = true; o.key[0] = 0x1234; o.key[1] = 0x5678; o.index_slots = 256; o.max_probe = 64; }
        strata::Table plain(&b1[0], b1.size() * 4, o), prep(&b2[0], b2.size() * 4, o);
        strata::Key k;
        for (int round = 0; round < 3; ++round) {
            for (size_t i = 0; i < sizeof names / sizeof *names; ++i) {
                const char* n = names[i];
                const size_t len = std::strlen(n);
                CHECK(prep.make_key(n, len, k) == strata::kOk);
                int32_t v1 = -1, v2 = -2;
                uint8_t t1 = 0, t2 = 0;
                CHECK(plain.resolve(n, len, &v1, &t1) == prep.resolve(k, &v2, &t2));
                CHECK(v1 == v2 || v1 == -1);
                CHECK(plain.declare(n, len, static_cast<int32_t>(i + round), static_cast<uint8_t>(i)) == prep.declare(k, static_cast<int32_t>(i + round), static_cast<uint8_t>(i)));
                CHECK(plain.resolve(n, len, &v1, &t1) && prep.resolve(k, &v2, &t2) && v1 == v2 && t1 == t2);
            }
            CHECK(plain.enter_scope() == prep.enter_scope());
        }
        CHECK(plain.state_digest() == prep.state_digest());
        CHECK(prep.check_invariants());
    }
}

int main(int argc, char** argv) {
    if (argc > 1) g_rng ^= static_cast<uint64_t>(std::strtoull(argv[1], 0, 0)) * 0x9E3779B97F4A7C15ull;
    test_T1();
    test_T2();
    test_T3();
    test_T4();
    std::printf("%d checks, %d failed\n", g_checks, g_failed);
    return g_failed ? 1 : 0;
}
