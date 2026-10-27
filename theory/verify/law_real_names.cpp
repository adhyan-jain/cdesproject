// The exact refusal law against REAL identifiers and the DEFAULT (unkeyed) hash.
//
//   law_real_names NAMES.txt m n L trials seed
//
// law_vs_table.cpp draws random names under a fresh random key, so every hash looks random by construction.
// Here the hash is the library's default mixer and the names are the distinct identifiers of a compiler
// trace: a trial inserts n names drawn at random without replacement into an unlimited table of m slots
// (the (P1) fill), then offers one more name from the rest and records whether it needs more than L probes
// (the event that a table with limit L would refuse it). Prints "exceeded trials".
// The trials share one pool of names, so they are not independent: the observed rate is compared with the
// law, and a z-score is not meaningful.
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <random>
#include <string>
#include <vector>

#define private public   // the probe count is read from the index words, as in law_vs_table.cpp
#include "strata/strata.hpp"

int main(int argc, char** argv) {
    if (argc < 7) return 2;
    std::ifstream in(argv[1]);
    const uint32_t m = atoi(argv[2]), n = atoi(argv[3]), L = atoi(argv[4]);
    const long trials = atol(argv[5]);
    std::mt19937_64 rng(strtoull(argv[6], 0, 10));
    std::vector<std::string> pool;
    for (std::string s; std::getline(in, s);) if (!s.empty()) pool.push_back(s);
    if (pool.size() <= n) { std::fprintf(stderr, "pool of %zu names is too small for n=%u\n", pool.size(), n); return 3; }
    std::vector<uint32_t> buf(std::max<size_t>(1 << 15, static_cast<size_t>(m) * 10));
    long exceeded = 0;
    for (long t = 0; t < trials; ++t) {
        for (uint32_t i = 0; i <= n; ++i) std::swap(pool[i], pool[i + rng() % (pool.size() - i)]);   // partial shuffle
        strata::Options o;
        o.index_slots = m;                                    // default (unkeyed) hash, no probe limit
        strata::Table A(buf.data(), buf.size() * 4, o);
        for (uint32_t i = 0; i < n; ++i) A.declare(pool[i].data(), pool[i].size(), 1);
        const std::string& f = pool[n];
        strata::Key k;
        A.make_key(f.data(), f.size(), k);
        const uint32_t home = k.hash & (m - 1);
        // probes needed by the fresh name = distance from its home to the first empty slot, plus one
        uint32_t steps = 1, slot = home;
        while (A.w_[slot] != 0) { slot = (slot + 1) & (m - 1); ++steps; }
        if (steps > L) ++exceeded;
    }
    std::printf("%ld %ld\n", exceeded, trials);
    return 0;
}
