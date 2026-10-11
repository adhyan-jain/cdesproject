// Every table under comparison behind one interface:
//
//   bool enter();  bool exit();                       exit at the outermost scope is a no-op
//   int  declare(const std::string&, int32_t value);  0 new, 1 redeclared in this scope
//                                                     (value replaced), <0 refused
//   bool resolve(const std::string&, int32_t* value); innermost visible declaration
//
// Names arrive as existing std::string objects, so no table pays for building a string.
#ifndef CDES_BASELINE_TABLES_HPP
#define CDES_BASELINE_TABLES_HPP

#include <string>
#include <unordered_map>
#include <vector>

#include "../../include/strata/strata.hpp"
#include "../common.hpp"

#ifdef CDES_HAVE_PHMAP
#include <parallel_hashmap/phmap.h>
#endif
#ifdef CDES_HAVE_METIS
#include "historical/conventional_symbol_table.hpp"
#include "historical/embedded_conventional_symbol_table.hpp"
#include "metis_x.hpp"
#endif

namespace tables {

// ---- STRATA ---------------------------------------------------------------------
inline void* counted_alloc(size_t n, void*) { return mem::alloc(n); }
inline void counted_free(void* p, void*) { mem::dealloc(p); }
inline void* counted_realloc(void* p, size_t, size_t n, void*) { return mem::resize(p, n); }
inline strata::Options strata_options(bool pack, bool shrink) {
    strata::Options o;
    o.pack_names = pack;
    o.shrink = shrink;
    o.alloc = counted_alloc;
    o.free = counted_free;
    o.realloc = counted_realloc;
    return o;
}
template <bool Pack, bool Shrink>
struct StrataT {
    strata::Table t;
    StrataT() : t(strata_options(Pack, Shrink)) {}
    static const char* id() { return !Shrink ? "strata_noshrink" : Pack ? "strata" : "strata_raw"; }
    bool enter() { return t.enter_scope() == strata::kOk; }
    bool exit() { return t.exit_scope() == strata::kOk; }
    int declare(const std::string& s, int32_t v) { return t.declare(s.data(), s.size(), v); }
    bool resolve(const std::string& s, int32_t* v) const { return t.resolve(s.data(), s.size(), v); }
    size_t used_peak() const { return t.stats().peak_used_bytes; }   // bytes actually occupied inside the buffer
};
typedef StrataT<true, true> Strata;            // default configuration
typedef StrataT<false, true> StrataRaw;        // ablation: names stored as raw bytes
typedef StrataT<true, false> StrataNoShrink;   // ablation: the buffer is never given back

// ---- conventional: one hash map per open scope ------------------------------------
struct ScopeMapStack {
    std::vector<std::unordered_map<std::string, int32_t> > scopes;
    ScopeMapStack() : scopes(1) {}
    static const char* id() { return "scope_map_stack"; }
    size_t used_peak() const { return 0; }
    bool enter() { scopes.emplace_back(); return true; }
    bool exit() { if (scopes.size() == 1) return false; scopes.pop_back(); return true; }
    int declare(const std::string& s, int32_t v) {
        std::pair<std::unordered_map<std::string, int32_t>::iterator, bool> r = scopes.back().emplace(s, v);
        if (r.second) return 0;
        r.first->second = v;
        return 1;
    }
    bool resolve(const std::string& s, int32_t* v) const {
        for (size_t i = scopes.size(); i-- > 0;) {
            std::unordered_map<std::string, int32_t>::const_iterator it = scopes[i].find(s);
            if (it != scopes[i].end()) { *v = it->second; return true; }
        }
        return false;
    }
};

// ---- one map from name to its innermost binding + an undo log ----------------------
// The algorithm of LLVM's ScopedHashTable: a lookup is one map probe whatever the
// nesting depth; leaving a scope pops that scope's bindings and restores what each
// one shadowed; a name with no binding left is erased from the map.
// Map must keep element addresses stable (std::unordered_map, phmap::node_hash_map).
template <class Map, const char* (*Name)()>
struct UndoLogTable {
    struct Bind { typename Map::value_type* node; uint32_t prev; int32_t value; };
    Map map;                       // name -> index of innermost binding + 1
    std::vector<Bind> binds;
    std::vector<uint32_t> marks;   // binds.size() at each scope entry
    static const char* id() { return Name(); }
    size_t used_peak() const { return 0; }
    bool enter() { marks.push_back(static_cast<uint32_t>(binds.size())); return true; }
    bool exit() {
        if (marks.empty()) return false;
        uint32_t m = marks.back();
        marks.pop_back();
        while (binds.size() > m) {
            Bind& b = binds.back();
            if (b.prev) b.node->second = b.prev;
            else map.erase(map.find(b.node->first));
            binds.pop_back();
        }
        return true;
    }
    int declare(const std::string& s, int32_t v) {
        std::pair<typename Map::iterator, bool> r = map.emplace(s, 0u);
        uint32_t head = r.first->second, floor = marks.empty() ? 0 : marks.back();
        if (head > floor) { binds[head - 1].value = v; return 1; }
        Bind b = {&*r.first, head, v};
        binds.push_back(b);
        r.first->second = static_cast<uint32_t>(binds.size());
        return 0;
    }
    bool resolve(const std::string& s, int32_t* v) const {
        typename Map::const_iterator it = map.find(s);
        if (it == map.end()) return false;
        *v = binds[it->second - 1].value;
        return true;
    }
};
inline const char* std_undo_name() { return "std_undo_log"; }
typedef UndoLogTable<std::unordered_map<std::string, uint32_t>, std_undo_name> StdUndoLog;

#ifdef CDES_HAVE_PHMAP
inline const char* swiss_undo_name() { return "swiss_undo_log"; }
typedef UndoLogTable<phmap::node_hash_map<std::string, uint32_t>, swiss_undo_name> SwissUndoLog;

// Interning in a flat Swiss table (names are never removed within a translation unit),
// dense per-identifier heads and an undo log. This mirrors what production front ends do:
// intern once, then resolve by integer.
struct SwissInterned {
    struct Bind { uint32_t ident, prev; int32_t value; };
    phmap::flat_hash_map<std::string, uint32_t> ids;
    std::vector<uint32_t> head;    // per identifier: innermost binding + 1, 0 = none
    std::vector<Bind> binds;
    std::vector<uint32_t> marks;
    static const char* id() { return "swiss_interned"; }
    size_t used_peak() const { return 0; }
    bool enter() { marks.push_back(static_cast<uint32_t>(binds.size())); return true; }
    bool exit() {
        if (marks.empty()) return false;
        uint32_t m = marks.back();
        marks.pop_back();
        while (binds.size() > m) { head[binds.back().ident] = binds.back().prev; binds.pop_back(); }
        return true;
    }
    int declare(const std::string& s, int32_t v) {
        std::pair<phmap::flat_hash_map<std::string, uint32_t>::iterator, bool> r =
            ids.emplace(s, static_cast<uint32_t>(head.size()));
        if (r.second) head.push_back(0);
        uint32_t i = r.first->second, h = head[i], floor = marks.empty() ? 0 : marks.back();
        if (h > floor) { binds[h - 1].value = v; return 1; }
        Bind b = {i, h, v};
        binds.push_back(b);
        head[i] = static_cast<uint32_t>(binds.size());
        return 0;
    }
    bool resolve(const std::string& s, int32_t* v) const {
        phmap::flat_hash_map<std::string, uint32_t>::const_iterator it = ids.find(s);
        if (it == ids.end() || head[it->second] == 0) return false;
        *v = binds[head[it->second] - 1].value;
        return true;
    }
};
#endif

#ifdef CDES_HAVE_METIS
// ---- tables of the earlier METIS repository, unmodified ------------------------------
// They number declarations themselves (0, 1, 2, ... per insert call); the harness passes
// the same running number as `value`, so results are comparable.
template <class T, const char* (*Name)()>
struct MetisAdapter {
    T t;
    static const char* id() { return Name(); }
    size_t used_peak() const { return 0; }
    bool enter() { return t.enterScope() >= 0; }
    bool exit() { t.exitScope(); return true; }
    int declare(const std::string& s, int32_t v) {
        // these tables do not say whether an insert was a redeclaration; the harness
        // only checks that they accepted it and numbered it as expected
        return t.insert(s) == v ? 0 : -1;
    }
    bool resolve(const std::string& s, int32_t* v) const {
        int id = t.resolve(s);
        *v = id;
        return id >= 0;
    }
};
inline const char* metisx_name() { return "metis_x"; }
inline const char* metis_arena_name() { return "metis_arena_lp"; }
inline const char* metis_maps_name() { return "metis_scope_maps"; }
typedef MetisAdapter<budgetsym::metisx::MetisXTable, metisx_name> MetisX;
typedef MetisAdapter<budgetsym::EmbeddedConventionalSymbolTable, metis_arena_name> MetisArenaLP;
typedef MetisAdapter<budgetsym::ConventionalSymbolTable, metis_maps_name> MetisScopeMaps;
#endif

}  // namespace tables
#endif
