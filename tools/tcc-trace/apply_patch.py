#!/usr/bin/env python3
"""Instrument Tiny C Compiler (tccgen.c) so that it logs its own symbol-table activity.

    python3 apply_patch.py /path/to/tinycc

The patched compiler writes one line per event to the file named by the environment
variable CDES_TRACE (appending), and behaves normally when the variable is unset.

    U          a new translation unit starts
    E / X      a lexical scope is entered / left (++local_scope / --local_scope in TCC,
               plus the function-parameter scope of gen_function)
    D name     an ordinary identifier is entered in the symbol table (sym_link)
    L name     the compiler looks an identifier up (sym_find)

Struct/union/enum tags, struct members, labels and macros live in other TCC tables and
are not logged. A file-scope identifier that TCC pushes while a local scope is open
(global_identifier_push, e.g. an implicit function declaration) is logged as "G name"
and is ignored by the replay tools.

Written against TinyCC commit 43c7708b85681a2fd4451c8a541af4494a8919b2; every
replacement below must match exactly once or the script stops.
"""
import sys

path = sys.argv[1].rstrip("/") + "/tccgen.c"
src = open(path).read()
if "CDES_TRACE" in src:
    sys.exit("already patched")


def rep(old, new, count=1):
    global src
    if src.count(old) != count:
        sys.exit("patch site not found exactly %d time(s): %r (found %d)" % (count, old[:60], src.count(old)))
    src = src.replace(old, new)


HELPERS = r'''
/* ---- cdesproject trace hooks ------------------------------------------- */
static FILE *cdes_fp;
static int cdes_depth;
static void cdes_close(void)
{
    if (cdes_fp) {
        while (cdes_depth > 0) { fputs("X\n", cdes_fp); --cdes_depth; }
        fclose(cdes_fp);
        cdes_fp = NULL;
    }
}
static void cdes_open(void)
{
    const char *p = getenv("CDES_TRACE");
    cdes_close();
    cdes_fp = p ? fopen(p, "a") : NULL;
    cdes_depth = 0;
    if (cdes_fp) fputs("U\n", cdes_fp);
}
static void cdes_scope(int enter)
{
    if (!cdes_fp) return;
    if (enter) { fputs("E\n", cdes_fp); ++cdes_depth; }
    else if (cdes_depth > 0) { fputs("X\n", cdes_fp); --cdes_depth; }
}
static void cdes_name(char kind, int v)
{
    if (cdes_fp) fprintf(cdes_fp, "%c %s\n", kind, get_tok_str(v, NULL));
}
/* ------------------------------------------------------------------------ */

/* push, without hashing */
ST_FUNC Sym *sym_push2('''
rep("\n/* push, without hashing */\nST_FUNC Sym *sym_push2(", HELPERS)

# lookups
rep('''    if ((unsigned)v >= (unsigned)(tok_ident - TOK_IDENT))
        return NULL;
    return table_ident[v]->sym_identifier;''',
    '''    if ((unsigned)v >= (unsigned)(tok_ident - TOK_IDENT))
        return NULL;
    cdes_name('L', v + TOK_IDENT);
    return table_ident[v]->sym_identifier;''')

# declarations of ordinary identifiers
rep('''    if (yes) {
        s->prev_tok = *ps, *ps = s;
        s->sym_scope = local_scope;''',
    '''    if (yes) {
        if (!(s->v & SYM_STRUCT)) cdes_name('D', s->v);
        s->prev_tok = *ps, *ps = s;
        s->sym_scope = local_scope;''')
rep('''    if (v < SYM_FIRST_ANOM) {
        ps = &table_ident[v - TOK_IDENT]->sym_identifier;''',
    '''    if (v < SYM_FIRST_ANOM) {
        cdes_name(cdes_depth ? 'G' : 'D', v);
        ps = &table_ident[v - TOK_IDENT]->sym_identifier;''')

# block scopes
rep('''    o->llstk = local_label_stack;
    ++local_scope;''', '''    o->llstk = local_label_stack;
    ++local_scope; cdes_scope(1);''')
rep('''    cur_scope = o->prev;
    --local_scope;''', '''    cur_scope = o->prev;
    --local_scope; cdes_scope(0);''')
rep('''    o->lstk = local_stack;
    ++local_scope;
}''', '''    o->lstk = local_stack;
    ++local_scope; cdes_scope(1);
}''')
rep('''    sym_pop(&local_stack, o->lstk, 0);
    --local_scope;
}''', '''    sym_pop(&local_stack, o->lstk, 0);
    --local_scope; cdes_scope(0);
}''')

# function-prototype parameter scope
rep('''        ps = local_stack ? &local_stack : &global_stack;
        ++local_scope;''', '''        ps = local_stack ? &local_stack : &global_stack;
        ++local_scope; cdes_scope(1);''')
rep('''            sym_pop(ps, sr->prev, 0);
            --local_scope;''', '''            sym_pop(ps, sr->prev, 0);
            --local_scope; cdes_scope(0);''')
rep('''        sym_pop(ps, sr, 1);
        --local_scope;''', '''        sym_pop(ps, sr, 1);
        --local_scope; cdes_scope(0);''')

# function definition: parameters live in a scope that ends with the function
rep('''    /* push parameters */
    local_scope = 1;''', '''    /* push parameters */
    cdes_scope(1);
    local_scope = 1;''')
rep('''    sym_pop(&local_stack, NULL, 0);
    label_pop(&global_label_stack, NULL, 0);''', '''    sym_pop(&local_stack, NULL, 0);
    cdes_scope(0);
    label_pop(&global_label_stack, NULL, 0);''')

# one trace unit per compilation
rep('''ST_FUNC int tccgen_compile(TCCState *s1)
{''', '''static void cdes_open(void);
static void cdes_close(void);
ST_FUNC int tccgen_compile(TCCState *s1)
{
    cdes_open();''')
rep('''ST_FUNC void tccgen_finish(TCCState *s1)
{''', '''ST_FUNC void tccgen_finish(TCCState *s1)
{
    cdes_close();''')
open(path, "w").write(src)
print("patched", path)
