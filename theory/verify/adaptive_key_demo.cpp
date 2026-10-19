// Illustration (not a timing attack): what a probe-length oracle buys against a PERSISTENT key.
// The attacker never sees the key.  Oracle: after declaring `anchor` and then a candidate in a fresh table
// with the secret key, Stats::longest_probe == 2 iff the candidate's home slot equals the anchor's home slot
// (an idealised stand-in for a timing side channel).  The attacker keeps the colliders it learns and the
// victim declares them first in later tables.  Compared: same key, and a fresh independent key per table.
// Usage: adaptive_key_demo m L honest seeds c1 c2 ...
#include "strata/strata.hpp"
#include <cstdio>
#include <cstdlib>
#include <random>
#include <string>
#include <vector>
using namespace strata;
static std::string rname(std::mt19937_64& r, int len = 12) {
    std::string s; for (int i = 0; i < len; i++) s += (char)('a' + r() % 26); return s;
}
int main(int argc, char** argv) {
    if (argc < 6) return 2;
    const uint32_t m = atoi(argv[1]), L = atoi(argv[2]);
    const int honest = atoi(argv[3]), seeds = atoi(argv[4]);
    std::vector<int> cs; for (int i = 5; i < argc; ++i) cs.push_back(atoi(argv[i]));
    int cmax = 0; for (size_t i = 0; i < cs.size(); ++i) if (cs[i] > cmax) cmax = cs[i];
    std::vector<uint32_t> buf(1 << 16);
    std::printf("m=%u L=%u honest names=%d seeds=%d\n", m, L, honest, seeds);
    std::printf("colliders  queries/collider   refused(same key)   refused(fresh key)   refused(random names, same count)\n");
    std::vector<std::vector<double> > same(cs.size()), fresh(cs.size()), ctrl(cs.size());
    double qpc = 0;
    for (int sd = 0; sd < seeds; ++sd) {
        std::mt19937_64 rng(1000 + sd);
        uint32_t key[2] = {(uint32_t)rng(), (uint32_t)rng()};
        auto opts = [&](const uint32_t* k) { Options o; o.index_slots = m; o.max_probe = L; o.keyed = true; o.key[0] = k[0]; o.key[1] = k[1]; return o; };
        const std::string anchor = "anchor_name";
        std::vector<std::string> coll; unsigned long long q = 0;
        while ((int)coll.size() < cmax) {
            std::string c = rname(rng); Table t(buf.data(), buf.size() * 4, opts(key));
            t.declare(anchor.data(), anchor.size(), 1); t.declare(c.data(), c.size(), 2); ++q;
            if (t.stats().longest_probe == 2) coll.push_back(c);
        }
        qpc += (double)q / cmax;
        for (size_t ci = 0; ci < cs.size(); ++ci) {
            auto run = [&](const uint32_t* k, bool use_learned) {
                Table t(buf.data(), buf.size() * 4, opts(k));
                t.declare(anchor.data(), anchor.size(), 1);
                std::mt19937_64 r2(777 + sd);
                for (int i = 0; i < cs[ci]; ++i) {
                    if (use_learned) t.declare(coll[i].data(), coll[i].size(), 2);
                    else { std::string x = rname(r2); t.declare(x.data(), x.size(), 2); }
                }
                int refused = 0;
                for (int i = 0; i < honest; ++i) { std::string h = "honest_" + rname(rng, 10); if (t.declare(h.data(), h.size(), 3) == kProbeLimit) ++refused; }
                return 100.0 * refused / honest;
            };
            uint32_t k2[2] = {(uint32_t)rng(), (uint32_t)rng()};
            same[ci].push_back(run(key, true)); fresh[ci].push_back(run(k2, true)); ctrl[ci].push_back(run(key, false));
        }
    }
    auto mean = [](const std::vector<double>& v) { double s = 0; for (size_t i = 0; i < v.size(); ++i) s += v[i]; return s / v.size(); };
    auto mx = [](const std::vector<double>& v) { double s = 0; for (size_t i = 0; i < v.size(); ++i) if (v[i] > s) s = v[i]; return s; };
    for (size_t ci = 0; ci < cs.size(); ++ci)
        std::printf("%9d  %15.0f   %8.2f%% (max %5.2f%%)   %8.2f%% (max %5.2f%%)   %8.2f%%\n", cs[ci], qpc / seeds,
                    mean(same[ci]), mx(same[ci]), mean(fresh[ci]), mx(fresh[ci]), mean(ctrl[ci]));
    return 0;
}
