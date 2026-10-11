// Scope-table back ends for the patched chibicc (see apply_patch.py).
//   -DBACKEND_STRATA   STRATA, growable mode
//   -DBACKEND_ARENA    the conventional arena + chains table
// chibicc stores a pointer per declaration; the tables store a 32-bit value, so the
// pointers live in a side array and the table holds the index.
//
// Global lookups (chibicc's find_func) ask for the declaration in the OUTERMOST scope,
// which an innermost-first table cannot answer when a local declaration hides it. Global
// declarations are therefore also kept in a second table instance of the same kind.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "strata/strata.hpp"
#include "arena_chain.hpp"

namespace {
void** g_vals;
uint32_t g_nvals, g_cap, g_depth;

int32_t remember(void* p) {
    if (g_nvals == g_cap) {
        g_cap = g_cap ? g_cap * 2 : 1024;
        g_vals = static_cast<void**>(std::realloc(g_vals, g_cap * sizeof(void*)));
        if (!g_vals) { std::fprintf(stderr, "cdes backend: out of memory\n"); std::exit(1); }
    }
    g_vals[g_nvals] = p;
    return static_cast<int32_t>(g_nvals++);
}
void fail(const char* what) { std::fprintf(stderr, "cdes backend: %s refused\n", what); std::exit(1); }

#if defined(BACKEND_STRATA)
strata::Table g_all, g_global;
bool t_enter() { return g_all.enter_scope() == strata::kOk; }
void t_leave() { g_all.exit_scope(); }
bool t_put(strata::Table& t, const char* n, int len, int32_t v) { return t.declare(n, static_cast<size_t>(len), v) >= 0; }
bool t_get(const strata::Table& t, const char* n, int len, int32_t* v) { return t.resolve(n, static_cast<size_t>(len), v); }
typedef strata::Table TableT;
#elif defined(BACKEND_ARENA)
arena_chain::Table g_all, g_global;
bool t_enter() { return g_all.enter_scope(); }
void t_leave() { g_all.exit_scope(); }
bool t_put(arena_chain::Table& t, const char* n, int len, int32_t v) { return t.declare(n, static_cast<size_t>(len), v) >= 0; }
bool t_get(const arena_chain::Table& t, const char* n, int len, int32_t* v) { return t.resolve(n, static_cast<size_t>(len), v); }
typedef arena_chain::Table TableT;
#else
#error "define BACKEND_STRATA or BACKEND_ARENA"
#endif
}  // namespace

// chibicc declares unnamed entities (for example unnamed parameters) under the empty name.
// The tables require at least one byte, so the empty name is stored as the single byte 0x01,
// which cannot occur in an identifier.
static inline void norm(const char*& name, int& len) {
    static const char kEmpty[1] = {1};
    if (len == 0) { name = kEmpty; len = 1; }
}

extern "C" {
void cdes_enter(void) { if (!t_enter()) fail("enter_scope"); ++g_depth; }
void cdes_leave(void) { t_leave(); --g_depth; }
void cdes_put(const char* name, int len, void* val) {
    norm(name, len);
    int32_t v = remember(val);
    if (!t_put(g_all, name, len, v)) { std::fprintf(stderr, "name of %d bytes: ", len); fail("declare"); }
    if (g_depth == 0 && !t_put(g_global, name, len, v)) fail("declare (global)");
}
void* cdes_get(const char* name, int len) {
    norm(name, len);
    int32_t v;
    return t_get(g_all, name, len, &v) ? g_vals[v] : 0;
}
void* cdes_get_global(const char* name, int len) {
    norm(name, len);
    int32_t v;
    return t_get(g_global, name, len, &v) ? g_vals[v] : 0;
}
}
