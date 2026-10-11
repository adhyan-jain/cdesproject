// ArenaChain - a conventional allocator-free scoped symbol table, written as a strong
// baseline for STRATA. It is the classic compiler design (chained hash table over an arena
// of symbol entries, popped at scope exit; cf. lcc and Tiny C Compiler's symbol stacks):
//
//   word 0                                                          word cap
//   | bucket heads | entry stack ->        free        <- scope marks |
//
//   entry  [next in chain][hash][value][len | depth << 16][name bytes, zero padded]
//
// One entry per DECLARATION (the name is stored each time, unpacked). A new entry is
// linked at the head of its bucket, so the first match in a chain is the innermost
// declaration; leaving a scope unlinks and pops that scope's entries.
//
// It shares STRATA's storage discipline on purpose - one buffer, caller-supplied or grown
// by realloc in 1.5x steps, no exceptions, refusal with no state change when full - so that
// a comparison isolates the data-structure differences (interning, undo entries, packing,
// open addressing) from the mere absence of an allocator.
#ifndef CDES_ARENA_CHAIN_HPP
#define CDES_ARENA_CHAIN_HPP

#include <cstdint>
#include <cstdlib>
#include <cstring>

namespace arena_chain {

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
            uint32_t b = e[1] & (nb_ - 1);
            while (w_[b] >= floor) w_[b] = entry(w_[b])[0];
            r += 4 + words(e[3] & 0xFFFF);
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
            if (e[1] == h && (e[3] & 0xFFFF) == len && std::memcmp(e + 4, key, n * 4) == 0) {
                if ((e[3] >> 16) != marks_) break;   // innermost match is in an outer scope: shadow it
                e[2] = static_cast<uint32_t>(value);
                return 1;
            }
        }
        if (!ensure(4 + n, 1)) return -1;
        uint32_t r = etop_, b = h & (nb_ - 1);
        uint32_t* e = entry(r);
        e[0] = w_[b];
        e[1] = h;
        e[2] = static_cast<uint32_t>(value);
        e[3] = static_cast<uint32_t>(len) | marks_ << 16;
        std::memcpy(e + 4, key, n * 4);
        w_[b] = r;
        etop_ += 4 + n;
        ++live_;
        touch();
        return 0;
    }
    bool resolve(const char* name, size_t len, int32_t* value) const {
        if (!valid_ || len == 0 || len > 255) return false;
        uint32_t key[64], n = words(len), h = hash(name, len, key, n);
        for (uint32_t r = w_[h & (nb_ - 1)]; r; r = entry(r)[0]) {
            const uint32_t* e = entry(r);
            if (e[1] == h && (e[3] & 0xFFFF) == len && std::memcmp(e + 4, key, n * 4) == 0) {
                *value = static_cast<int32_t>(e[2]);
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
                uint32_t b = e[1] & (nb_ - 1);
                e[0] = w_[b];
                w_[b] = r;
                r += 4 + words(e[3] & 0xFFFF);
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

}  // namespace arena_chain
#endif
