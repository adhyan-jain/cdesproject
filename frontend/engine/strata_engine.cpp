// STRATA demo engine: the bridge between the web demo (frontend/web) and the real table.
//
// Two modes. TRACE (see trace_mode below) replays a whole compiler trace and checks every
// answer. Otherwise it reads a short script on stdin, replays it on a strata::Table in FIXED mode (one
// caller-supplied buffer, no allocator) and prints the outcome as JSON on stdout:
//
//   CAP <bytes>                  buffer size, 128..65536, multiple of 4 (first line)
//   D <name> <type> <value>      declare(name, value, type)
//   L <name>                     resolve(name)
//   E                            enter_scope()
//   X                            exit_scope()
//   V <name> <type> <src>        resolve(src), then declare(name, value of src)
//
// Nothing here re-implements the table. Every status, value and byte count comes from
// strata::Table itself; the layout shown by the UI is read back from the buffer the table
// lives in, following the format documented at the top of include/strata/strata.hpp.
// Each answer is also checked against tests/reference_model.hpp (the independent model
// the test suite uses) and against resolve(), and the table's own check_invariants().
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

#include "strata/strata.hpp"
#include "../../benchmarks/baselines/arena_chain.hpp"
#include "../../tests/reference_model.hpp"

namespace {

const uint32_t kRefMask = 0x00FFFFFFu, kShadowBit = 0x01000000u;
const size_t kMaxOps = 400;

// ---- small JSON writer (no std::to_string: it is missing in some MinGW builds) ----------
std::string num(int64_t v) {
    if (v == 0) return "0";
    bool neg = v < 0;
    uint64_t u = neg ? static_cast<uint64_t>(-(v + 1)) + 1 : static_cast<uint64_t>(v);
    char b[24];
    int i = 23;
    b[i] = 0;
    while (u) { b[--i] = static_cast<char>('0' + u % 10); u /= 10; }
    if (neg) b[--i] = '-';
    return std::string(b + i);
}
std::string hex64(uint64_t v) {
    static const char* d = "0123456789abcdef";
    std::string s(16, '0');
    for (int i = 15; i >= 0; --i) { s[static_cast<size_t>(i)] = d[v & 15]; v >>= 4; }
    return s;
}
std::string str(const std::string& s) {
    std::string o = "\"";
    for (size_t i = 0; i < s.size(); ++i) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (c == '"' || c == '\\') { o += '\\'; o += static_cast<char>(c); }
        else if (c < 0x20) { o += "\\u00"; o += "0123456789abcdef"[c >> 4]; o += "0123456789abcdef"[c & 15]; }
        else o += static_cast<char>(c);
    }
    return o + "\"";
}
std::string b(bool v) { return v ? "true" : "false"; }

const char* status_name(strata::Status s) {
    switch (s) {
    case strata::kOk: return "kOk";
    case strata::kRedeclared: return "kRedeclared";
    case strata::kNoMemory: return "kNoMemory";
    case strata::kNameTooLong: return "kNameTooLong";
    case strata::kEmptyName: return "kEmptyName";
    case strata::kNoScope: return "kNoScope";
    case strata::kTooDeep: return "kTooDeep";
    case strata::kProbeLimit: return "kProbeLimit";
    }
    return "unknown";
}

bool valid_name(const std::string& s) {
    if (s.empty() || s.size() > 64) return false;
    for (size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        bool alpha = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_';
        if (!(alpha || (i > 0 && c >= '0' && c <= '9'))) return false;
    }
    return true;
}
bool parse_int(const std::string& s, int64_t lo, int64_t hi, int64_t& out) {
    if (s.empty() || s.size() > 12) return false;
    size_t i = 0;
    bool neg = false;
    if (s[0] == '-') { neg = true; i = 1; }
    if (i == s.size()) return false;
    int64_t v = 0;
    for (; i < s.size(); ++i) {
        if (s[i] < '0' || s[i] > '9') return false;
        v = v * 10 + (s[i] - '0');
    }
    if (neg) v = -v;
    if (v < lo || v > hi) return false;
    out = v;
    return true;
}
std::vector<std::string> split(const std::string& line) {
    std::vector<std::string> out;
    std::string cur;
    for (size_t i = 0; i < line.size(); ++i) {
        if (line[i] == ' ') { if (!cur.empty()) out.push_back(cur); cur.clear(); }
        else cur += line[i];
    }
    if (!cur.empty()) out.push_back(cur);
    return out;
}

// ---- reading the table's buffer back ------------------------------------------------
struct Record { uint32_t ref, words; std::string name; int32_t value; uint32_t type, depth; };
struct UndoEntry {
    std::string kind;          // "mark", "new", "shadow"
    uint32_t pos, size;        // position counted in words from the end of the buffer
    std::string name;
    uint32_t slot;             // new: index slot that scope exit will empty
    int32_t value;             // shadow: the hidden declaration
    uint32_t type, depth;
    uint32_t itop;             // mark: identifier-stack top when the scope was entered
};

class Inspector {
public:
    Inspector(const std::vector<uint32_t>& w, const strata::Table& t) : w_(w), t_(t) {}

    void read_layout() {
        strata::Stats s = t_.stats();
        cap_ = static_cast<uint32_t>(s.capacity_bytes / 4);
        idx_ = static_cast<uint32_t>(s.index_bytes / 4);
        itop_ = static_cast<uint32_t>(s.ident_bytes / 4);
        undo_ = static_cast<uint32_t>(s.undo_bytes / 4);
    }
    // meta word: bits 0-6 name words | 7 raw | 8-9 raw length mod 4 | 10-17 type | 18-31 depth
    Record record(uint32_t ref) const {
        const uint32_t* rec = &w_[idx_ + ref];
        Record r;
        r.ref = ref;
        r.value = static_cast<int32_t>(rec[0]);
        const uint32_t meta = rec[1];
        r.words = meta & 0x7Fu;
        r.type = (meta >> 10) & 0xFFu;
        r.depth = meta >> 18;
        if (meta & 0x80u) {                       // raw bytes (not used by the demo's names)
            uint32_t tail = (meta >> 8) & 3u, len = tail ? (r.words - 1) * 4 + tail : r.words * 4;
            const char* p = reinterpret_cast<const char*>(rec + 2);
            r.name.assign(p, len);
            while (!r.name.empty() && r.name[r.name.size() - 1] == 0) r.name.erase(r.name.size() - 1);
        } else {                                  // 6-bit codes, five per word, 0 = padding
            static const char* alphabet = "?abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
            for (uint32_t i = 0; i < r.words; ++i)
                for (int k = 0; k < 5; ++k) {
                    uint32_t c = (rec[2 + i] >> (6 * k)) & 63u;
                    if (c) r.name += alphabet[c];
                }
        }
        return r;
    }
    std::vector<Record> records() const {
        std::vector<Record> out;
        for (uint32_t r = 1; r < itop_;) {
            Record rec = record(r);
            out.push_back(rec);
            r += 2 + rec.words;
        }
        return out;
    }
    // Undo stack, newest entry first. `mark` is the position of the innermost scope mark
    // (0 at the outermost scope); each mark stores the position of the one before it.
    std::vector<UndoEntry> undo(uint32_t mark) const {
        std::vector<UndoEntry> out;
        for (uint32_t pos = undo_; pos > 0;) {
            const uint32_t* e = &w_[cap_ - pos];
            UndoEntry u = UndoEntry();
            u.pos = pos;
            if (pos == mark) {
                u.kind = "mark"; u.size = 2; u.itop = e[0];
                mark = e[1];
            } else if (e[0] & kShadowBit) {
                u.kind = "shadow"; u.size = 3;
                u.name = record(e[0] & kRefMask).name;
                u.value = static_cast<int32_t>(e[1]);
                u.type = (e[2] >> 10) & 0xFFu;
                u.depth = e[2] >> 18;
            } else {
                u.kind = "new"; u.size = 1; u.slot = e[0];
                u.name = record(w_[e[0]] & kRefMask).name;
            }
            out.push_back(u);
            pos -= u.size;
        }
        return out;
    }
    uint32_t idx() const { return idx_; }
    uint32_t slot(uint32_t i) const { return w_[i]; }

private:
    const std::vector<uint32_t>& w_;
    const strata::Table& t_;
    uint32_t cap_ = 0, idx_ = 0, itop_ = 0, undo_ = 0;
};

std::string record_json(const Record& r) {
    return "{\"name\":" + str(r.name) + ",\"value\":" + num(r.value) + ",\"type\":" + num(r.type) +
           ",\"depth\":" + num(r.depth) + ",\"ref\":" + num(r.ref) + ",\"words\":" + num(2 + r.words) + "}";
}
std::string undo_json(const UndoEntry& u) {
    std::string s = "{\"kind\":" + str(u.kind) + ",\"pos\":" + num(u.pos) + ",\"words\":" + num(u.size);
    if (u.kind == "mark") s += ",\"itop\":" + num(u.itop);
    if (u.kind == "new") s += ",\"name\":" + str(u.name) + ",\"slot\":" + num(u.slot);
    if (u.kind == "shadow")
        s += ",\"name\":" + str(u.name) + ",\"value\":" + num(u.value) + ",\"type\":" + num(u.type) + ",\"depth\":" + num(u.depth);
    return s + "}";
}

// The demo keeps a C type in STRATA's 8-bit type tag (0 int, 1 float, 2 char, 3 bool) and
// the value in its 32-bit value field (float as its bit pattern). `int y = x;` with a float x
// converts the way C would.
double to_double(uint32_t tag, int32_t v) {
    if (tag == 1) { float f; std::memcpy(&f, &v, 4); return f; }
    return v;
}
int32_t convert(uint32_t from, int32_t v, uint32_t to) {
    const double d = to_double(from, v);
    switch (to) {
    case 1: { float f = static_cast<float>(d); int32_t r; std::memcpy(&r, &f, 4); return r; }
    case 2: return d < 0 ? 0 : d > 127 ? 127 : static_cast<int32_t>(d);
    case 3: return d != 0 ? 1 : 0;
    default: return d < -2147483648.0 ? INT32_MIN : d > 2147483647.0 ? INT32_MAX : static_cast<int32_t>(d);
    }
}

int fail(const std::string& msg) {
    std::string out = "{\"ok\":false,\"error\":" + str(msg) + "}\n";
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 1;
}

}  // namespace

// ---- TRACE mode: replay a whole compiler trace --------------------------------------------
// Input: "TRACE" then the compiler-trace format of benchmarks/common.hpp (U, E, X, D name,
// L name; G lines are ignored). Every answer of STRATA and of the conventional allocator-free
// table (benchmarks/baselines/arena_chain.hpp) is checked against the reference model, as
// benchmarks/bench_main.cpp does; then both tables are timed in interleaved rounds.
struct TOp { uint8_t kind; uint32_t name; };
enum { T_ENTER, T_EXIT, T_DECLARE, T_LOOKUP, T_UNIT };
const size_t kTraceBytes = 1u << 20;           // 1 MiB fixed buffer: room for every stored trace

struct TraceResult { size_t wrong_lookups = 0, wrong_declares = 0, refused = 0, peak = 0; bool invariants = true; };

struct StrataRunner {
    std::vector<uint32_t> buf = std::vector<uint32_t>(kTraceBytes / 4);
    std::unique_ptr<strata::Table> t;
    void reset() { t.reset(); t.reset(new strata::Table(&buf[0], kTraceBytes)); }
    void enter() { t->enter_scope(); }
    void exit() { t->exit_scope(); }
    int declare(const std::string& n, int32_t v) { int s = t->declare(n.data(), n.size(), v); return s < 0 ? -1 : s; }
    bool resolve(const std::string& n, int32_t* v) const { return t->resolve(n.data(), n.size(), v); }
    size_t peak() const { return t->stats().peak_used_bytes; }
    bool check() const { return t->check_invariants(); }
};
struct ArenaRunner {
    std::vector<uint32_t> buf = std::vector<uint32_t>(kTraceBytes / 4);
    std::unique_ptr<arena_chain::Table> t;
    void reset() { t.reset(); t.reset(new arena_chain::Table(&buf[0], kTraceBytes)); }
    void enter() { t->enter_scope(); }
    void exit() { t->exit_scope(); }
    int declare(const std::string& n, int32_t v) { return t->declare(n.data(), n.size(), v); }
    bool resolve(const std::string& n, int32_t* v) const { return t->resolve(n.data(), n.size(), v); }
    size_t peak() const { return t->peak_used_bytes(); }
    bool check() const { return true; }
};

template <class R>
TraceResult check_trace(R& r, const std::vector<TOp>& ops, const std::vector<std::string>& names) {
    TraceResult res;
    std::unique_ptr<ReferenceModel> model(new ReferenceModel());
    r.reset();
    int32_t seq = 0;
    for (size_t i = 0; i < ops.size(); ++i) {
        const TOp& op = ops[i];
        switch (op.kind) {
        case T_ENTER: r.enter(); model->enter(); break;
        case T_EXIT: r.exit(); model->exit(); break;
        case T_DECLARE: {
            int got = r.declare(names[op.name], seq);
            int want = model->declare(names[op.name], seq);
            ++seq;
            if (got < 0) ++res.refused;
            else if (got != want) ++res.wrong_declares;
            break;
        }
        case T_LOOKUP: {
            int32_t v = -1, mv = -1;
            bool f = r.resolve(names[op.name], &v), mf = model->resolve(names[op.name], &mv);
            if (f != mf || (f && v != mv)) ++res.wrong_lookups;
            break;
        }
        default:
            res.peak = std::max(res.peak, r.peak());
            res.invariants = res.invariants && r.check();
            r.reset(); model.reset(new ReferenceModel()); seq = 0;
            break;
        }
    }
    res.peak = std::max(res.peak, r.peak());
    res.invariants = res.invariants && r.check();
    return res;
}

// Nanosecond clock. Old MinGW's std::chrono clocks are too coarse, so Windows uses QPC.
double now_ns() {
#ifdef _WIN32
    static LARGE_INTEGER f = [] { LARGE_INTEGER x; QueryPerformanceFrequency(&x); return x; }();
    LARGE_INTEGER c;
    QueryPerformanceCounter(&c);
    return static_cast<double>(c.QuadPart) * 1e9 / static_cast<double>(f.QuadPart);
#else
    return static_cast<double>(std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count());
#endif
}

template <class R>
double time_trace(R& r, const std::vector<TOp>& ops, const std::vector<std::string>& names) {
    static volatile int32_t guard = 0;
    const double t0 = now_ns();
    r.reset();
    int32_t seq = 0, sink = 0;
    for (size_t i = 0; i < ops.size(); ++i) {
        const TOp& op = ops[i];
        switch (op.kind) {
        case T_ENTER: r.enter(); break;
        case T_EXIT: r.exit(); break;
        case T_DECLARE: sink += r.declare(names[op.name], seq++); break;
        case T_LOOKUP: { int32_t v = 0; sink += r.resolve(names[op.name], &v) ? v : 0; break; }
        default: r.reset(); seq = 0; break;
        }
    }
    guard = guard + sink;
    return now_ns() - t0;
}

double median(std::vector<double> v) {
    std::sort(v.begin(), v.end());
    return v.size() % 2 ? v[v.size() / 2] : (v[v.size() / 2 - 1] + v[v.size() / 2]) / 2;
}
std::string fixed1(double d) {                 // one decimal, no printf (MinGW's printf is unreliable)
    int64_t t = static_cast<int64_t>(d * 10 + (d < 0 ? -0.5 : 0.5));
    std::string s = num(t / 10) + "." + num((t < 0 ? -t : t) % 10);
    if (t < 0 && t / 10 == 0) s = "-" + s;
    return s;
}
std::string result_json(const TraceResult& r, double ms) {
    return "{\"wrongLookups\":" + num(static_cast<int64_t>(r.wrong_lookups)) + ",\"wrongDeclares\":" + num(static_cast<int64_t>(r.wrong_declares)) +
           ",\"refused\":" + num(static_cast<int64_t>(r.refused)) + ",\"peakBytes\":" + num(static_cast<int64_t>(r.peak)) +
           ",\"invariants\":" + b(r.invariants) + ",\"medianUs\":" + fixed1(ms * 1000) + "}";
}

int trace_mode() {
    std::vector<TOp> ops;
    std::vector<std::string> names;
    std::unordered_map<std::string, uint32_t> ids;
    size_t count[5] = {0, 0, 0, 0, 0};
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line[line.size() - 1] == '\r') line.erase(line.size() - 1);
        if (line.empty()) continue;
        TOp op = {0, 0};
        const char tag = line[0];
        if (line.size() > 1 && line[1] != ' ') continue;
        if (tag == 'E') op.kind = T_ENTER;
        else if (tag == 'X') op.kind = T_EXIT;
        else if (tag == 'U') op.kind = T_UNIT;
        else if (tag == 'D' || tag == 'L') {
            op.kind = tag == 'D' ? T_DECLARE : T_LOOKUP;
            std::string n = line.size() > 2 ? line.substr(2) : "";
            size_t sp = n.find(' ');
            if (sp != std::string::npos) n.erase(sp);
            if (n.empty() || n.size() > 255) continue;
            std::unordered_map<std::string, uint32_t>::iterator it = ids.find(n);
            if (it == ids.end()) { it = ids.insert(std::make_pair(n, static_cast<uint32_t>(names.size()))).first; names.push_back(n); }
            op.name = it->second;
        } else continue;                      // G lines and anything else
        if (op.kind == T_UNIT && ops.empty()) continue;
        ops.push_back(op);
        ++count[op.kind];
    }
    if (ops.empty()) return fail("empty trace");

    StrataRunner s;
    ArenaRunner a;
    const TraceResult rs = check_trace(s, ops, names), ra = check_trace(a, ops, names);
    // Interleaved timing rounds (order alternates), as in bench_main.cpp but fewer rounds.
    const int kRounds = 11;
    std::vector<double> ts, ta, diff;
    time_trace(s, ops, names); time_trace(a, ops, names);   // warm-up
    for (int i = 0; i < kRounds; ++i) {
        double x, y;
        if (i % 2) { y = time_trace(a, ops, names); x = time_trace(s, ops, names); }
        else { x = time_trace(s, ops, names); y = time_trace(a, ops, names); }
        ts.push_back(x); ta.push_back(y); diff.push_back(y > 0 ? (y - x) / y * 100 : 0);
    }
    std::sort(diff.begin(), diff.end());
    const double ms_s = median(ts) / 1e6, ms_a = median(ta) / 1e6;
    std::string out = "{\"ok\":true,\"mode\":\"trace\",\"compiler\":" + str(__VERSION__) + ",\"ops\":" + num(static_cast<int64_t>(ops.size())) +
                      ",\"declares\":" + num(static_cast<int64_t>(count[T_DECLARE])) + ",\"lookups\":" + num(static_cast<int64_t>(count[T_LOOKUP])) +
                      ",\"enters\":" + num(static_cast<int64_t>(count[T_ENTER])) + ",\"units\":" + num(static_cast<int64_t>(count[T_UNIT] + 1)) +
                      ",\"distinctNames\":" + num(static_cast<int64_t>(names.size())) + ",\"bufferBytes\":" + num(static_cast<int64_t>(kTraceBytes)) +
                      ",\"rounds\":" + num(kRounds) + ",\"strata\":" + result_json(rs, ms_s) + ",\"arena\":" + result_json(ra, ms_a) +
                      ",\"timeDiffMedianPct\":" + fixed1(median(diff)) + ",\"timeDiffMinPct\":" + fixed1(diff.front()) +
                      ",\"timeDiffMaxPct\":" + fixed1(diff.back()) + "}\n";
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}

int main() {
    std::vector<std::string> lines;
    std::string line;
    if (std::cin.peek() == 'T') {
        std::getline(std::cin, line);
        if (line == "TRACE" || line == "TRACE\r") return trace_mode();
        return fail("first line must be CAP <bytes> or TRACE");
    }
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line[line.size() - 1] == '\r') line.erase(line.size() - 1);
        if (!line.empty()) lines.push_back(line);
        if (lines.size() > kMaxOps + 1) return fail("too many operations (limit 400)");
    }
    if (lines.empty()) return fail("empty script");
    std::vector<std::string> head = split(lines[0]);
    int64_t cap_bytes = 0;
    if (head.size() != 2 || head[0] != "CAP" || !parse_int(head[1], 128, 65536, cap_bytes) || cap_bytes % 4)
        return fail("first line must be CAP <bytes>, 128..65536, a multiple of 4");

    std::vector<uint32_t> buffer(static_cast<size_t>(cap_bytes / 4), 0u);
    strata::Table table(&buffer[0], static_cast<size_t>(cap_bytes));
    if (!table.valid()) return fail("table could not be created on this buffer");
    std::unique_ptr<ReferenceModel> model(new ReferenceModel());
    std::vector<uint32_t> marks;               // undo-stack position of each open scope's mark
    Inspector ins(buffer, table);
    bool model_agrees = true;

    std::string ops = "[";
    for (size_t li = 1; li < lines.size(); ++li) {
        std::vector<std::string> f = split(lines[li]);
        if (f.empty()) continue;
        const std::string& op = f[0];
        const uint64_t before = table.state_digest();
        const strata::Stats s0 = table.stats();
        std::string o = "{\"op\":" + str(op);
        std::string effect;
        strata::Status st = strata::kOk;
        bool has_status = true;

        if (op == "V") {
            // V name type src: declare `name` initialised from variable `src`, as `int y = x;`
            // compiles: the compiler first resolves src, then declares name.
            int64_t type = 0;
            if (f.size() != 4 || !valid_name(f[1]) || !parse_int(f[2], 0, 255, type) || !valid_name(f[3]))
                return fail("bad declare-from on line " + num(static_cast<int64_t>(li + 1)));
            const std::string& src = f[3];
            int32_t sv = 0, mv = 0;
            uint8_t sty = 0, mt = 0;
            const bool found = table.resolve(src.data(), src.size(), &sv, &sty);
            const bool mfound = model->resolve(src, &mv, &mt);
            if (found != mfound || (found && (sv != mv || sty != mt))) model_agrees = false;
            o += ",\"src\":" + str(src) + ",\"srcFound\":" + b(found);
            if (!found) {
                o += ",\"name\":" + str(f[1]) + ",\"type\":" + num(type);
                effect = "undeclared";
                has_status = false;
            } else {
                const int32_t value = convert(sty, sv, static_cast<uint32_t>(type));
                o += ",\"srcValue\":" + num(sv) + ",\"srcType\":" + num(sty);
                f[0] = "D";
                f[3] = num(value);
            }
        }
        if (f[0] == "D" && effect.empty()) {
            int64_t type = 0, value = 0;
            if (f.size() != 4 || !valid_name(f[1]) || !parse_int(f[2], 0, 255, type) ||
                !parse_int(f[3], INT32_MIN, INT32_MAX, value))
                return fail("bad declare on line " + num(static_cast<int64_t>(li + 1)));
            const std::string& name = f[1];
            st = table.declare(name.data(), name.size(), static_cast<int32_t>(value), static_cast<uint8_t>(type));
            o += ",\"name\":" + str(name) + ",\"type\":" + num(type) + ",\"value\":" + num(value);
            if (st == strata::kOk || st == strata::kRedeclared) {
                int expect = model->declare(name, static_cast<int32_t>(value), static_cast<uint8_t>(type));
                if (expect != static_cast<int>(st)) model_agrees = false;
            }
            const strata::Stats s1 = table.stats();
            if (st == strata::kRedeclared) effect = "redeclared";
            else if (st != strata::kOk) effect = "refused";
            else if (s1.undo_bytes - s0.undo_bytes == 12) {
                effect = "shadow";
                ins.read_layout();
                UndoEntry top = ins.undo(marks.empty() ? 0 : marks.back())[0];
                o += ",\"hidden\":{\"value\":" + num(top.value) + ",\"type\":" + num(top.type) + ",\"depth\":" + num(top.depth) + "}";
            } else {
                effect = "new";
            }
        } else if (op == "V") {
            // undeclared source: reported above, nothing declared
        } else if (op == "L") {
            if (f.size() != 2 || !valid_name(f[1])) return fail("bad lookup on line " + num(static_cast<int64_t>(li + 1)));
            const std::string& name = f[1];
            int32_t v = 0, mv = 0;
            uint8_t t = 0, mt = 0;
            bool found = table.resolve(name.data(), name.size(), &v, &t);
            bool mfound = model->resolve(name, &mv, &mt);
            if (found != mfound || (found && (v != mv || t != mt))) model_agrees = false;
            o += ",\"name\":" + str(name) + ",\"found\":" + b(found);
            if (found) {
                ins.read_layout();
                uint32_t depth = 0;
                std::vector<Record> recs = ins.records();
                for (size_t i = 0; i < recs.size(); ++i) if (recs[i].name == name) depth = recs[i].depth;
                o += ",\"value\":" + num(v) + ",\"type\":" + num(t) + ",\"depth\":" + num(depth);
            }
            effect = found ? "found" : "missing";
            has_status = false;
        } else if (op == "E") {
            st = table.enter_scope();
            if (st == strata::kOk) {
                marks.push_back(static_cast<uint32_t>(table.stats().undo_bytes / 4));
                model->enter();
                effect = "entered";
            } else {
                effect = "refused";
            }
        } else if (op == "X") {
            // What this exit will undo, read from the undo stack before it happens.
            std::string removed = "[", restored = "[";
            if (!marks.empty()) {
                ins.read_layout();
                std::vector<Record> recs = ins.records();
                std::vector<UndoEntry> u = ins.undo(marks.back());
                for (size_t i = 0; i < u.size() && u[i].kind != "mark"; ++i) {
                    int32_t cur_v = 0;
                    uint32_t cur_t = 0, cur_d = 0;
                    for (size_t r = 0; r < recs.size(); ++r)
                        if (recs[r].name == u[i].name) { cur_v = recs[r].value; cur_t = recs[r].type; cur_d = recs[r].depth; }
                    std::string item = "{\"name\":" + str(u[i].name) + ",\"value\":" + num(cur_v) + ",\"type\":" + num(cur_t) +
                                       ",\"depth\":" + num(cur_d);
                    if (u[i].kind == "shadow") {
                        item += ",\"restored\":{\"value\":" + num(u[i].value) + ",\"type\":" + num(u[i].type) + ",\"depth\":" + num(u[i].depth) + "}}";
                        restored += (restored.size() > 1 ? "," : "") + item;
                    } else {
                        removed += (removed.size() > 1 ? "," : "") + item + "}";
                    }
                }
            }
            st = table.exit_scope();
            if (st == strata::kOk) {
                marks.pop_back();
                model->exit();
                effect = "exited";
                o += ",\"removed\":" + removed + "],\"restored\":" + restored + "]";
            } else {
                effect = "refused";
            }
        } else {
            return fail("unknown operation '" + op + "' on line " + num(static_cast<int64_t>(li + 1)));
        }

        const uint64_t after = table.state_digest();
        if (has_status) o += ",\"status\":" + str(status_name(st)) + ",\"code\":" + num(st);
        o += ",\"effect\":" + str(effect) + ",\"changed\":" + b(before != after) + ",\"digestBefore\":" + str(hex64(before)) +
             ",\"digestAfter\":" + str(hex64(after)) + ",\"usedBytes\":" + num(static_cast<int64_t>(table.stats().used_bytes)) +
             ",\"depthAfter\":" + num(static_cast<int64_t>(table.depth())) + "}";
        ops += (ops.size() > 1 ? "," : "") + o;
    }
    ops += "]";

    // ---- final state, read back from the buffer --------------------------------------
    ins.read_layout();
    const strata::Stats s = table.stats();
    std::vector<Record> recs = ins.records();
    std::vector<UndoEntry> undo = ins.undo(marks.empty() ? 0 : marks.back());

    bool resolve_agrees = true;                // every decoded record is what resolve() returns
    std::string records = "[";
    for (size_t i = 0; i < recs.size(); ++i) {
        int32_t v = 0;
        uint8_t t = 0;
        if (!table.resolve(recs[i].name.data(), recs[i].name.size(), &v, &t) || v != recs[i].value || t != recs[i].type)
            resolve_agrees = false;
        records += (i ? "," : "") + record_json(recs[i]);
    }
    records += "]";
    std::string undos = "[";
    for (size_t i = 0; i < undo.size(); ++i) undos += (i ? "," : "") + undo_json(undo[i]);
    undos += "]";
    std::string index = "[";                   // occupied slots: home slot from the table's own hash
    bool first = true;
    for (uint32_t i = 0; i < ins.idx(); ++i) {
        uint32_t w = ins.slot(i);
        if (!w) continue;
        Record r = ins.record(w & kRefMask);
        strata::Key k;
        table.make_key(r.name.data(), r.name.size(), k);
        uint32_t home = k.hash & (ins.idx() - 1);
        index += std::string(first ? "" : ",") + "{\"slot\":" + num(i) + ",\"fp\":" + num(w >> 24) + ",\"ref\":" + num(w & kRefMask) +
                 ",\"name\":" + str(r.name) + ",\"home\":" + num(home) + ",\"probe\":" + num(((i - home) & (ins.idx() - 1)) + 1) + "}";
        first = false;
    }
    index += "]";

    std::string out = "{\"ok\":true,\"engine\":{\"source\":\"frontend/engine/strata_engine.cpp\",\"header\":\"include/strata/strata.hpp\",\"compiler\":" +
                      str(__VERSION__) + ",\"mode\":\"fixed\"},\"capacityBytes\":" + num(cap_bytes) + ",\"stats\":{\"capacity\":" +
                      num(static_cast<int64_t>(s.capacity_bytes)) + ",\"used\":" + num(static_cast<int64_t>(s.used_bytes)) +
                      ",\"peak\":" + num(static_cast<int64_t>(s.peak_used_bytes)) + ",\"index\":" + num(static_cast<int64_t>(s.index_bytes)) +
                      ",\"records\":" + num(static_cast<int64_t>(s.ident_bytes)) + ",\"undo\":" + num(static_cast<int64_t>(s.undo_bytes)) +
                      ",\"free\":" + num(static_cast<int64_t>(s.capacity_bytes - s.used_bytes)) + ",\"liveDeclarations\":" +
                      num(static_cast<int64_t>(s.live_declarations)) + ",\"liveIdentifiers\":" + num(static_cast<int64_t>(s.live_identifiers)) +
                      ",\"depth\":" + num(static_cast<int64_t>(s.depth)) + ",\"indexSlots\":" + num(ins.idx()) + ",\"rebuilds\":" +
                      num(static_cast<int64_t>(s.rebuilds)) + "},\"checks\":{\"invariants\":" + b(table.check_invariants()) +
                      ",\"resolveAgrees\":" + b(resolve_agrees) + ",\"modelAgrees\":" + b(model_agrees) + "},\"digest\":" +
                      str(hex64(table.state_digest())) + ",\"ops\":" + ops + ",\"records\":" + records + ",\"undo\":" + undos +
                      ",\"index\":" + index + "}\n";
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
