// STRATA - a budgeted, stack-disciplined scoped symbol table.  C++14, header only.
//
// All state lives in ONE contiguous buffer of 32-bit words:
//
//   word 0                                                               word cap
//   | index (open addressing) | identifier stack ->   free   <- undo stack |
//
//   index       one word per slot: 8-bit fingerprint | 24-bit identifier reference
//   identifier  [value][meta][name words...]     one record per DISTINCT visible name;
//               it holds the innermost declaration of that name directly
//   undo entry  [index slot]                     a declaration of a name not visible before
//               [ident ref|S][value][meta bits]  a declaration that shadows: the hidden
//                                                declaration is saved here
//   scope mark  [identifier-stack top at entry][previous mark]   pushed on the undo stack
//
// Why this shape:
//   * A lookup ends in the identifier record: no second hop to a declaration record, and
//     the cost does not depend on how deeply the name is shadowed.
//   * A declaration that shadows nothing costs one identifier record plus 4 bytes.
//   * Identifier characters [A-Za-z0-9_] are packed five to a word (6 bits each); the query
//     is packed once and compared word by word, so stored names are never unpacked.
//   * Scopes are strictly LIFO, so everything a scope added sits on top of the two stacks.
//     Leaving a scope pops them; the index entries of names first seen in that scope are
//     the most recently inserted ones, and in linear probing the most recently inserted
//     keys can be removed by simply emptying their slots (no tombstones, no shifting).
//     The undo entry of such a name records its slot, so removal is one store per name.
//   * References are relative (identifiers: from the start of their region; undo entries:
//     from the end of the buffer), so growing the index or the buffer moves two blocks and
//     rebuilds the index without patching any stored reference.
//
// Modes:
//   fixed     Table(buffer, bytes): never allocates; when the buffer is full declare()/
//             enter_scope() return kNoMemory and leave the table unchanged.
//   growable  Table(options): grows the buffer on demand (up to options.max_bytes) and
//             gives memory back when less than a quarter is in use. A failed allocation
//             leaves the table unchanged.
//   bounded   Table(buffer, bytes, options) with options.index_slots != 0: a fixed-mode
//             table whose index has a static size and is never rebuilt, so no operation
//             contains a hidden O(n) step. With options.max_probe = L, a lookup or a
//             declaration examines at most L index slots; a new name that would need a
//             longer probe sequence is refused with kProbeLimit and nothing changes.
//             options.keyed selects a keyed hash (HalfSipHash-1-3) so that the positions
//             of names cannot be predicted without the key.
// No exceptions are thrown and none are needed. Not thread-safe.
//
// Limits: names 1..255 bytes; scope depth <= 16383; buffer <= 64 MiB; type tag 0..255.
// The keyed hash reads name words in host order; its agreement with the reference
// HalfSipHash is checked on little-endian hosts only.
#ifndef STRATA_STRATA_HPP
#define STRATA_STRATA_HPP

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>

namespace strata {

enum Status {
    kOk = 0,           // new declaration stored
    kRedeclared = 1,   // same name already declared in the current scope: value/type replaced
    kNoMemory = -1,    // buffer or budget exhausted; nothing was changed
    kNameTooLong = -2, // more than kMaxNameLen bytes
    kEmptyName = -3,
    kNoScope = -4,     // exit_scope() at the outermost scope
    kTooDeep = -5,     // more than kMaxDepth open scopes
    kProbeLimit = -6   // bounded mode: the name would need more than max_probe index probes; nothing was changed
};

enum { kMaxNameLen = 255, kMaxNameWords = 64, kMaxDepth = 16383, kMarkWords = 2 };

typedef void* (*AllocFn)(size_t bytes, void* user);
typedef void (*FreeFn)(void* p, void* user);
typedef void* (*ReallocFn)(void* p, size_t old_bytes, size_t new_bytes, void* user);  // 0 on failure, old block kept

struct Options {
    size_t initial_bytes;  // growable mode: first buffer size
    size_t max_bytes;      // growable mode: hard budget (0 = unlimited)
    bool pack_names;       // 6-bit packing of identifier characters (false: raw bytes)
    bool shrink;           // growable mode: give memory back after usage has stayed low for 64 scope exits
    bool sparse_index;     // keep the index at most 1/2 full instead of 3/4: faster probes, more bytes per name
    AllocFn alloc;         // default: malloc
    FreeFn free;           // default: free
    ReallocFn realloc;     // default: realloc, or alloc + copy + free when only alloc/free are given
    void* user;
    bool keyed;            // hash names with HalfSipHash-1-3 under `key` instead of the unkeyed Murmur mixer
    uint32_t key[2];       // secret 64-bit key for `keyed`; must come from a source the input's author cannot predict
    uint32_t index_slots;  // fixed mode only: static index of this many slots (power of two >= 16), never rebuilt; 0 = grow in place
    uint32_t max_probe;    // with a static index: index slots examined per operation at most; 0 = no limit
    Options() : initial_bytes(1024), max_bytes(0), pack_names(true), shrink(true), sparse_index(false),
                alloc(0), free(0), realloc(0), user(0), keyed(false), index_slots(0), max_probe(0) { key[0] = key[1] = 0; }
};

struct Stats {
    size_t capacity_bytes;   // current buffer size
    size_t used_bytes;       // index + identifier stack + undo stack
    size_t peak_used_bytes;  // high-water mark of used_bytes
    size_t index_bytes, ident_bytes, undo_bytes;
    size_t live_declarations, live_identifiers, depth;
    size_t rebuilds;         // index or buffer relocations so far
    size_t longest_probe;    // most index slots any insertion has examined so far (1 = home slot was free)
};

// A name prepared for lookup: packed (or raw) words, key bits of the meta word, hash.
struct Key {
    uint32_t w[kMaxNameWords];
    uint32_t n;     // number of words
    uint32_t meta;  // n | raw << 7 | (len & 3) << 8
    uint32_t hash;
};

namespace detail {
// 0 = not an identifier character; otherwise a 6-bit code 1..63.
inline const uint8_t* code_table() {
    static uint8_t t[256];
    static bool ready = false;
    if (!ready) {
        uint8_t c = 1;
        for (int ch = 'a'; ch <= 'z'; ++ch) t[ch] = c++;
        for (int ch = 'A'; ch <= 'Z'; ++ch) t[ch] = c++;
        for (int ch = '0'; ch <= '9'; ++ch) t[ch] = c++;
        t[static_cast<unsigned char>('_')] = c;  // 63
        ready = true;
    }
    return t;
}
inline uint32_t rotl(uint32_t x, int r) { return (x << r) | (x >> (32 - r)); }
// MurmurHash3 x86_32 (Austin Appleby, public domain) over whole words; the meta word
// (length information) is mixed in last so that packing and hashing can share a loop.
enum : uint32_t { kHashSeed = 0x9747b28cu };
inline uint32_t hash_step(uint32_t h, uint32_t k) {
    k *= 0xcc9e2d51u;
    k = rotl(k, 15) * 0x1b873593u;
    return rotl(h ^ k, 13) * 5u + 0xe6546b64u;
}
inline uint32_t hash_finish(uint32_t h, uint32_t meta) {
    h ^= meta * 0x9E3779B1u;
    h ^= h >> 16; h *= 0x85ebca6bu;
    h ^= h >> 13; h *= 0xc2b2ae35u;
    h ^= h >> 16;
    return h;
}
inline uint32_t hash_words(const uint32_t* w, uint32_t n, uint32_t meta) {
    uint32_t h = kHashSeed;
    for (uint32_t i = 0; i < n; ++i) h = hash_step(h, w[i]);
    return hash_finish(h, meta);
}
// HalfSipHash-1-3 (J.-P. Aumasson; reference code CC0) of the message formed by the name
// words followed by the meta word, each taken as four little-endian bytes. 64-bit key,
// 32-bit result. On a little-endian machine the result equals the reference
// halfsiphash() of those bytes built with one compression and three finalization rounds.
inline void sipround(uint32_t& v0, uint32_t& v1, uint32_t& v2, uint32_t& v3) {
    v0 += v1; v1 = rotl(v1, 5); v1 ^= v0; v0 = rotl(v0, 16);
    v2 += v3; v3 = rotl(v3, 8); v3 ^= v2;
    v0 += v3; v3 = rotl(v3, 7); v3 ^= v0;
    v2 += v1; v1 = rotl(v1, 13); v1 ^= v2; v2 = rotl(v2, 16);
}
inline uint32_t halfsiphash13(const uint32_t* w, uint32_t n, uint32_t meta, uint32_t k0, uint32_t k1) {
    uint32_t v0 = k0, v1 = k1, v2 = 0x6c796765u ^ k0, v3 = 0x74656462u ^ k1;
    for (uint32_t i = 0; i <= n; ++i) {
        const uint32_t m = i < n ? w[i] : meta;
        v3 ^= m; sipround(v0, v1, v2, v3); v0 ^= m;
    }
    const uint32_t b = ((n + 1) * 4) << 24;   // length in bytes, top byte of the final block
    v3 ^= b; sipround(v0, v1, v2, v3); v0 ^= b;
    v2 ^= 0xff;
    sipround(v0, v1, v2, v3); sipround(v0, v1, v2, v3); sipround(v0, v1, v2, v3);
    return v1 ^ v3;
}
inline void* default_alloc(size_t n, void*) { return std::malloc(n); }
inline void default_free(void* p, void*) { std::free(p); }
inline void* default_realloc(void* p, size_t, size_t n, void*) { return std::realloc(p, n); }
}  // namespace detail

class Table {
public:
    // ---- construction ---------------------------------------------------
    // Fixed mode. `buffer` must be aligned for uint32_t and outlive the table.
    // At most 64 MiB of it is used.
    Table(void* buffer, size_t bytes, bool pack_names = true, bool sparse_index = false)
        : w_(static_cast<uint32_t*>(buffer)),
          cap_(bytes / 4 > kMaxWords ? static_cast<uint32_t>(kMaxWords) : static_cast<uint32_t>(bytes / 4)),
          fixed_(true) {
        opt_.pack_names = pack_names;
        opt_.sparse_index = sparse_index;
        init_hooks();
        valid_ = w_ != 0 && cap_ >= kMinWords;
        if (valid_) reset_layout();
    }
    // Fixed mode with options: pack_names, sparse_index, keyed/key, index_slots, max_probe
    // are used; the allocation fields are ignored. An index_slots that is not a power of
    // two >= 16 or does not fit the buffer, or a max_probe without index_slots, gives an
    // invalid table (every call returns kNoMemory) rather than a silently unbounded one.
    Table(void* buffer, size_t bytes, const Options& o)
        : w_(static_cast<uint32_t*>(buffer)),
          cap_(bytes / 4 > kMaxWords ? static_cast<uint32_t>(kMaxWords) : static_cast<uint32_t>(bytes / 4)),
          fixed_(true), opt_(o) {
        init_hooks();
        const uint32_t n = o.index_slots;
        bool ok = w_ != 0 && cap_ >= kMinWords;
        if (n) ok = ok && n >= kInitialIndex && !(n & (n - 1)) && n < cap_;
        else ok = ok && o.max_probe == 0;
        valid_ = ok;
        if (valid_) reset_layout();
    }
    // Growable mode.
    explicit Table(const Options& o = Options()) : w_(0), cap_(0), fixed_(false), opt_(o) {
        opt_.index_slots = opt_.max_probe = 0;   // a static index exists in fixed mode only
        init_hooks();
        size_t words = o.initial_bytes / 4;
        if (words < kMinWords) words = kMinWords;
        if (words > kMaxWords) words = kMaxWords;
        if (o.max_bytes && words * 4 > o.max_bytes) words = o.max_bytes / 4;
        valid_ = false;
        if (words >= kMinWords) {
            w_ = static_cast<uint32_t*>(opt_.alloc(words * 4, opt_.user));
            if (w_) { cap_ = static_cast<uint32_t>(words); valid_ = true; reset_layout(); }
        }
    }
    ~Table() { if (!fixed_ && w_) opt_.free(w_, opt_.user); }

    bool valid() const { return valid_; }  // false: no usable buffer; every call returns kNoMemory

    // ---- scopes -----------------------------------------------------------
    Status enter_scope() {
        if (!valid_) return kNoMemory;
        if (depth_ >= kMaxDepth) return kTooDeep;
        if (!ensure(kMarkWords, 0)) return kNoMemory;
        undo_ += kMarkWords;
        uint32_t* m = w_ + cap_ - undo_;
        m[0] = itop_;
        m[1] = mark_;
        mark_ = undo_;
        ++depth_;
        touch();
        return kOk;
    }

    Status exit_scope() {
        if (!valid_) return kNoMemory;
        if (mark_ == 0) return kNoScope;
        // 1. undo this scope's declarations, newest first
        while (undo_ > mark_) {
            const uint32_t* e = w_ + cap_ - undo_;
            if (e[0] & kShadowBit) {           // restore the declaration this one was hiding
                uint32_t* rec = ident(e[0] & kRefMask);
                rec[0] = e[1];
                rec[1] = (rec[1] & kKeyBits) | e[2];
                undo_ -= 3;
            } else {
                w_[e[0]] = 0;                  // first declaration of the name: empty its index slot
                --nident_;
                undo_ -= 1;
            }
            --ndecl_;
        }
        const uint32_t* m = w_ + cap_ - mark_;
        uint32_t saved_itop = m[0];
        mark_ = m[1];
        undo_ -= kMarkWords;
        --depth_;
        // 2. the names first seen in this scope were un-interned above (they are the newest
        //    index entries, so their slots could simply be emptied); drop their records.
        itop_ = saved_itop;
        // 3. give memory back only after the table has stayed small for a while, so that a
        //    large scope that is entered repeatedly does not shrink and regrow each time
        if (!fixed_ && opt_.shrink) {
            if (static_cast<uint64_t>(idx_ + itop_ + undo_) * 4 <= cap_) {
                if (++calm_ >= kShrinkPatience) { maybe_shrink(); calm_ = 0; }
            } else {
                calm_ = 0;
            }
        }
        return kOk;
    }

    // ---- declarations -------------------------------------------------------
    Status declare(const char* name, size_t len, int32_t value, uint8_t type = 0) {
        if (!valid_) return kNoMemory;
        Key k;
        Status s = make_key(name, len, k);
        if (s != kOk) return s;
        const uint32_t tag = static_cast<uint32_t>(type) << kTypeShift | depth_ << kDepthShift;
        uint32_t stop = kNoSlot;                       // where the search for the name ended
        uint32_t ref = find(k, &stop);
        if (ref) {
            uint32_t* rec = ident(ref);
            if ((rec[1] >> kDepthShift) == depth_) {   // already declared in the current scope
                rec[0] = static_cast<uint32_t>(value);
                rec[1] = (rec[1] & kKeyBits) | tag;
                return kRedeclared;
            }
            if (!ensure(3, 0)) return kNoMemory;
            rec = ident(ref);                          // ensure() may have moved the buffer
            undo_ += 3;
            uint32_t* e = w_ + cap_ - undo_;
            e[0] = ref | kShadowBit;
            e[1] = rec[0];
            e[2] = rec[1] & ~static_cast<uint32_t>(kKeyBits);
            rec[0] = static_cast<uint32_t>(value);
            rec[1] = (rec[1] & kKeyBits) | tag;
            ++ndecl_;
            touch();
            return kOk;
        }
        // new name: reserve everything first so that failure changes nothing
        if (itop_ + 2 + k.n > kRefMask) return kNoMemory;
        const uint32_t idx_before = idx_;
        if (!ensure(2 + k.n + 1, 1)) return kNoMemory;
        if (opt_.max_probe && stop == kNoSlot) return kProbeLimit;   // no empty slot within the limit
        ref = itop_;
        uint32_t* rec = ident(ref);
        rec[0] = static_cast<uint32_t>(value);
        rec[1] = k.meta | tag;
        std::memcpy(rec + 2, k.w, k.n * 4);
        itop_ += 2 + k.n;
        ++nident_;
        // The search above ended at the first empty slot of the name's probe path. Unless
        // ensure() rebuilt the index, that slot is where the name goes: no second walk.
        uint32_t slot;
        if (stop != kNoSlot && idx_ == idx_before) {
            slot = stop;
            w_[slot] = slot_word(k.hash, ref);
            const uint32_t steps = ((slot - home(k.hash)) & (idx_ - 1)) + 1;
            if (steps > longest_) longest_ = steps;
        } else {
            slot = index_insert(k.hash, ref);
        }
        undo_ += 1;
        w_[cap_ - undo_] = slot;
        ++ndecl_;
        touch();
        return kOk;
    }
    // NUL-terminated convenience forms (named differently to avoid overload ambiguity)
    Status declare_cstr(const char* name, int32_t value, uint8_t type = 0) {
        return declare(name, std::strlen(name), value, type);
    }

    // Innermost visible declaration of `name`. Returns false when there is none.
    bool resolve(const char* name, size_t len, int32_t* value = 0, uint8_t* type = 0) const {
        if (!valid_) return false;
        Key k;
        if (make_key(name, len, k) != kOk) return false;
        uint32_t ref = find(k);
        if (!ref) return false;
        const uint32_t* rec = ident(ref);
        if (value) *value = static_cast<int32_t>(rec[0]);
        if (type) *type = static_cast<uint8_t>(rec[1] >> kTypeShift);
        return true;
    }
    bool resolve_cstr(const char* name, int32_t* value = 0, uint8_t* type = 0) const {
        return resolve(name, std::strlen(name), value, type);
    }
    // True when `name` is declared in the current (innermost) scope itself.
    bool declared_in_current_scope(const char* name, size_t len) const {
        Key k;
        if (!valid_ || make_key(name, len, k) != kOk) return false;
        uint32_t ref = find(k);
        return ref && (ident(ref)[1] >> kDepthShift) == depth_;
    }

    // ---- introspection ------------------------------------------------------
    size_t depth() const { return depth_; }
    size_t size() const { return ndecl_; }
    Stats stats() const {
        Stats s;
        s.capacity_bytes = static_cast<size_t>(cap_) * 4;
        s.index_bytes = static_cast<size_t>(idx_) * 4;
        s.ident_bytes = static_cast<size_t>(itop_) * 4;
        s.undo_bytes = static_cast<size_t>(undo_) * 4;
        s.used_bytes = s.index_bytes + s.ident_bytes + s.undo_bytes;
        s.peak_used_bytes = static_cast<size_t>(peak_) * 4;
        s.live_declarations = ndecl_;
        s.live_identifiers = nident_;
        s.depth = depth_;
        s.rebuilds = rebuilds_;
        s.longest_probe = longest_;
        return s;
    }
    // Structural self-check used by the tests: every identifier is reachable through the
    // index, the undo stack parses back to the scope marks, counters match. O(n).
    bool check_invariants() const {
        if (!valid_) return false;
        if (idx_ + itop_ + undo_ > cap_ || (idx_ & (idx_ - 1))) return false;
        uint32_t idents = 0, used = 0, r = 1;
        for (uint32_t i = 0; i < idx_; ++i) if (w_[i]) ++used;
        while (r < itop_) {
            const uint32_t* rec = ident(r);
            uint32_t n = rec[1] & kWordsMask;
            if (n == 0 || n > kMaxNameWords || (rec[1] >> kDepthShift) > depth_) return false;
            uint32_t h = hash_of(rec + 2, n, rec[1] & kKeyBits);
            uint32_t i = home(h), steps = 0;
            while (w_[i] != slot_word(h, r)) {
                if (w_[i] == 0 || ++steps > idx_) return false;  // unreachable from its home slot
                i = (i + 1) & (idx_ - 1);
            }
            if (opt_.max_probe && steps >= opt_.max_probe) return false;  // beyond the probe limit
            ++idents;
            r += 2 + n;
        }
        if (r != itop_ || idents != nident_ || used != nident_) return false;
        uint32_t decls = 0, marks = 0, fresh = 0;
        for (uint32_t pos = undo_, mark = mark_; pos > 0;) {
            const uint32_t* e = w_ + cap_ - pos;
            if (pos == mark) { mark = e[1]; pos -= kMarkWords; ++marks; continue; }
            if (e[0] & kShadowBit) {
                if (pos < 3 || (e[0] & kRefMask) == 0 || (e[0] & kRefMask) >= itop_) return false;
                pos -= 3;
            } else {
                if (e[0] >= idx_ || w_[e[0]] == 0 || (w_[e[0]] & kRefMask) >= itop_) return false;
                pos -= 1;
                ++fresh;
            }
            ++decls;
        }
        return decls == ndecl_ && marks == depth_ && fresh == nident_;
    }

    // 64-bit digest of the complete logical state: counters, the index, both stacks.
    // Two tables with equal digests hold the same content in the same layout. The tests
    // use it to show that a refused operation changes nothing at all.
    uint64_t state_digest() const {
        uint64_t h = 1469598103934665603ull;
        const uint32_t head[8] = {idx_, itop_, undo_, mark_, ndecl_, nident_, depth_, cap_};
        for (int i = 0; i < 8; ++i) h = (h ^ head[i]) * 1099511628211ull;
        for (uint32_t i = 0; i < idx_ + itop_; ++i) h = (h ^ w_[i]) * 1099511628211ull;
        for (uint32_t i = cap_ - undo_; i < cap_; ++i) h = (h ^ w_[i]) * 1099511628211ull;
        return h;
    }

    // Packs (or copies) a name and hashes it. Public so tests can inspect the encoding.
    Status make_key(const char* name, size_t len, Key& k) const {
        if (len == 0) return kEmptyName;
        if (len > kMaxNameLen) return kNameTooLong;
        const uint8_t* code = detail::code_table();
        const unsigned char* s = reinterpret_cast<const unsigned char*>(name);
        uint32_t n = 0, raw = 0, h = detail::kHashSeed;
        if (opt_.pack_names) {
            size_t i = 0;
            for (; i + 5 <= len; i += 5) {
                uint32_t a = code[s[i]], b = code[s[i + 1]], c = code[s[i + 2]], d = code[s[i + 3]], e = code[s[i + 4]];
                if (!(a && b && c && d && e)) { raw = 1; break; }
                uint32_t word = a | b << 6 | c << 12 | d << 18 | e << 24;
                k.w[n++] = word;
                h = detail::hash_step(h, word);
            }
            if (!raw && i < len) {
                uint32_t word = 0;
                for (int sh = 0; i < len; ++i, sh += 6) {
                    uint32_t a = code[s[i]];
                    if (!a) { raw = 1; break; }
                    word |= a << sh;
                }
                k.w[n++] = word;
                h = detail::hash_step(h, word);
            }
        } else {
            raw = 1;
        }
        uint32_t tail = 0;
        if (raw) {
            n = static_cast<uint32_t>((len + 3) / 4);
            k.w[n - 1] = 0;
            std::memcpy(k.w, name, len);
            tail = static_cast<uint32_t>(len & 3);   // raw names can end in NUL bytes: keep the length
        }
        // packed names need no length: a code is never 0, so the padding is unambiguous
        k.n = n;
        k.meta = n | raw << 7 | tail << 8;
        if (opt_.keyed) k.hash = detail::halfsiphash13(k.w, n, k.meta, opt_.key[0], opt_.key[1]);
        else k.hash = raw ? detail::hash_words(k.w, n, k.meta) : detail::hash_finish(h, k.meta);
        return kOk;
    }

#ifdef STRATA_TEST_HOOKS
    // Forces every key into one home slot (worst-case clustering) when set.
    static bool& degenerate_hash() { static bool on = false; return on; }
#endif

private:
    // meta word of an identifier record:
    //   bits 0-6 name words | 7 raw | 8-9 raw length mod 4 | 10-17 type | 18-31 scope depth
    enum : uint32_t {
        kRefMask = 0x00FFFFFFu, kShadowBit = 0x01000000u, kMinWords = 32, kMaxWords = 0x00FFFFFFu,
        kNoSlot = 0xFFFFFFFFu, kWordsMask = 0x7Fu, kKeyBits = 0x3FFu, kTypeShift = 10, kDepthShift = 18, kInitialIndex = 16,
        kShrinkPatience = 64
    };

    Table(const Table&);
    Table& operator=(const Table&);

    void init_hooks() {
        if (!opt_.alloc && !opt_.free && !opt_.realloc) opt_.realloc = detail::default_realloc;
        if (!opt_.alloc) opt_.alloc = detail::default_alloc;
        if (!opt_.free) opt_.free = detail::default_free;
        idx_ = itop_ = undo_ = mark_ = peak_ = calm_ = longest_ = 0;
        ndecl_ = nident_ = depth_ = rebuilds_ = 0;
    }
    void reset_layout() {
        idx_ = opt_.index_slots ? opt_.index_slots : static_cast<uint32_t>(kInitialIndex);
        std::memset(w_, 0, static_cast<size_t>(idx_) * 4);
        itop_ = 1;  // reference 0 means "none"
        undo_ = mark_ = 0;
        ndecl_ = nident_ = depth_ = 0;
        touch();
    }
    uint32_t* ident(uint32_t ref) { return w_ + idx_ + ref; }
    const uint32_t* ident(uint32_t ref) const { return w_ + idx_ + ref; }
    uint32_t free_words() const { return cap_ - idx_ - itop_ - undo_; }
    void touch() { uint32_t u = idx_ + itop_ + undo_; if (u > peak_) peak_ = u; }

    static uint32_t slot_word(uint32_t h, uint32_t ref) {
        uint32_t fp = h >> 24;
        return (fp ? fp : 1u) << 24 | ref;
    }
    uint32_t home(uint32_t h) const {
#ifdef STRATA_TEST_HOOKS
        if (degenerate_hash()) return 0;
#endif
        return h & (idx_ - 1);
    }

    uint32_t hash_of(const uint32_t* w, uint32_t n, uint32_t meta) const {
        return opt_.keyed ? detail::halfsiphash13(w, n, meta, opt_.key[0], opt_.key[1]) : detail::hash_words(w, n, meta);
    }
    // Returns the identifier reference of the name, or 0. When the search ends at an empty
    // slot and `stop` is given, *stop is that slot (the place a new name would take); it is
    // left untouched when the search ends at the probe limit instead.
    uint32_t find(const Key& k, uint32_t* stop = 0) const {
        uint32_t fp = k.hash >> 24;
        if (!fp) fp = 1;
        const uint32_t mask = idx_ - 1;
        // No name is ever stored beyond max_probe slots from its home (declare refuses,
        // and a static index is never rebuilt), so the search may stop there.
        uint32_t left = opt_.max_probe ? opt_.max_probe : 0xFFFFFFFFu;
        for (uint32_t i = home(k.hash); left; i = (i + 1) & mask, --left) {
            uint32_t s = w_[i];
            if (s == 0) { if (stop) *stop = i; return 0; }
            if ((s >> 24) != fp) continue;
            const uint32_t* rec = ident(s & kRefMask);
            if ((rec[1] & kKeyBits) != k.meta) continue;
            uint32_t j = 0;
            while (j < k.n && rec[2 + j] == k.w[j]) ++j;
            if (j == k.n) return s & kRefMask;
        }
        return 0;
    }
    uint32_t index_insert(uint32_t h, uint32_t ref) {
        const uint32_t mask = idx_ - 1;
        uint32_t i = home(h), steps = 1;
        while (w_[i]) { i = (i + 1) & mask; ++steps; }
        w_[i] = slot_word(h, ref);
        if (steps > longest_) longest_ = steps;
        return i;
    }
    // Before the index is rebuilt: every first-declaration undo entry holds an index slot
    // that is about to become meaningless. Its record needs the entry again when it is
    // re-inserted, so the two words are swapped: the record's value word keeps the entry's
    // position (relative to the end of the buffer), the entry keeps the value. reindex()
    // swaps them back and writes the new slot. No name is hashed more than once per rebuild
    // and no scratch memory is needed.
    void stash_undo() {
        for (uint32_t pos = undo_, mark = mark_; pos > 0;) {
            uint32_t* e = w_ + cap_ - pos;
            if (pos == mark) { mark = e[1]; pos -= kMarkWords; continue; }
            if (e[0] & kShadowBit) { pos -= 3; continue; }
            uint32_t* rec = ident(w_[e[0]] & kRefMask);
            const uint32_t value = rec[0];
            rec[0] = pos;
            e[0] = value;
            pos -= 1;
        }
    }
    // Clears the index and re-inserts every name, oldest first (which keeps the "newest
    // keys can be emptied" property), completing what stash_undo() began.
    void reindex() {
        std::memset(w_, 0, static_cast<size_t>(idx_) * 4);
        for (uint32_t r = 1; r < itop_;) {
            uint32_t* rec = ident(r);
            const uint32_t n = rec[1] & kWordsMask;
            const uint32_t slot = index_insert(hash_of(rec + 2, n, rec[1] & kKeyBits), r);
            uint32_t* e = w_ + cap_ - rec[0];
            rec[0] = e[0];
            e[0] = slot;
            r += 2 + n;
        }
    }

    // Makes room for `words` more stack words and `new_idents` more index entries.
    // On failure nothing has changed.
    bool ensure(uint32_t words, uint32_t new_idents) {
        uint32_t idx = idx_;
        const uint64_t num = opt_.sparse_index ? 2 : 3;   // maximum load factor num/4
        if (opt_.index_slots)                             // static index: never rebuilt
            return static_cast<uint64_t>(nident_ + new_idents) * 4 <= static_cast<uint64_t>(idx) * num && free_words() >= words;
        while (static_cast<uint64_t>(nident_ + new_idents) * 4 > static_cast<uint64_t>(idx) * num) idx *= 2;
        if (idx == idx_ && free_words() >= words) return true;
        uint64_t need = static_cast<uint64_t>(idx) + itop_ + undo_ + words;
        if (need <= cap_) return relocate(cap_, idx);  // index grows inside the buffer
        if (fixed_) return false;
        uint64_t cap = static_cast<uint64_t>(cap_) + cap_ / 2;   // grow by half, or to what is needed
        if (cap < need) cap = need;
        if (cap > kMaxWords) cap = kMaxWords;
        if (opt_.max_bytes && cap * 4 > opt_.max_bytes) cap = opt_.max_bytes / 4;
        if (cap < need) return false;
        return relocate(static_cast<uint32_t>(cap), idx);
    }
    void maybe_shrink() {
        uint32_t used = idx_ + itop_ + undo_;
        uint32_t floor = static_cast<uint32_t>(opt_.initial_bytes / 4);
        if (floor < kMinWords) floor = kMinWords;
        if (cap_ <= floor || static_cast<uint64_t>(used) * 4 > cap_) return;
        uint32_t idx = idx_;
        // halve the index while it would stay at most half of its maximum load
        const uint64_t num = opt_.sparse_index ? 2 : 3;
        while (idx > kInitialIndex && static_cast<uint64_t>(nident_) * 16 <= static_cast<uint64_t>(idx) * num) idx /= 2;
        uint32_t cap = cap_;
        while (cap / 2 >= floor && static_cast<uint64_t>(idx + itop_ + undo_) * 2 <= cap / 2) cap /= 2;
        if (cap < cap_) relocate(cap, idx);
    }
    // Moves to a buffer of `cap` words with `idx` index slots (in place when cap == cap_).
    // Identifier and undo references are relative, so the two stacks are moved as blocks.
    // The index is rebuilt only when its size changes: when just the buffer grows or
    // shrinks, the index and the slots recorded in the undo stack stay valid as they are.
    bool relocate(uint32_t cap, uint32_t idx) {
        const size_t ib = static_cast<size_t>(itop_) * 4, ub = static_cast<size_t>(undo_) * 4;
        const bool resize_index = idx != idx_;
        if (cap > cap_) {            // grow: extend the block, then slide the two stacks outwards
            uint32_t* nw = resize_block(cap);
            if (!nw) return false;
            w_ = nw;
            if (resize_index) stash_undo();   // nothing below can fail any more
            std::memmove(w_ + cap - undo_, w_ + cap_ - undo_, ub);
            if (resize_index) std::memmove(w_ + idx, w_ + idx_, ib);
        } else if (cap < cap_) {     // shrink: slide the stacks inwards, then give the tail back
            if (resize_index) { stash_undo(); std::memmove(w_ + idx, w_ + idx_, ib); }
            std::memmove(w_ + cap - undo_, w_ + cap_ - undo_, ub);
            uint32_t* nw = resize_block(cap);
            if (nw) w_ = nw;         // if the allocator refuses, the larger block is simply kept
        } else if (resize_index) {
            stash_undo();
            std::memmove(w_ + idx, w_ + idx_, ib);
        }
        cap_ = cap;
        if (resize_index) { idx_ = idx; reindex(); }
        ++rebuilds_;
        touch();
        return true;
    }
    uint32_t* resize_block(uint32_t cap) {
        const size_t ob = static_cast<size_t>(cap_) * 4, nb = static_cast<size_t>(cap) * 4;
        if (opt_.realloc) return static_cast<uint32_t*>(opt_.realloc(w_, ob, nb, opt_.user));
        uint32_t* nw = static_cast<uint32_t*>(opt_.alloc(nb, opt_.user));
        if (!nw) return 0;
        std::memcpy(nw, w_, ob < nb ? ob : nb);
        opt_.free(w_, opt_.user);
        return nw;
    }

    uint32_t* w_;
    uint32_t cap_;       // buffer size in words
    uint32_t idx_;       // index slots (power of two)
    uint32_t itop_;      // identifier stack top, words from the start of its region
    uint32_t undo_;      // undo stack size in words (grows down from the end)
    uint32_t mark_;      // current scope mark (undo-stack reference), 0 at the outermost scope
    uint32_t peak_;
    uint32_t calm_;      // consecutive scope exits with the buffer at most a quarter full
    uint32_t longest_;   // most index slots examined by any insertion
    uint32_t ndecl_, nident_, depth_, rebuilds_;
    bool fixed_, valid_;
    Options opt_;
};

}  // namespace strata
#endif
