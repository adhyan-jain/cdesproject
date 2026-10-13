// Hash-flooding experiments for STRATA.
//
//   hardening --mode flood --out FILE.csv [--reps N]
//       Builds C identifiers that collide in STRATA's default hash for EVERY seed
//       (MurmurHash3 multicollisions in the style of Aumasson and Bernstein, restricted to
//       words that are valid 6-bit packings of identifier characters), checks that they
//       collide, and measures declaring and then looking up N of them against N ordinary
//       names of the same length, for four configurations:
//         default          unkeyed hash, index grows
//         keyed            HalfSipHash-1-3 under a key the generator does not know
//         bounded          unkeyed hash, static index, probe limit
//         bounded_keyed    keyed hash, static index, probe limit
//
//   hardening --mode traces --trace FILE --name LABEL --out FILE.csv
//       Replays a compiler trace in bounded mode (static index sized from a first pass)
//       for probe limits from 4 to 512, with and without the keyed hash: refused declarations,
//       longest probe sequence, wrong lookups against the reference model, peak bytes.
//
//   hardening --mode probes --out FILE.csv [--reps N]
//       How long are insertion probe sequences? For index sizes 2^10, 2^13, 2^16 and load
//       factors 3/8, 1/2, 5/8, 3/4, with the default and the keyed hash: fills an index with
//       random identifiers by linear probing (homes taken from the table's own hash), then
//       measures, for fresh names, how many slots an insertion would examine. Reports the
//       measured probability of exceeding a probe limit L next to the bound
//       rho^L / (1 - rho), rho = a * e^(1 - a), derived in docs/PROBE_LIMIT_ANALYSIS.md.
//
//   hardening --mode names --count N --words W
//       Prints N colliding identifiers of 5*W characters (W even), one per line.
#include <cmath>
#include <cstring>

#include "../include/strata/strata.hpp"
#include "../tests/reference_model.hpp"
#include "common.hpp"

// ---- seed-independent multicollisions of the word mixer --------------------------------
// hash_step(h, k) = rotl(h ^ f(k), 13) * 5 + c, with f(k) = rotl(k * c1, 15) * c2 a bijection.
// Flipping bit 18 of f(k1) flips bit 31 of (h ^ f(k1)) after the rotation; multiplying by 5
// and adding c keeps that difference in bit 31 exactly, for every h. Flipping bit 31 of
// f(k2) in the next word cancels it. So (k1, k2) and (k1', k2') with
// f(k1') = f(k1) ^ 2^18 and f(k2') = f(k2) ^ 2^31 give the same state whatever the seed.
static uint32_t rotl32(uint32_t x, int r) { return (x << r) | (x >> (32 - r)); }
static uint32_t rotr32(uint32_t x, int r) { return (x >> r) | (x << (32 - r)); }
static uint32_t inverse(uint32_t a) {          // multiplicative inverse of an odd number mod 2^32
    uint32_t x = a;
    for (int i = 0; i < 5; ++i) x *= 2u - a * x;
    return x;
}
static const uint32_t C1 = 0xcc9e2d51u, C2 = 0x1b873593u;
static uint32_t f(uint32_t k) { return rotl32(k * C1, 15) * C2; }
static uint32_t f_inverse(uint32_t y) { return rotr32(y * inverse(C2), 15) * inverse(C1); }

// A word is a packing of five identifier characters when its top two bits are clear and
// none of its five 6-bit codes is zero. `lead` also forbids a digit in the first position.
static bool packable(uint32_t w, bool lead) {
    if (w >> 30) return false;
    for (int i = 0; i < 5; ++i) if (((w >> (6 * i)) & 63) == 0) return false;
    uint32_t first = w & 63;
    return !lead || first < 53 || first == 63;
}
static void unpack(uint32_t w, std::string& out) {
    static const char alphabet[] = "\0abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
    for (int i = 0; i < 5; ++i) out.push_back(alphabet[(w >> (6 * i)) & 63]);
}
static uint64_t g_rng = 0x243F6A8885A308D3ull;
static uint32_t rnd32() {
    g_rng ^= g_rng << 13; g_rng ^= g_rng >> 7; g_rng ^= g_rng << 17;
    return static_cast<uint32_t>(g_rng >> 16);
}
struct PairBlock { uint32_t a[2], b[2]; };     // (a[0], b[0]) and (a[1], b[1]) are interchangeable
static PairBlock find_pair_block() {
    PairBlock p;
    for (;;) {
        uint32_t k = rnd32() & 0x3FFFFFFFu;
        if (!packable(k, true)) continue;
        uint32_t k2 = f_inverse(f(k) ^ (1u << 18));
        if (!packable(k2, true)) continue;
        p.a[0] = k; p.a[1] = k2;
        break;
    }
    for (;;) {
        uint32_t k = rnd32() & 0x3FFFFFFFu;
        if (!packable(k, false)) continue;
        uint32_t k2 = f_inverse(f(k) ^ (1u << 31));
        if (!packable(k2, false)) continue;
        p.b[0] = k; p.b[1] = k2;
        break;
    }
    return p;
}
// `count` distinct identifiers of 10 * blocks characters with one common hash.
static std::vector<std::string> colliding_names(size_t count, int blocks) {
    std::vector<PairBlock> pb;
    for (int i = 0; i < blocks; ++i) pb.push_back(find_pair_block());
    std::vector<std::string> out;
    for (size_t n = 0; n < count; ++n) {
        std::string s;
        for (int i = 0; i < blocks; ++i) {
            int bit = static_cast<int>((n >> i) & 1);
            unpack(pb[i].a[bit], s);
            unpack(pb[i].b[bit], s);
        }
        out.push_back(s);
    }
    return out;
}
static std::vector<std::string> ordinary_names(size_t count, size_t len) {
    static const char alphabet[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789";
    std::vector<std::string> out;
    for (size_t n = 0; n < count; ++n) {
        std::string s;
        s.push_back(alphabet[rnd32() % 53]);
        while (s.size() + 8 < len) s.push_back(alphabet[rnd32() % 63]);
        char tail[16];
        std::snprintf(tail, sizeof tail, "%08zu", n);      // makes the names distinct
        s += tail;
        out.push_back(s);
    }
    return out;
}
// The default mixer with an arbitrary seed (the header fixes the seed; this replica is
// used only to show that the collisions do not depend on it).
static uint32_t murmur_words_seeded(const uint32_t* w, uint32_t n, uint32_t meta, uint32_t seed) {
    uint32_t h = seed;
    for (uint32_t i = 0; i < n; ++i) h = strata::detail::hash_step(h, w[i]);
    return strata::detail::hash_finish(h, meta);
}

struct FloodResult { double declare_ns, lookup_ns; size_t refused, longest; bool correct; };

static FloodResult flood_once(const std::vector<std::string>& names, int config, std::vector<uint32_t>& buf) {
    strata::Options o;
    o.keyed = config == 1 || config == 3;
    o.key[0] = 0x6b657931u ^ rnd32();      // drawn at run time: not known when the names were built
    o.key[1] = 0x6b657932u ^ rnd32();
    const bool bounded = config >= 2;
    size_t slots = 16;
    while (slots * 3 < names.size() * 4) slots *= 2;
    if (bounded) { o.index_slots = static_cast<uint32_t>(slots); o.max_probe = 64; }
    strata::Table* t = bounded ? new strata::Table(&buf[0], buf.size() * 4, o) : new strata::Table(o);
    FloodResult r = {0, 0, 0, 0, true};
    std::vector<char> stored(names.size(), 0);
    Clock::time_point t0 = Clock::now();
    for (size_t i = 0; i < names.size(); ++i) {
        strata::Status s = t->declare(names[i].data(), names[i].size(), static_cast<int32_t>(i));
        if (s == strata::kOk) stored[i] = 1; else ++r.refused;
    }
    r.declare_ns = ns_since(t0);
    t0 = Clock::now();
    for (size_t i = 0; i < names.size(); ++i) {
        int32_t v = -1;
        bool found = t->resolve(names[i].data(), names[i].size(), &v);
        if (found != (stored[i] != 0) || (found && v != static_cast<int32_t>(i))) r.correct = false;
    }
    r.lookup_ns = ns_since(t0);
    r.longest = t->stats().longest_probe;
    if (!t->check_invariants()) r.correct = false;
    delete t;
    return r;
}

static int mode_flood(const std::string& out, int reps) {
    FILE* fo = out.empty() ? stdout : std::fopen(out.c_str(), "a");
    if (!fo) return 3;
    if (out.empty() || std::ftell(fo) == 0)
        std::fprintf(fo, "names,name_bytes,input,config,n,declare_ns_median,lookup_ns_median,refused,longest_probe,correct,reps\n");
    static const char* cfg[] = {"default", "keyed", "bounded", "bounded_keyed"};
    const int blocks = 15;                                   // 150-character names, 2^15 of them
    std::vector<std::string> evil_all = colliding_names(32768, blocks);
    std::vector<std::string> plain_all = ordinary_names(32768, 10 * blocks);

    // 1. the names are valid identifiers and really collide, for the built-in seed and others
    strata::Table probe;
    strata::Key k0;
    probe.make_key(evil_all[0].data(), evil_all[0].size(), k0);
    const uint32_t seeds[8] = {0, 1, 0x9747b28cu, 0xdeadbeefu, 0x12345678u, 0xffffffffu, 0x80000000u, 0x0badf00du};
    uint32_t seeded0[8];
    for (int si = 0; si < 8; ++si) seeded0[si] = murmur_words_seeded(k0.w, k0.n, k0.meta, seeds[si]);
    size_t distinct_check = 0;
    for (size_t i = 0; i < evil_all.size(); ++i) {
        strata::Key k;
        if (probe.make_key(evil_all[i].data(), evil_all[i].size(), k) != strata::kOk || (k.meta & 0x80) || k.hash != k0.hash) {
            std::fprintf(stderr, "generated name %zu does not collide\n", i);
            return 4;
        }
        for (int si = 0; si < 8; ++si)
            if (murmur_words_seeded(k.w, k.n, k.meta, seeds[si]) != seeded0[si]) {
                std::fprintf(stderr, "name %zu does not collide under seed %08x\n", i, seeds[si]);
                return 4;
            }
        if (i && evil_all[i] != evil_all[0]) ++distinct_check;
    }
    if (distinct_check != evil_all.size() - 1) { std::fprintf(stderr, "names are not distinct\n"); return 4; }
    std::fprintf(stderr, "verified: %zu distinct identifiers of %zu characters share hash %08x under the built-in seed "
                         "and collide under 8 further seeds; first: %s\n",
                 evil_all.size(), evil_all[0].size(), k0.hash, evil_all[0].c_str());

    std::vector<uint32_t> buf(1u << 22);                     // 16 MiB for the bounded configurations
    for (size_t n = 1024; n <= 32768; n *= 2) {
        for (int input = 0; input < 2; ++input) {
            std::vector<std::string> names((input ? evil_all : plain_all).begin(), (input ? evil_all : plain_all).begin() + static_cast<long>(n));
            for (int c = 0; c < 4; ++c) {
                std::vector<double> d, l;
                FloodResult last = {0, 0, 0, 0, true};
                bool correct = true;
                for (int rep = 0; rep < reps; ++rep) {
                    last = flood_once(names, c, buf);
                    d.push_back(last.declare_ns);
                    l.push_back(last.lookup_ns);
                    correct = correct && last.correct;
                }
                std::sort(d.begin(), d.end());
                std::sort(l.begin(), l.end());
                std::fprintf(fo, "%zu,%zu,%s,%s,%zu,%.0f,%.0f,%zu,%zu,%d,%d\n", n, names[0].size(), input ? "colliding" : "ordinary",
                             cfg[c], n, d[d.size() / 2], l[l.size() / 2], last.refused, last.longest, correct ? 1 : 0, reps);
                std::fflush(fo);
            }
        }
    }
    if (fo != stdout) std::fclose(fo);
    return 0;
}

// ---- compiler traces in bounded mode ------------------------------------------------------
static int mode_traces(const std::string& path, const std::string& name, const std::string& out) {
    Trace tr;
    if (!load_trace(path, tr)) { std::fprintf(stderr, "cannot load trace '%s'\n", path.c_str()); return 2; }
    // first pass, growable table: peak number of distinct visible names and peak bytes per unit
    size_t peak_idents = 0, grow_peak = 0;
    {
        strata::Table* t = new strata::Table();
        for (size_t i = 0; i < tr.ops.size(); ++i) {
            const Op& op = tr.ops[i];
            const std::string& nm = tr.names[op.name];
            switch (op.kind) {
            case OP_ENTER: t->enter_scope(); break;
            case OP_EXIT: t->exit_scope(); break;
            case OP_DECLARE: t->declare(nm.data(), nm.size(), 0); break;
            case OP_LOOKUP: break;
            default: grow_peak = std::max(grow_peak, t->stats().peak_used_bytes); delete t; t = new strata::Table(); break;
            }
            peak_idents = std::max(peak_idents, t->stats().live_identifiers);
        }
        grow_peak = std::max(grow_peak, t->stats().peak_used_bytes);
        delete t;
    }
    uint32_t slots = 16;
    while (static_cast<uint64_t>(slots) * 3 < static_cast<uint64_t>(peak_idents) * 4) slots *= 2;
    FILE* fo = out.empty() ? stdout : std::fopen(out.c_str(), "a");
    if (!fo) return 3;
    if (out.empty() || std::ftell(fo) == 0)
        std::fprintf(fo, "trace,hash,index_slots,max_probe,declares,refused_probe_limit,refused_memory,wrong_lookups,"
                         "longest_probe,peak_used_bytes,growing_index_peak_used_bytes,rebuilds\n");
    std::vector<uint32_t> buf(1u << 22);
    const uint32_t limits[] = {0, 4, 8, 16, 32, 64, 128, 256, 512};
    for (int keyed = 0; keyed < 2; ++keyed) {
        for (size_t li = 0; li < sizeof limits / sizeof limits[0]; ++li) {
            strata::Options o;
            o.index_slots = slots;
            o.max_probe = limits[li];
            o.keyed = keyed != 0;
            o.key[0] = 0x0a1b2c3du;
            o.key[1] = 0x4e5f6071u;
            strata::Table* t = new strata::Table(&buf[0], buf.size() * 4, o);
            ReferenceModel* ref = new ReferenceModel();
            size_t refused_probe = 0, refused_mem = 0, wrong = 0, longest = 0, peak = 0, rebuilds = 0;
            int32_t seq = 0;
            for (size_t i = 0; i < tr.ops.size(); ++i) {
                const Op& op = tr.ops[i];
                const std::string& nm = tr.names[op.name];
                switch (op.kind) {
                case OP_ENTER: if (t->enter_scope() == strata::kOk) ref->enter(); else ++refused_mem; break;
                case OP_EXIT: if (t->exit_scope() == strata::kOk) ref->exit(); break;
                case OP_DECLARE: {
                    strata::Status s = t->declare(nm.data(), nm.size(), seq);
                    if (s == strata::kProbeLimit) ++refused_probe;
                    else if (s == strata::kNoMemory) ++refused_mem;
                    else ref->declare(nm, seq);
                    ++seq;
                    break;
                }
                case OP_LOOKUP: {
                    int32_t a = -1, b = -1;
                    if (!t->resolve(nm.data(), nm.size(), &a)) a = -1;
                    if (!ref->resolve(nm, &b)) b = -1;
                    if (a != b) ++wrong;
                    break;
                }
                default:
                    longest = std::max(longest, t->stats().longest_probe);
                    peak = std::max(peak, t->stats().peak_used_bytes);
                    rebuilds += t->stats().rebuilds;
                    delete t; delete ref;
                    t = new strata::Table(&buf[0], buf.size() * 4, o);
                    ref = new ReferenceModel();
                    seq = 0;
                    break;
                }
            }
            longest = std::max(longest, t->stats().longest_probe);
            peak = std::max(peak, t->stats().peak_used_bytes);
            rebuilds += t->stats().rebuilds;
            delete t; delete ref;
            std::fprintf(fo, "%s,%s,%u,%u,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu\n", name.c_str(), keyed ? "halfsiphash13" : "murmur3",
                         slots, limits[li], tr.count[OP_DECLARE], refused_probe, refused_mem, wrong, longest, peak, grow_peak, rebuilds);
        }
    }
    if (fo != stdout) std::fclose(fo);
    return 0;
}

// ---- insertion probe lengths against the analytical bound --------------------------------
static std::string random_identifier() {
    static const char alphabet[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789";
    std::string s;
    s.push_back(alphabet[rnd32() % 53]);
    const uint32_t len = 6 + rnd32() % 19;                 // 6 .. 24 characters
    while (s.size() < len) s.push_back(alphabet[rnd32() % 63]);
    return s;
}
static int mode_probes(const std::string& out, int trials) {
    FILE* fo = out.empty() ? stdout : std::fopen(out.c_str(), "a");
    if (!fo) return 3;
    const uint32_t limits[] = {8, 16, 32, 64, 128, 256, 512};
    const int nl = static_cast<int>(sizeof limits / sizeof limits[0]);
    if (out.empty() || std::ftell(fo) == 0) {
        std::fprintf(fo, "hash,index_slots,load,names,trials,samples,mean_probes,knuth_mean,longest");
        for (int i = 0; i < nl; ++i) std::fprintf(fo, ",measured_gt_%u,bound_gt_%u", limits[i], limits[i]);
        std::fprintf(fo, "\n");
    }
    const uint32_t sizes[] = {1u << 10, 1u << 13, 1u << 16};
    const double loads[] = {0.375, 0.5, 0.625, 0.75};
    for (int keyed = 0; keyed < 2; ++keyed)
        for (size_t si = 0; si < 3; ++si)
            for (size_t ai = 0; ai < 4; ++ai) {
                const uint32_t m = sizes[si], n = static_cast<uint32_t>(loads[ai] * m), mask = m - 1;
                const size_t fresh_per_trial = 20000;
                unsigned long long over[16] = {0}, samples = 0, total = 0;
                uint32_t longest = 0;
                std::vector<char> used;
                used.assign(m, 0);
                for (int tr = 0; tr < trials; ++tr) {
                    strata::Options o;
                    o.keyed = keyed != 0;
                    o.key[0] = rnd32();
                    o.key[1] = rnd32();
                    strata::Table t(o);                      // used only for its hash of a name
                    std::fill(used.begin(), used.end(), 0);
                    strata::Key k;
                    for (uint32_t i = 0; i < n; ++i) {       // names repeat with negligible probability
                        std::string s = random_identifier();
                        t.make_key(s.data(), s.size(), k);
                        uint32_t j = k.hash & mask;
                        while (used[j]) j = (j + 1) & mask;
                        used[j] = 1;
                    }
                    for (size_t f = 0; f < fresh_per_trial; ++f) {
                        std::string s = random_identifier();
                        t.make_key(s.data(), s.size(), k);
                        uint32_t j = k.hash & mask, steps = 1;
                        while (used[j]) { j = (j + 1) & mask; ++steps; }
                        total += steps;
                        ++samples;
                        if (steps > longest) longest = steps;
                        for (int i = 0; i < nl; ++i) if (steps > limits[i]) ++over[i];
                    }
                }
                const double a = static_cast<double>(n) / m, rho = a * std::exp(1.0 - a);
                std::fprintf(fo, "%s,%u,%.3f,%u,%d,%llu,%.3f,%.3f,%u", keyed ? "halfsiphash13" : "murmur3", m, a, n, trials, samples,
                             static_cast<double>(total) / static_cast<double>(samples), 0.5 * (1.0 + 1.0 / ((1.0 - a) * (1.0 - a))), longest);
                for (int i = 0; i < nl; ++i)
                    std::fprintf(fo, ",%.3e,%.3e", static_cast<double>(over[i]) / static_cast<double>(samples),
                                 std::pow(rho, static_cast<double>(limits[i])) / (1.0 - rho));
                std::fprintf(fo, "\n");
                std::fflush(fo);
            }
    if (fo != stdout) std::fclose(fo);
    return 0;
}

int main(int argc, char** argv) {
    std::string mode, path, name, out;
    int reps = 5, words = 4;
    size_t count = 16;
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string a = argv[i], v = argv[i + 1];
        if (a == "--mode") mode = v; else if (a == "--trace") path = v; else if (a == "--name") name = v;
        else if (a == "--out") out = v; else if (a == "--reps") reps = std::atoi(v.c_str());
        else if (a == "--count") count = static_cast<size_t>(std::atol(v.c_str()));
        else if (a == "--words") words = std::atoi(v.c_str());
        else { std::fprintf(stderr, "unknown option %s\n", a.c_str()); return 2; }
    }
    if (reps < 1) reps = 1;
    if (mode == "flood") return mode_flood(out, reps);
    if (mode == "traces") return mode_traces(path, name.empty() ? path : name, out);
    if (mode == "probes") return mode_probes(out, reps);
    if (mode == "names") {
        if (words < 2 || words > 50 || (words & 1) || count == 0 || (words / 2 < 40 && count > (static_cast<size_t>(1) << (words / 2)))) {
            std::fprintf(stderr, "--words must be even, 2..50, and --count at most 2^(words/2)\n");
            return 2;
        }
        std::vector<std::string> n = colliding_names(count, words / 2);
        for (size_t i = 0; i < n.size(); ++i) std::printf("%s\n", n[i].c_str());
        return 0;
    }
    std::fprintf(stderr, "usage: hardening --mode flood|traces|probes|names ...\n");
    return 2;
}
