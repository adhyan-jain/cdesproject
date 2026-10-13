// Checks strata::detail::halfsiphash13 against the reference HalfSipHash implementation
// (https://github.com/veorq/SipHash, halfsiphash.c, CC0), which is fetched by
// scripts/audit/halfsiphash_check.sh and compiled with cROUNDS=1, dROUNDS=3.
// Little-endian hosts only: the header hashes name words in host order.
#include <cstdio>
#include <cstring>

#include "../include/strata/strata.hpp"

extern "C" int halfsiphash(const void* in, const size_t inlen, const void* k, uint8_t* out, const size_t outlen);

int main() {
    uint64_t rng = 0x9E3779B97F4A7C15ull;
    int bad = 0;
    const int cases = 200000;
    for (int c = 0; c < cases; ++c) {
        uint32_t w[65], key[2];
        rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
        uint32_t n = 1 + static_cast<uint32_t>(rng >> 20) % 64;
        for (uint32_t i = 0; i <= n; ++i) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; w[i] = static_cast<uint32_t>(rng >> 16); }
        for (int i = 0; i < 2; ++i) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; key[i] = static_cast<uint32_t>(rng >> 16); }
        const uint32_t meta = w[n];
        uint8_t out[4];
        halfsiphash(w, (n + 1) * 4, key, out, 4);
        uint32_t ref;
        std::memcpy(&ref, out, 4);
        if (ref != strata::detail::halfsiphash13(w, n, meta, key[0], key[1])) ++bad;
    }
    std::printf("halfsiphash13 against the reference implementation: %d cases, %d mismatches\n", cases, bad);
    return bad ? 1 : 0;
}
