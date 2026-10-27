// End-to-end check of the exact refusal law against the real strata::Table (keyed, static index).
//
// Per trial: random key; table A (no probe limit) receives n random distinct names, then one more fresh
// name whose probe count is read from the index (test-only access to private members).  The law concerns
// P(steps > L).  Table B (same key, max_probe = L) receives the same names: while no earlier probe has
// exceeded L, B must be in exactly A's state (state_digest) and B's status for the last name must be
// kProbeLimit iff steps > L.  Usage: law_vs_table m n L trials seed
#include <algorithm>
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
    const size_t words = std::max<size_t>(1 << 15, static_cast<size_t>(m) * 10);   // room for n names of 6 words each
    std::vector<uint32_t> ba(words), bb(words);
    // Trial accounting for the process distinctions of the manuscript (Section VI-B):
    //   (i)/(ii) table A: unconstrained fill of n names, then the first capped query     -> exceed / trials
    //   (iii)    fill conditioned on no refusal in table B                                -> exceed_clean / clean
    //   (iv)     table B keeps inserting after refusals; final query on every trial       -> b_final_refused / trials
    // coupling_violations counts trials in which B refused the final name although A's probe count did not
    // exceed L; the domination argument (B's occupied set is contained in A's) says it is zero.
    long exceed = 0, clean = 0, mismatch = 0, exceed_clean = 0, trials_with_refusal = 0, b_fill_refusals = 0,
         b_final_refused = 0, b_final_refused_dirty = 0, coupling_violations = 0, b_stored = 0, b_stored_clean = 0;
    char nm[32];
    for (long t = 0; t < trials; ++t) {
        Options oa; oa.index_slots = m; oa.keyed = true; oa.key[0] = (uint32_t)rng(); oa.key[1] = (uint32_t)rng();
        Options ob = oa; ob.max_probe = L;
        Table A(ba.data(), ba.size() * 4, oa), B(bb.data(), bb.size() * 4, ob);
        bool diverged = false;
        long refused_here = 0;
        for (uint32_t i = 0; i < n; ++i) {
            int len = snprintf(nm, sizeof nm, "n%llx", (unsigned long long)rng());
            A.declare(nm, len, 1);
            Status sb = B.declare(nm, len, 1);
            if (sb == kProbeLimit) { diverged = true; ++refused_here; }
        }
        b_fill_refusals += refused_here;
        if (diverged) ++trials_with_refusal;
        b_stored += (long)n - refused_here;
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
        const bool refused = B.declare(nm, len, 1) == kProbeLimit;   // process (iv): asked on every trial
        if (refused) { ++b_final_refused; if (diverged) ++b_final_refused_dirty; }
        if (refused && !over) ++coupling_violations;
        if (!diverged) {
            ++clean; b_stored_clean += n;
            if (over) ++exceed_clean;
            if (dA != dB) ++mismatch;                           // B must equal A while no refusal has occurred
            if (refused != over) ++mismatch;
        }
    }
    std::printf("%ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld\n", exceed, clean, mismatch, exceed_clean, trials_with_refusal,
                b_fill_refusals, b_final_refused, b_final_refused_dirty, coupling_violations, b_stored, b_stored_clean);
    return 0;
}
