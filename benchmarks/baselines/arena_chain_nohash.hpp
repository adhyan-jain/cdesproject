// ArenaChainNoHash (layout C1) - ArenaChain (layout C0) with the stored hash word removed.
//
// Reviewer experiment R13. IDENTICAL to arena_chain.hpp (same hash function, same load factor
// 1, same bucket doubling, same 1.5x growth, same refusal-without-state-change rules, same
// 64-byte-bisectable fixed buffer) except for the entry layout:
//
//   C0 entry  [next in chain][hash][value][len | depth << 16][name bytes, zero padded] = 4 + wc
//   C1 entry  [next in chain]      [value][len | depth << 16][name bytes, zero padded] = 3 + wc
//
// Wherever C0 reads the stored hash, C1 recomputes it from the stored (zero-padded) name words:
//   * exit_scope (to find the bucket of every popped entry)
//   * rebuild of the bucket array when it doubles (to re-link every entry)
// and the chain-walk compare drops the e[1]==h pre-filter, so a chain probe compares the
// length and then the name words (the extra cost of not storing the hash).
//
// Original header comment of arena_chain.hpp follows.
//
// ArenaChain - a conventional allocator-free scoped symbol table, written as a strong
// baseline for STRATA. It is the classic compiler design (chained hash table over an arena
// of symbol entries, popped at scope exit; cf. lcc and Tiny C Compiler's symbol stacks):
//
//   word 0                                                          word cap
//   | bucket heads | entry stack ->        free        <- scope marks |
//
//   entry  [next in chain][value][len | depth << 16][name bytes, zero padded]
//
// One entry per DECLARATION (the name is stored each time, unpacked). A new entry is
// linked at the head of its bucket, so the first match in a chain is the innermost
// declaration; leaving a scope unlinks and pops that scope's entries.
//
// It shares STRATA's storage discipline on purpose - one buffer, caller-supplied or grown
// by realloc in 1.5x steps, no exceptions, refusal with no state change when full - so that
// a comparison isolates the data-structure differences (interning, undo entries, packing,
// open addressing) from the mere absence of an allocator.
#ifndef CDES_ARENA_CHAIN_NOHASH_HPP
#define CDES_ARENA_CHAIN_NOHASH_HPP

#include <cstdint>
#include <cstdlib>
#include <cstring>

namespace arena_chain_nohash {

typedef void* (*ReallocFn)(void* p, size_t bytes);

class Table {
public:
    Table(void* buffer, size_t bytes) : w_(static_cast<uint32_t*>(buffer)), cap_(static_cast<uint32_t>(bytes / 4)), fixed_(true), realloc_(0) {
        valid_ = w_ != 0 && cap_ >= 32;
        if (valid_) reset();
    }
    explicit Table(ReallocFn r = 0, size_t initial_bytes = 1024) : w_(0), cap_(0), fixed_(false), realloc_(r ? r : default_realloc) {
        w_ = static_cast<uint32_t*>(realloc_(0, initial_bytes));
        valid_ = w_ != 0;
        if (valid_) { cap_ = static_cast<uint32_t>(initial_bytes / 4); reset(); }
    }
    ~Table() { if (!fixed_ && w_) realloc_(w_, 0); }

    bool enter_scope() {
        if (!valid_ || marks_ >= 0xFFFF || !ensure(1, 0)) return false;
        ++marks_;
        w_[cap_ - marks_] = etop_;
        return true;
    }
    bool exit_scope() {
        if (!valid_ || marks_ == 0) return false;
        uint32_t floor = w_[cap_ - marks_];
        for (uint32_t r = floor; r < etop_;) {       // unlink every entry of the scope
            const uint32_t* e = entry(r);
            uint32_t b = hash_stored(e) & (nb_ - 1);   // C1: recomputed, not stored
            while (w_[b] >= floor) w_[b] = entry(w_[b])[0];
            r += 3 + words(e[2] & 0xFFFF);
            --live_;
        }
        etop_ = floor;
        --marks_;
        return true;
    }
    // 0 new, 1 redeclared in this scope, -1 refused (nothing changed)
    int declare(const char* name, size_t len, int32_t value) {
        if (!valid_ || len == 0 || len > 255) return -1;
        uint32_t key[64], n = words(len), h = hash(name, len, key, n);
        for (uint32_t r = w_[h & (nb_ - 1)]; r; r = entry(r)[0]) {
            uint32_t* e = entry(r);
            if ((e[2] & 0xFFFF) == len && std::memcmp(e + 3, key, n * 4) == 0) {
                if ((e[2] >> 16) != marks_) break;   // innermost match is in an outer scope: shadow it
                e[1] = static_cast<uint32_t>(value);
                return 1;
            }
        }
        if (!ensure(3 + n, 1)) return -1;
        uint32_t r = etop_, b = h & (nb_ - 1);
        uint32_t* e = entry(r);
        e[0] = w_[b];
        e[1] = static_cast<uint32_t>(value);
        e[2] = static_cast<uint32_t>(len) | marks_ << 16;
        std::memcpy(e + 3, key, n * 4);
        w_[b] = r;
        etop_ += 3 + n;
        ++live_;
        touch();
        return 0;
    }
    bool resolve(const char* name, size_t len, int32_t* value) const {
        if (!valid_ || len == 0 || len > 255) return false;
        uint32_t key[64], n = words(len), h = hash(name, len, key, n);
        for (uint32_t r = w_[h & (nb_ - 1)]; r; r = entry(r)[0]) {
            const uint32_t* e = entry(r);
            if ((e[2] & 0xFFFF) == len && std::memcmp(e + 3, key, n * 4) == 0) {
                *value = static_cast<int32_t>(e[1]);
                return true;
            }
        }
        return false;
    }
    size_t peak_used_bytes() const { return static_cast<size_t>(peak_) * 4; }
    size_t size() const { return live_; }

private:
    Table(const Table&);
    Table& operator=(const Table&);
    static void* default_realloc(void* p, size_t n) { if (n == 0) { std::free(p); return 0; } return std::realloc(p, n); }
    static uint32_t words(size_t len) { return static_cast<uint32_t>((len + 3) / 4); }
    static uint32_t rotl(uint32_t x, int r) { return (x << r) | (x >> (32 - r)); }
    // Same mixer as STRATA (MurmurHash3, 32-bit) over the zero-padded name words.
    static uint32_t hash(const char* name, size_t len, uint32_t* key, uint32_t n) {
        key[n - 1] = 0;
        std::memcpy(key, name, len);
        return hash_words(key, len, n);
    }
    // Hash of an entry from the name words stored in it (the zero padding is part of the key,
    // exactly as in hash() above, so the result is bit-identical to the one computed on insert).
    static uint32_t hash_stored(const uint32_t* e) {
        uint32_t len = e[2] & 0xFFFF;
        return hash_words(e + 3, len, words(len));
    }
    static uint32_t hash_words(const uint32_t* key, size_t len, uint32_t n) {
        uint32_t h = 0x9747b28cu;
        for (uint32_t i = 0; i < n; ++i) {
            uint32_t k = key[i] * 0xcc9e2d51u;
            k = rotl(k, 15) * 0x1b873593u;
            h = rotl(h ^ k, 13) * 5u + 0xe6546b64u;
        }
        h ^= static_cast<uint32_t>(len);
        h ^= h >> 16; h *= 0x85ebca6bu;
        h ^= h >> 13; h *= 0xc2b2ae35u;
        h ^= h >> 16;
        return h;
    }
    void reset() {
        nb_ = 16;
        std::memset(w_, 0, nb_ * 4);
        etop_ = 1;
        marks_ = live_ = 0;
        peak_ = nb_ + etop_;
    }
    uint32_t* entry(uint32_t r) { return w_ + nb_ + r; }
    const uint32_t* entry(uint32_t r) const { return w_ + nb_ + r; }
    void touch() { uint32_t u = nb_ + etop_ + marks_; if (u > peak_) peak_ = u; }

    // Room for `need` more words and `more` more entries (buckets double at load factor 1).
    bool ensure(uint32_t need, uint32_t more) {
        uint32_t nb = nb_;
        while (live_ + more > nb) nb *= 2;
        uint64_t total = static_cast<uint64_t>(nb) + etop_ + marks_ + need;
        if (nb == nb_ && total <= cap_) return true;
        uint32_t cap = cap_;
        if (total > cap_) {
            if (fixed_) return false;
            uint64_t want = static_cast<uint64_t>(cap_) + cap_ / 2;
            if (want < total) want = total;
            uint32_t* nw = static_cast<uint32_t*>(realloc_(w_, static_cast<size_t>(want) * 4));
            if (!nw) return false;
            w_ = nw;
            cap = static_cast<uint32_t>(want);
            std::memmove(w_ + cap - marks_, w_ + cap_ - marks_, static_cast<size_t>(marks_) * 4);
        }
        if (nb != nb_) {             // more buckets: slide the entries up and re-link, oldest first
            std::memmove(w_ + nb, w_ + nb_, static_cast<size_t>(etop_) * 4);
            nb_ = nb;
            std::memset(w_, 0, static_cast<size_t>(nb_) * 4);
            for (uint32_t r = 1; r < etop_;) {
                uint32_t* e = entry(r);
                uint32_t b = hash_stored(e) & (nb_ - 1);   // C1: recomputed, not stored
                e[0] = w_[b];
                w_[b] = r;
                r += 3 + words(e[2] & 0xFFFF);
            }
        }
        cap_ = cap;
        touch();
        return true;
    }

    uint32_t* w_;
    uint32_t cap_, nb_, etop_, marks_, live_, peak_;
    bool fixed_, valid_;
    ReallocFn realloc_;
};

}  // namespace arena_chain_nohash
#endif
