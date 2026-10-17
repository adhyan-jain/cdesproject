// End-to-end check of the exact refusal law against the real strata::Table (keyed, static index).
//
// Per trial: random key; table A (no probe limit) receives n random distinct names, then one more fresh
// name whose probe count is read from the index (test-only access to private members).  The law concerns
// P(steps > L).  Table B (same key, max_probe = L) receives the same names: while no earlier probe has
// exceeded L, B must be in exactly A's state (state_digest) and B's status for the last name must be
// kProbeLimit iff steps > L.  Usage: law_vs_table m n L trials seed
#include <cstdio>
#include <cstdlib>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <random>
#include <vector>
#define private public
#include "strata/strata.hpp"
#undef private
using namespace strata;
int main(int argc, char** argv) {
    if (argc < 6) return 2;
    const uint32_t m = atoi(argv[1]), n = atoi(argv[2]), L = atoi(argv[3]);
    const long trials = atol(argv[4]);
    std::mt19937_64 rng(strtoull(argv[5], 0, 10));
    std::vector<uint32_t> ba(1 << 15), bb(1 << 15);
    long exceed = 0, clean = 0, mismatch = 0;
    char nm[32];
    for (long t = 0; t < trials; ++t) {
        Options oa; oa.index_slots = m; oa.keyed = true; oa.key[0] = (uint32_t)rng(); oa.key[1] = (uint32_t)rng();
        Options ob = oa; ob.max_probe = L;
        Table A(ba.data(), ba.size() * 4, oa), B(bb.data(), bb.size() * 4, ob);
        bool diverged = false;
        for (uint32_t i = 0; i < n; ++i) {
            int len = snprintf(nm, sizeof nm, "n%llx", (unsigned long long)rng());
            A.declare(nm, len, 1);
            Status sb = B.declare(nm, len, 1);
            if (sb == kProbeLimit) diverged = true;
        }
        int len = snprintf(nm, sizeof nm, "f%llx", (unsigned long long)rng());
        const uint64_t dA = A.state_digest(), dB = B.state_digest();
        Key k; A.make_key(nm, len, k);
        const uint32_t home = k.hash & (m - 1);
        A.declare(nm, len, 1);
        uint32_t slot = home, steps = 1;
        while (!((A.w_[slot] & 0x00FFFFFFu) && (A.w_[slot] >> 24) == ((k.hash >> 24) ? (k.hash >> 24) : 1u)
                 && A.ident(A.w_[slot] & 0x00FFFFFFu)[2] == k.w[0])) { slot = (slot + 1) & (m - 1); ++steps; }
        const bool over = steps > L;
        if (over) ++exceed;
        if (!diverged) {
            ++clean;
            if (dA != dB) ++mismatch;                           // B must equal A while no refusal has occurred
            Status sb = B.declare(nm, len, 1);
            if ((sb == kProbeLimit) != over) ++mismatch;
        }
    }
    std::printf("%ld %ld %ld\n", exceed, clean, mismatch);
    return 0;
}
