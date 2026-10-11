#!/usr/bin/env python3
"""Patch chibicc (https://github.com/rui314/chibicc, commit 90d1f7f, MIT) in two ways.

    python3 apply_patch.py /path/to/chibicc

1. Trace logging. With the environment variable CDES_TRACE set, the compiler appends its
   variable-scope activity to that file, in the same format as the TinyCC traces:
       U            a compilation starts          E / X   enter_scope / leave_scope
       D name       push_scope (a declaration)    L name  find_var (a lookup)
   chibicc resolves identifiers by STRING, one hash map per open scope, so these are the
   calls of a compiler that really uses a string-keyed scoped symbol table.

2. Pluggable table. When built with -DCDES_BACKEND, the per-scope "vars" hash maps are not
   used at all; push_scope / find_var / find_func call the functions declared below, which
   tools/chibicc/cdes_backend.cpp implements on STRATA or on the conventional arena table.
   (Struct/union/enum tags keep chibicc's own maps.)

Every replacement must match exactly once.
"""
import sys

path = sys.argv[1].rstrip("/") + "/parse.c"
src = open(path).read()
if "CDES_TRACE" in src:
    sys.exit("already patched")


def rep(old, new):
    global src
    if src.count(old) != 1:
        sys.exit("patch site not found exactly once: %r (found %d)" % (old[:60], src.count(old)))
    src = src.replace(old, new)


rep('static Scope *scope = &(Scope){};',
    '''static Scope *scope = &(Scope){};

// ---- cdesproject hooks -------------------------------------------------------------
static FILE *cdes_fp;
static bool cdes_init;
static void cdes_log(const char *tag, const char *name, int len) {
  if (!cdes_init) {
    cdes_init = true;
    char *p = getenv("CDES_TRACE");
    cdes_fp = p ? fopen(p, "a") : NULL;
    if (cdes_fp) fputs("U\\n", cdes_fp);
  }
  if (!cdes_fp) return;
  if (name) fprintf(cdes_fp, "%s %.*s\\n", tag, len, name);
  else fprintf(cdes_fp, "%s\\n", tag);
}
#ifdef CDES_BACKEND
void cdes_enter(void);
void cdes_leave(void);
void cdes_put(const char *name, int len, void *val);
void *cdes_get(const char *name, int len);
void *cdes_get_global(const char *name, int len);
#endif
// --------------------------------------------------------------------------------------''')

rep('''static void enter_scope(void) {
  Scope *sc = calloc(1, sizeof(Scope));
  sc->next = scope;
  scope = sc;
}''', '''static void enter_scope(void) {
  Scope *sc = calloc(1, sizeof(Scope));
  sc->next = scope;
  scope = sc;
  cdes_log("E", NULL, 0);
#ifdef CDES_BACKEND
  cdes_enter();
#endif
}''')

rep('''static void leave_scope(void) {
  scope = scope->next;
}''', '''static void leave_scope(void) {
  scope = scope->next;
  cdes_log("X", NULL, 0);
#ifdef CDES_BACKEND
  cdes_leave();
#endif
}''')

rep('''static VarScope *find_var(Token *tok) {
  for (Scope *sc = scope; sc; sc = sc->next) {''', '''static VarScope *find_var(Token *tok) {
  cdes_log("L", tok->loc, tok->len);
#ifdef CDES_BACKEND
  return cdes_get(tok->loc, tok->len);
#endif
  for (Scope *sc = scope; sc; sc = sc->next) {''')

rep('''static VarScope *push_scope(char *name) {
  VarScope *sc = calloc(1, sizeof(VarScope));
  hashmap_put(&scope->vars, name, sc);
  return sc;
}''', '''static VarScope *push_scope(char *name) {
  VarScope *sc = calloc(1, sizeof(VarScope));
  cdes_log("D", name, strlen(name));
#ifdef CDES_BACKEND
  cdes_put(name, strlen(name), sc);
#else
  hashmap_put(&scope->vars, name, sc);
#endif
  return sc;
}''')

rep('''  VarScope *sc2 = hashmap_get(&sc->vars, name);
  if (sc2 && sc2->var && sc2->var->is_function)''', '''#ifdef CDES_BACKEND
  VarScope *sc2 = cdes_get_global(name, strlen(name));
#else
  VarScope *sc2 = hashmap_get(&sc->vars, name);
#endif
  if (sc2 && sc2->var && sc2->var->is_function)''')
open(path, "w").write(src)
print("patched", path)
