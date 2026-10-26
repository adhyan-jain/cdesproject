# Reviewer experiments R13-R16 (memory vs a conventional table without a stored hash; monotonicity; repeated timing sessions)

All of this was run on 2026-10-26/27 (UTC) on branch `reviewer-report-revision`, code base commit `c5d8eb8` plus the uncommitted changes listed in section 1.
Nothing here was copied from the paper; every number comes from `results/review/`. Where a result differs from the paper it is said so in section 0.

## 0. Summary (read this first)

* **R13 (memory).** The ledger prediction holds: the measured smallest buffer of the real C1 table (conventional arena table WITHOUT the stored hash word) equals the `chain_nohash` prediction of `theory/verify/space_model.py` exactly, on all 8 traces. STRATA's saving is **16.4-17.9 % against C0** (paper headline; here 16.38-17.95 %, pooled 17.33 %) but only **5.3-9.0 % against C1** (5.26-9.03 %, median 6.84 %, pooled 7.46 %). The paper's 5-9 % estimate against C1 is confirmed by measurement, and so is the reviewer's point: roughly 11 percentage points of the headline come from the stored hash word of C0, not from STRATA's design. STRATA with raw (unpacked) names needs the same buffer as C1 to within 64 bytes (0 to -0.38 %): the saving against C1 is almost entirely the 5-per-word name packing.
* **R13 (time).** Removing the hash word makes the arena table SLOWER (C1/C0 = 1.04-1.12 in the pooled median, 7 of 8 traces established slower, sqlite not established). STRATA is slower than C0 on every trace (pooled ratio 1.08-1.20, all 8 established; within +-10 % equivalence on none: 6 outside the margin, zlib and sqlite inconclusive). STRATA against C1: ratio 0.995-1.131; 6 of 8 traces are slower by an established amount (cjson 1.04, littlefs 1.11, freertos 1.07, lua 1.07, mbedtls 1.05, tinycc 1.13), zlib and sqlite are not established; equivalence within +-10 % is shown on 6 of 8 traces (not littlefs - inconclusive - and tinycc - outside). STRATA is faster than METIS-X on all 8 traces (ratio 0.69-0.93, all established); keyed STRATA is 1.20-1.28x slower than unkeyed STRATA (all established). The paper's qualitative conclusions on time (STRATA slower than the arena table, faster than METIS-X) are reproduced; no verdict was reversed. The paper's per-trace magnitudes should be replaced by the numbers below because the compiler (g++ 16.2.1 vs 11.4) and machine differ.
* **R14 (monotonicity).** On all 8 traces and all four fixed-buffer tables (STRATA packed, STRATA raw, C0, C1) the scan found **0 non-monotone points**: below the threshold every capacity fails, from the threshold up every capacity succeeds (section 4).
* **R15/R16 (repeatability).** 5 independent sessions, each a fresh process per trace, 31 rounds (+2 warm-up), pinned to cpu 4, 5 minutes apart. Within one session the intervals are narrow, but the absolute times of different sessions differ by up to 1.5x (CPU frequency state, see 6.3), so ratios, not absolute times, are the only comparable quantity; the between-session spread of the ratios is mostly 1-4 % but the per-session medians of STRATA/C0 span 1.058-1.144 on sqlite and 1.149-1.226 on tinycc so that for sqlite STRATA/C0 and STRATA/C1 the session-level evidence is weaker than any single session's interval suggests (section 5).

## 1. What was implemented (files)

| file | content |
|---|---|
| `benchmarks/baselines/arena_chain_nohash.hpp` | **new**: layout C1 = `arena_chain.hpp` with the hash word removed. Entry `[next][value][len\|depth<<16][name words]` = 3+wc words instead of 4+wc. Same MurmurHash3 mixer over the zero-padded name words, same load factor 1 (buckets double when live declarations would exceed buckets), same 1.5x growth in growable mode, same refusal-without-state-change, same 64-byte-resolution bisection. The hash is **recomputed from the stored name** in `exit_scope` (bucket of each popped entry) and in the bucket-array rebuild (re-linking); the chain walk compares length then name words (no hash pre-filter). |
| `benchmarks/baselines/tables.hpp` | added `ArenaChainNoHash` (id `arena_nohash`); nothing else changed. |
| `benchmarks/bench_main.cpp` | registered `ArenaChainNoHash` after `ArenaChain`; added option `--rot K` (default 0 = old behaviour) shifting the rotation of the start order. |
| `benchmarks/budget_main.cpp` | new modes `r13` and `scan`, generic checked replay (variant 4 = C1). Existing modes unchanged. |
| `benchmarks/review_aux.cpp` | `sizes` (control struct sizes) and `timer` (empty interval) |
| `scripts/review_sessions.sh`, `scripts/review_analyze.py` | session driver and statistics |

Correctness of C1: in the growable benchmark (`bench`) the check pass compares every lookup result and declaration status with `tests/reference_model.hpp`; for all traces `wrong_lookups = wrong_declares = refused = 0` for `arena_nohash` (columns in `results/review/sessions/s*/summary.csv`). In fixed-buffer mode every result was compared with the reference model at the smallest buffer for all four tables: 0 wrong, 0 refused; with 64 bytes less each table refuses an operation (`results/review/r13_minbuf.csv`).

Build (everything under `build/review_bench/`; same flags as `scripts/build.sh`, `-std=c++14 -O2 -Wall -Wextra`; METIS-X is the unmodified commit `7b3dacf`, extracted with `git archive` from `/home/adhyan/Desktop/Compiler` because `third_party/` is not in this checkout; parallel-hashmap was not needed):
```
mkdir -p build/review_bench/traces build/review_bench/third_party/metis
git -C /home/adhyan/Desktop/Compiler archive 7b3dacfa5405ec3e6a03b718f485b473d779123d include | tar -x -C build/review_bench/third_party/metis
for f in workloads/traces/*.trace.gz; do b=$(basename $f .trace.gz); case $b in chibicc_*) continue;; esac; gunzip -c $f > build/review_bench/traces/$b.trace; done
g++ -std=c++14 -O2 -Wall -Wextra -DCDES_HAVE_METIS -Ibuild/review_bench/third_party/metis/include -o build/review_bench/bench benchmarks/bench_main.cpp
g++ -std=c++14 -O2 -Wall -Wextra -DSTRATA_TEST_HOOKS -o build/review_bench/budget benchmarks/budget_main.cpp
g++ -std=c++14 -O2 -Wall -Wextra -o build/review_bench/review_aux benchmarks/review_aux.cpp
```
(`budget_main.cpp` defines `STRATA_TEST_HOOKS` itself; the duplicate `-D` gives a harmless redefinition warning, as in `scripts/build.sh`.)

The eight traces are the stored TinyCC traces `workloads/traces/{zlib,cjson,littlefs,freertos,lua,mbedtls,tinycc,sqlite}.trace.gz` (the `chibicc_*` ones are not used); they are the same files as in the paper run `results/raw/20261013-143828-paper/`.

## 2. R13 - smallest fixed buffer (verification of the ledger)

Commands (one per trace, pinned to cpu 4; not timed): 
```
cd build/review_bench
for t in zlib cjson littlefs freertos lua mbedtls tinycc sqlite; do taskset -c 4 ./budget --mode r13 --trace traces/$t.trace --name $t --out ../../results/review/r13_minbuf.csv; done
python3 theory/verify/space_model.py          # prints the ledger prediction next to the paper run's budget.csv
```
Method: bisection to 64-byte resolution of the smallest caller-provided buffer with which the whole trace (a new table per translation unit, all 8 traces' units) replays without a single refused operation. Raw data: `results/review/r13_minbuf.csv` (also peak words used, wrong results, refusals at min-64). Derived: `results/review/r13_savings.csv`. Saving = (baseline - STRATA) / baseline.

#### Smallest fixed buffer (bytes, 64-byte bisection)

| trace | STRATA | STRATA raw | C0 (hash word) | C1 (no hash word) | saving vs C0 | saving vs C1 | C1 vs C0 | raw-name STRATA vs C1 |
|---|---|---|---|---|---|---|---|---|
| zlib | 16128 | 17088 | 19328 | 17024 | 16.56% | 5.26% | 11.92% | -0.38% |
| cjson | 30720 | 32512 | 36736 | 32512 | 16.38% | 5.51% | 11.50% | 0.00% |
| littlefs | 20480 | 22016 | 24832 | 21952 | 17.53% | 6.71% | 11.60% | -0.29% |
| freertos | 45056 | 48896 | 54912 | 48896 | 17.95% | 7.85% | 10.96% | 0.00% |
| lua | 36800 | 39040 | 44480 | 39040 | 17.27% | 5.74% | 12.23% | 0.00% |
| mbedtls | 81920 | 90048 | 99200 | 90048 | 17.42% | 9.03% | 9.23% | 0.00% |
| tinycc | 160256 | 172352 | 194304 | 172288 | 17.52% | 6.98% | 11.33% | -0.04% |
| sqlite | 143744 | 156544 | 173504 | 156480 | 17.15% | 8.14% | 9.81% | -0.04% |

saving_vs_c0_pct: min 16.38, median 17.34, max 17.95; pooled (sum of bytes) 17.33

saving_vs_c1_pct: min 5.26, median 6.84, max 9.03; pooled (sum of bytes) 7.46

c1_vs_c0_pct: min 9.23, median 11.41, max 12.23; pooled (sum of bytes) 10.67


Ledger check (`theory/verify/space_model.py`, columns `arena_chain`, `chain_nohash`): predicted C0 = 19328, 36736, 24832, 54912, 44480, 99200, 194304, 173504 and predicted C1 = 17024, 32512, 21952, 48896, 39040, 90048, 172288, 156480 bytes (zlib ... sqlite). The measured values above are identical in all 16 cases, i.e. the ledger is "exact to 64 bytes" (in fact exact). (The script itself also reports `model==measured` for C0, raw and packed STRATA on all 8 traces against the paper run's `budget.csv`.)

Honest reading: against the conventional baseline WITHOUT the stored hash the saving is 5.3-9.0 %, not 16.4-17.9 %. The larger figure is a comparison with a table that spends one word per declaration on a cached hash. Whether a conventional table stores the hash is a design choice, and C1 is a legitimate baseline. Unlike C0, C1 pays for the saved memory with time (section 5).

## 3. Layout/state accounting for R14: what counts as "buffer"

From `include/strata/strata.hpp`, `benchmarks/baselines/arena_chain*.hpp`, and `results/review/control_struct_sizes.txt`:

* **Buffer (counted in the minimum):** every word of the single caller-supplied block: for STRATA the index slots, identifier records (name + meta + value) and the undo/scope stack; for the arena tables the bucket heads, the entry stack and the scope marks. `peak_used_bytes` (`budget.csv` column `peak_used_bytes_at_min`) is the high-water mark of the words in use; the minimum buffer is that value rounded up to the 64-byte bisection step (it equals it, within 64 bytes, in all rows).
* **Not counted (external, outside the buffer):** the control struct (`sizeof(strata::Table)` = 144 bytes; `arena_chain::Table` and `arena_chain_nohash::Table` = 48 bytes each); the stack temporaries of one operation (STRATA `strata::Key` = 268 bytes; the arena tables' `uint32_t key[64]` = 256 bytes); one process-wide 256-byte character-code table in STRATA (`detail::code_table()`, static, shared by all tables). The key material (the caller-supplied 64-bit key in keyed mode) is in the control struct's `Options`. No scratch space is used outside the buffer. In **fixed mode no heap allocation is made** (only the caller's buffer is touched; the growable mode calls the allocator and is not part of this experiment). The trace data, names and the reference model of the benchmark are the harness's, not the table's.
* Consequently "smallest fixed buffer" compares the data bytes of the structures; a total-footprint comparison would add 144 bytes (STRATA) versus 48 bytes (arena) of control struct plus 268 versus 256 bytes of stack, i.e. a constant of about 100 bytes that does not change with the trace.

## 4. R14 - is "replay succeeds" monotone in the buffer capacity?

Command (per trace; the 5 small traces ran sequentially on cpu 6, tinycc and sqlite on cpus 8 and 10 in parallel - the scan is not timed - and their outputs were concatenated into one file):
```
cd build/review_bench
taskset -c 6 ./budget --mode scan --trace traces/$t.trace --name $t --out ../../results/review/r14_scan.csv --detail ../../results/review/r14_scan_detail.csv
```
Method (`mode_scan` in `benchmarks/budget_main.cpp`): for each of the four tables, first bisect the minimum m, then replay the whole trace at (a) **every capacity from 64 B to 2m at 64-byte resolution**, (b) **every 4 bytes** (the word size; the tables use `bytes/4` words, so this is every distinct capacity) from m-2048 to m+2048, and (c) every 4 KiB from 2m to 8m. "Success" = no refused operation anywhere in the whole trace (all translation units). At every success all lookup results and declaration statuses were compared to the reference model. The buffer was **not** cleared between replays (it holds the garbage of the previous replay), so the result also shows independence from initial contents. Raw per-capacity outcomes: `results/review/r14_scan_detail.csv` (57 645+24 722+26 976 rows). Non-monotone point = a failure at a capacity larger than the smallest success.

| trace | table | bisected min (B) | capacities tested | successes | failures | non-monotone points | wrong results at successes |
|---|---|---|---|---|---|---|---|
| zlib | strata_packed | 16128 | 1553 | 790 | 763 | 0 | 0 |
| zlib | strata_raw | 17088 | 1585 | 821 | 764 | 0 | 0 |
| zlib | arena_C0_hash | 19328 | 1658 | 855 | 803 | 0 | 0 |
| zlib | arena_C1_nohash | 17024 | 1582 | 810 | 772 | 0 | 0 |
| cjson | strata_packed | 30720 | 2031 | 1044 | 987 | 0 | 0 |
| cjson | strata_raw | 32512 | 2089 | 1072 | 1017 | 0 | 0 |
| cjson | arena_C0_hash | 36736 | 2227 | 1142 | 1085 | 0 | 0 |
| cjson | arena_C1_nohash | 32512 | 2089 | 1081 | 1008 | 0 | 0 |
| littlefs | strata_packed | 20480 | 1696 | 868 | 828 | 0 | 0 |
| littlefs | strata_raw | 22016 | 1746 | 905 | 841 | 0 | 0 |
| littlefs | arena_C0_hash | 24832 | 1838 | 939 | 899 | 0 | 0 |
| littlefs | arena_C1_nohash | 21952 | 1744 | 902 | 842 | 0 | 0 |
| freertos | strata_packed | 45056 | 2500 | 1297 | 1203 | 0 | 0 |
| freertos | strata_raw | 48896 | 2625 | 1350 | 1275 | 0 | 0 |
| freertos | arena_C0_hash | 54912 | 2822 | 1456 | 1366 | 0 | 0 |
| freertos | arena_C1_nohash | 48896 | 2625 | 1354 | 1271 | 0 | 0 |
| lua | strata_packed | 36800 | 2229 | 1149 | 1080 | 0 | 0 |
| lua | strata_raw | 39040 | 2303 | 1188 | 1115 | 0 | 0 |
| lua | arena_C0_hash | 44480 | 2481 | 1278 | 1203 | 0 | 0 |
| lua | arena_C1_nohash | 39040 | 2303 | 1190 | 1113 | 0 | 0 |
| mbedtls | strata_packed | 81920 | 3706 | 1915 | 1791 | 0 | 0 |
| mbedtls | strata_raw | 90048 | 3971 | 2058 | 1913 | 0 | 0 |
| mbedtls | arena_C0_hash | 99200 | 4271 | 2219 | 2052 | 0 | 0 |
| mbedtls | arena_C1_nohash | 90048 | 3971 | 2064 | 1907 | 0 | 0 |
| tinycc | strata_packed | 160256 | 6268 | 3262 | 3006 | 0 | 0 |
| tinycc | strata_raw | 172352 | 6664 | 3470 | 3194 | 0 | 0 |
| tinycc | arena_C0_hash | 194304 | 7382 | 3835 | 3547 | 0 | 0 |
| tinycc | arena_C1_nohash | 172288 | 6662 | 3464 | 3198 | 0 | 0 |
| sqlite | strata_packed | 143744 | 5728 | 2976 | 2752 | 0 | 0 |
| sqlite | strata_raw | 156544 | 6147 | 3197 | 2950 | 0 | 0 |
| sqlite | arena_C0_hash | 173504 | 6702 | 3492 | 3210 | 0 | 0 |
| sqlite | arena_C1_nohash | 156480 | 6145 | 3190 | 2955 | 0 | 0 |

Result: **0 non-monotone points and 0 wrong results in all 32 trace x table combinations (about 120 000 capacities)**. All 8 traces were scanned (the request was at least 3). The threshold is sharp and at the word level: the smallest successful capacity equals the table's peak words in use and the capacity 4 bytes below it fails (columns `first_success_bytes`, `last_failure_bytes` in `r14_scan.csv`). Reason (from the code): in fixed mode the layout and every accept/refuse decision are a deterministic function of the operation sequence and of the number of words that would be needed, not of the capacity, so the success predicate is "capacity >= peak words", which is monotone. This was tested only in the fixed (caller-buffer) mode; the growable mode, `index_slots` bounded mode and the sparse variant are not covered, and the scan is for these 8 traces, not a proof. Bisection with 64-byte steps is therefore valid for these tables and traces.

## 5. R15/R16 - replay-time comparison in 5 independent sessions

### 5.1 Protocol

Command (the same for every session; `scripts/review_sessions.sh 5 300 4 31`):
```
scripts/review_sessions.sh 5 300 4 31      # SESSIONS=5, GAP=300 s, CORE=4, REPS=31
```
For each session s = 1..5 the script launches, for each of the 8 traces in a trace order rotated by s-1, a **new process**
```
taskset -c 4 ./build/review_bench/bench --trace build/review_bench/traces/$t.trace --name $t --reps 31 --rot $((s-1)) \
      --impls strata,strata_keyed,arena_chain,arena_nohash,metis_x --summary results/review/sessions/s$s/summary.csv --raw results/review/sessions/s$s/replays.csv
```
and sleeps 300 s before the next session (start times in 6.4: sessions began 19:30:23, 19:35:35, 19:40:47, 19:46:00, 19:51:13 UTC on 2026-10-26, i.e. about 5 min 12 s apart; each session itself took 9-13 s). **31 measured rounds + 2 warm-up as in the existing protocol (no reduction was needed)**: a session is short because the 5 tables are fast on these traces. In each round every table replays the whole trace once (one timed interval per replay, table construction and destruction included), the start table rotates from round to round, and `--rot` additionally shifts the rotation by s-1 so that the table that starts the first round differs between sessions; STRATA ids: `strata` = STRATA default, `strata_keyed` = STRATA with HalfSipHash-1-3 keyed hash, `arena_chain` = C0, `arena_nohash` = C1, `metis_x` = METIS-X. Raw paired rounds: `results/review/sessions/s{1..5}/replays.csv` (trace, impl, round, replay_ns), summaries `summary.csv`, environment per session `context.txt`.

Analysis: `python3 scripts/review_analyze.py results/review > results/review/analysis_tables.md`
(outputs `analysis_per_session.csv`, `analysis_pooled.csv`, `analysis.json`, `r13_savings.csv`, `p95_latency.csv`).

* Statistic: the ratio num/den of the two replay times in the SAME round (paired). Ratio < 1: the first table is faster. Per session: the median of the 31 ratios with a 95 % percentile bootstrap CI (10 000 resamples of rounds, seed fixed in the script). "Difference established" = 95 % CI excludes 1.
* **TOST** equivalence: margin = ratio in [0.90, 1.10] (+-10 %, a stated practical margin, not derived from the data); a pair is "equivalent" if the **90 %** CI lies completely inside the margin (equivalent to two one-sided tests at alpha = 0.05); "outside margin" if the 90 % CI lies completely beyond one bound; otherwise "inconclusive".
* Between-session variability: the min-max of the five per-session medians, SD and DerSimonian-Laird I^2 of them (`analysis_pooled.csv` columns `session_median_min/max`, `between_session_sd_pct`, `I2_pct`).
* **Pooled analysis**: three intervals for the pooled median of log ratio: (t) Student-t interval over the five session medians (df = 4, session = unit of replication; this contains between-session variability; **the verdicts in the tables below use this one**), (boot2) two-level bootstrap (resample sessions, then rounds within sessions), and (rounds) a plain bootstrap of all 155 pooled pairs ignoring sessions (too narrow, kept only to show the difference; in `analysis_pooled.csv`). With only five sessions the t interval is wide-tailed by construction; it is the conservative choice.

The cell format in the tables is `median ratio [95% CI]` for sessions 1 to 5 in order. "pooled median" is the median of all 155 paired ratios; "t-CI95 over sessions" is the 95 % t-interval of the mean of the session log medians (so it is not centred on the pooled median).


#### STRATA / arena C0 (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 1.095 [1.092, 1.107]; 1.127 [1.116, 1.134]; 1.116 [1.109, 1.129]; 1.101 [1.098, 1.107]; 1.126 [1.108, 1.132] | 1.095-1.127 | 1.110 | [1.095, 1.131] | established | [1.099, 1.127] | inconclusive | established / outside margin |
| cjson | 1.142 [1.128, 1.148]; 1.171 [1.168, 1.176]; 1.152 [1.138, 1.163]; 1.169 [1.159, 1.176]; 1.158 [1.152, 1.167] | 1.142-1.171 | 1.158 | [1.143, 1.174] | established | [1.147, 1.170] | outside margin | established / outside margin |
| littlefs | 1.204 [1.193, 1.217]; 1.218 [1.210, 1.228]; 1.204 [1.183, 1.218]; 1.198 [1.186, 1.207]; 1.193 [1.181, 1.198] | 1.193-1.218 | 1.204 | [1.192, 1.215] | established | [1.195, 1.212] | outside margin | established / outside margin |
| freertos | 1.199 [1.184, 1.202]; 1.196 [1.192, 1.200]; 1.168 [1.152, 1.175]; 1.195 [1.193, 1.197]; 1.185 [1.177, 1.191] | 1.168-1.199 | 1.192 | [1.173, 1.204] | established | [1.177, 1.200] | outside margin | established / outside margin |
| lua | 1.161 [1.159, 1.167]; 1.157 [1.156, 1.159]; 1.188 [1.183, 1.199]; 1.189 [1.188, 1.194]; 1.175 [1.166, 1.183] | 1.157-1.189 | 1.176 | [1.156, 1.193] | established | [1.160, 1.188] | outside margin | established / outside margin |
| mbedtls | 1.160 [1.152, 1.169]; 1.168 [1.164, 1.182]; 1.168 [1.138, 1.187]; 1.168 [1.160, 1.182]; 1.165 [1.159, 1.172] | 1.160-1.168 | 1.166 | [1.161, 1.170] | established | [1.162, 1.169] | outside margin | established / outside margin |
| tinycc | 1.204 [1.200, 1.215]; 1.149 [1.145, 1.156]; 1.190 [1.184, 1.197]; 1.180 [1.177, 1.187]; 1.226 [1.208, 1.237] | 1.149-1.226 | 1.191 | [1.154, 1.226] | established | [1.162, 1.217] | outside margin | established / outside margin |
| sqlite | 1.144 [1.141, 1.148]; 1.058 [1.057, 1.060]; 1.083 [1.082, 1.089]; 1.067 [1.064, 1.070]; 1.098 [1.093, 1.103] | 1.058-1.144 | 1.084 | [1.049, 1.132] | established | [1.058, 1.122] | inconclusive | established / inconclusive |

Geometric mean over the 8 traces of the pooled median ratio: 1.159.  t-verdict counts: faster-established 0, slower-established 8, not established 0; TOST equivalent 0, outside margin 6, inconclusive 2.

#### STRATA / arena C1 (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 0.996 [0.985, 1.000]; 1.007 [1.001, 1.018]; 0.996 [0.989, 1.003]; 0.987 [0.980, 0.998]; 0.974 [0.971, 0.983] | 0.974-1.007 | 0.995 | [0.976, 1.007] | not established | [0.980, 1.004] | equivalent | not established / equivalent |
| cjson | 1.043 [1.027, 1.050]; 1.045 [1.044, 1.052]; 1.047 [1.042, 1.054]; 1.043 [1.037, 1.053]; 1.036 [1.025, 1.041] | 1.036-1.047 | 1.043 | [1.038, 1.048] | established | [1.039, 1.047] | equivalent | established / equivalent |
| littlefs | 1.110 [1.105, 1.126]; 1.085 [1.083, 1.096]; 1.116 [1.105, 1.134]; 1.116 [1.112, 1.122]; 1.103 [1.096, 1.130] | 1.085-1.116 | 1.108 | [1.090, 1.122] | established | [1.094, 1.119] | inconclusive | established / inconclusive |
| freertos | 1.083 [1.074, 1.089]; 1.076 [1.074, 1.079]; 1.069 [1.061, 1.080]; 1.056 [1.053, 1.061]; 1.077 [1.068, 1.082] | 1.056-1.083 | 1.072 | [1.059, 1.085] | established | [1.062, 1.082] | equivalent | established / equivalent |
| lua | 1.065 [1.057, 1.068]; 1.047 [1.046, 1.049]; 1.075 [1.067, 1.086]; 1.073 [1.071, 1.079]; 1.069 [1.066, 1.075] | 1.047-1.075 | 1.068 | [1.052, 1.080] | established | [1.055, 1.077] | equivalent | established / equivalent |
| mbedtls | 1.044 [1.039, 1.050]; 1.047 [1.029, 1.071]; 1.051 [1.029, 1.059]; 1.034 [1.024, 1.051]; 1.053 [1.049, 1.057] | 1.034-1.053 | 1.047 | [1.037, 1.055] | established | [1.039, 1.053] | equivalent | established / equivalent |
| tinycc | 1.148 [1.139, 1.154]; 1.110 [1.101, 1.114]; 1.129 [1.127, 1.134]; 1.132 [1.125, 1.137]; 1.138 [1.128, 1.145] | 1.110-1.148 | 1.131 | [1.114, 1.149] | established | [1.118, 1.145] | outside margin | established / outside margin |
| sqlite | 0.982 [0.980, 0.984]; 1.040 [1.038, 1.041]; 1.039 [1.037, 1.046]; 1.030 [1.028, 1.035]; 1.043 [1.037, 1.048] | 0.982-1.043 | 1.037 | [0.995, 1.060] | not established | [1.002, 1.052] | equivalent | not established / equivalent |

Geometric mean over the 8 traces of the pooled median ratio: 1.062.  t-verdict counts: faster-established 0, slower-established 6, not established 2; TOST equivalent 6, outside margin 1, inconclusive 1.

#### arena C1 / arena C0 (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 1.104 [1.096, 1.113]; 1.117 [1.112, 1.120]; 1.123 [1.119, 1.128]; 1.112 [1.109, 1.127]; 1.145 [1.141, 1.153] | 1.104-1.145 | 1.120 | [1.102, 1.139] | established | [1.106, 1.135] | outside margin | established / outside margin |
| cjson | 1.102 [1.091, 1.109]; 1.117 [1.111, 1.123]; 1.099 [1.092, 1.104]; 1.115 [1.111, 1.123]; 1.122 [1.114, 1.132] | 1.099-1.122 | 1.111 | [1.099, 1.123] | established | [1.102, 1.120] | outside margin | established / outside margin |
| littlefs | 1.083 [1.068, 1.092]; 1.124 [1.117, 1.126]; 1.081 [1.065, 1.092]; 1.075 [1.071, 1.080]; 1.072 [1.056, 1.085] | 1.072-1.124 | 1.084 | [1.061, 1.113] | established | [1.067, 1.107] | inconclusive | established / inconclusive |
| freertos | 1.112 [1.101, 1.116]; 1.110 [1.107, 1.114]; 1.085 [1.077, 1.103]; 1.130 [1.126, 1.135]; 1.098 [1.090, 1.105] | 1.085-1.130 | 1.110 | [1.086, 1.128] | established | [1.091, 1.123] | inconclusive | established / inconclusive |
| lua | 1.097 [1.090, 1.099]; 1.103 [1.100, 1.106]; 1.103 [1.100, 1.113]; 1.107 [1.104, 1.109]; 1.096 [1.093, 1.099] | 1.096-1.107 | 1.102 | [1.095, 1.107] | established | [1.097, 1.106] | inconclusive | established / inconclusive |
| mbedtls | 1.114 [1.107, 1.118]; 1.109 [1.102, 1.118]; 1.110 [1.087, 1.114]; 1.121 [1.120, 1.129]; 1.107 [1.105, 1.111] | 1.107-1.121 | 1.112 | [1.105, 1.119] | established | [1.107, 1.118] | outside margin | established / outside margin |
| tinycc | 1.056 [1.046, 1.066]; 1.037 [1.031, 1.052]; 1.050 [1.040, 1.063]; 1.042 [1.040, 1.054]; 1.077 [1.076, 1.088] | 1.037-1.077 | 1.053 | [1.033, 1.072] | established | [1.038, 1.068] | equivalent | established / equivalent |
| sqlite | 1.165 [1.164, 1.168]; 1.017 [1.016, 1.019]; 1.044 [1.042, 1.046]; 1.034 [1.033, 1.036]; 1.052 [1.049, 1.058] | 1.017-1.165 | 1.044 | [0.993, 1.134] | not established | [1.008, 1.117] | inconclusive | established / inconclusive |

Geometric mean over the 8 traces of the pooled median ratio: 1.092.  t-verdict counts: faster-established 0, slower-established 7, not established 1; TOST equivalent 1, outside margin 3, inconclusive 4.

#### STRATA / METIS-X (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 0.767 [0.757, 0.770]; 0.766 [0.762, 0.772]; 0.775 [0.771, 0.777]; 0.767 [0.763, 0.772]; 0.767 [0.763, 0.769] | 0.766-0.775 | 0.769 | [0.764, 0.773] | established | [0.765, 0.772] | outside margin | established / outside margin |
| cjson | 0.823 [0.816, 0.829]; 0.832 [0.828, 0.835]; 0.828 [0.821, 0.832]; 0.827 [0.819, 0.832]; 0.827 [0.823, 0.835] | 0.823-0.832 | 0.828 | [0.823, 0.831] | established | [0.824, 0.830] | outside margin | established / outside margin |
| littlefs | 0.810 [0.803, 0.822]; 0.833 [0.826, 0.840]; 0.820 [0.807, 0.832]; 0.829 [0.822, 0.836]; 0.829 [0.821, 0.836] | 0.810-0.833 | 0.825 | [0.812, 0.836] | established | [0.815, 0.833] | outside margin | established / outside margin |
| freertos | 0.707 [0.704, 0.711]; 0.705 [0.702, 0.707]; 0.708 [0.705, 0.716]; 0.709 [0.707, 0.711]; 0.712 [0.709, 0.715] | 0.705-0.712 | 0.708 | [0.705, 0.712] | established | [0.706, 0.711] | outside margin | established / outside margin |
| lua | 0.762 [0.757, 0.764]; 0.757 [0.755, 0.758]; 0.760 [0.757, 0.764]; 0.755 [0.753, 0.757]; 0.757 [0.755, 0.759] | 0.755-0.762 | 0.757 | [0.755, 0.762] | established | [0.756, 0.761] | outside margin | established / outside margin |
| mbedtls | 0.693 [0.686, 0.701]; 0.689 [0.679, 0.693]; 0.692 [0.683, 0.697]; 0.689 [0.681, 0.694]; 0.692 [0.690, 0.695] | 0.689-0.693 | 0.692 | [0.689, 0.693] | established | [0.689, 0.693] | outside margin | established / outside margin |
| tinycc | 0.902 [0.897, 0.906]; 0.904 [0.900, 0.906]; 0.908 [0.904, 0.910]; 0.904 [0.901, 0.909]; 0.898 [0.891, 0.904] | 0.898-0.908 | 0.904 | [0.899, 0.908] | established | [0.900, 0.907] | inconclusive | established / equivalent |
| sqlite | 0.932 [0.929, 0.935]; 0.931 [0.929, 0.933]; 0.929 [0.927, 0.933]; 0.930 [0.926, 0.930]; 0.929 [0.926, 0.931] | 0.929-0.932 | 0.930 | [0.928, 0.932] | established | [0.929, 0.932] | equivalent | established / equivalent |

Geometric mean over the 8 traces of the pooled median ratio: 0.798.  t-verdict counts: faster-established 8, slower-established 0, not established 0; TOST equivalent 1, outside margin 6, inconclusive 1.

#### STRATA keyed / STRATA (ratio of replay times; < 1 means the first is faster)

| trace | per-session median ratio [95% CI] | between-session range | pooled median | t-CI95 over sessions | difference | 90% CI (t) | TOST +-10% | boot2 diff / TOST |
|---|---|---|---|---|---|---|---|---|
| zlib | 1.278 [1.269, 1.292]; 1.275 [1.267, 1.280]; 1.314 [1.308, 1.318]; 1.276 [1.264, 1.281]; 1.280 [1.267, 1.292] | 1.275-1.314 | 1.284 | [1.264, 1.305] | established | [1.269, 1.300] | outside margin | established / outside margin |
| cjson | 1.236 [1.222, 1.259]; 1.239 [1.236, 1.245]; 1.237 [1.232, 1.245]; 1.240 [1.226, 1.250]; 1.244 [1.234, 1.260] | 1.236-1.244 | 1.238 | [1.235, 1.243] | established | [1.236, 1.242] | outside margin | established / outside margin |
| littlefs | 1.299 [1.280, 1.308]; 1.272 [1.263, 1.281]; 1.287 [1.260, 1.305]; 1.284 [1.276, 1.294]; 1.288 [1.275, 1.306] | 1.272-1.299 | 1.284 | [1.274, 1.298] | established | [1.276, 1.295] | outside margin | established / outside margin |
| freertos | 1.234 [1.230, 1.243]; 1.237 [1.231, 1.240]; 1.243 [1.236, 1.254]; 1.238 [1.237, 1.241]; 1.233 [1.230, 1.237] | 1.233-1.243 | 1.237 | [1.232, 1.242] | established | [1.233, 1.241] | outside margin | established / outside margin |
| lua | 1.212 [1.207, 1.219]; 1.210 [1.206, 1.212]; 1.208 [1.204, 1.213]; 1.212 [1.210, 1.214]; 1.214 [1.210, 1.218] | 1.208-1.214 | 1.211 | [1.209, 1.214] | established | [1.209, 1.213] | outside margin | established / outside margin |
| mbedtls | 1.245 [1.237, 1.257]; 1.241 [1.232, 1.248]; 1.243 [1.224, 1.263]; 1.244 [1.224, 1.248]; 1.242 [1.235, 1.253] | 1.241-1.245 | 1.243 | [1.241, 1.245] | established | [1.241, 1.244] | outside margin | established / outside margin |
| tinycc | 1.202 [1.194, 1.209]; 1.203 [1.200, 1.206]; 1.203 [1.198, 1.205]; 1.208 [1.196, 1.210]; 1.214 [1.207, 1.227] | 1.202-1.214 | 1.204 | [1.200, 1.212] | established | [1.201, 1.211] | outside margin | established / outside margin |
| sqlite | 1.225 [1.220, 1.229]; 1.223 [1.221, 1.225]; 1.222 [1.218, 1.225]; 1.223 [1.216, 1.226]; 1.224 [1.219, 1.227] | 1.222-1.225 | 1.224 | [1.222, 1.225] | established | [1.222, 1.224] | outside margin | established / outside margin |

Geometric mean over the 8 traces of the pooled median ratio: 1.240.  t-verdict counts: faster-established 0, slower-established 8, not established 0; TOST equivalent 0, outside margin 8, inconclusive 0.


### 5.2 Median replay times per session (ms)

The absolute medians differ a lot between sessions (e.g. mbedtls STRATA 23.2 to 34.9 ms), so only paired ratios within a session are interpreted. 

#### Median replay time per session (ms)

| trace | session | strata | strata_keyed | arena_chain | arena_nohash | metis_x |
|---|---|---|---|---|---|---|
| zlib | 1 | 1.110 | 1.420 | 1.017 | 1.124 | 1.462 |
| zlib | 2 | 1.395 | 1.781 | 1.244 | 1.383 | 1.823 |
| zlib | 3 | 1.395 | 1.830 | 1.251 | 1.401 | 1.804 |
| zlib | 4 | 1.412 | 1.793 | 1.275 | 1.424 | 1.834 |
| zlib | 5 | 1.094 | 1.403 | 0.978 | 1.122 | 1.430 |
| cjson | 1 | 0.418 | 0.520 | 0.367 | 0.404 | 0.505 |
| cjson | 2 | 0.591 | 0.732 | 0.508 | 0.566 | 0.712 |
| cjson | 3 | 0.560 | 0.691 | 0.482 | 0.534 | 0.673 |
| cjson | 4 | 0.651 | 0.800 | 0.554 | 0.620 | 0.782 |
| cjson | 5 | 0.412 | 0.512 | 0.354 | 0.397 | 0.496 |
| littlefs | 1 | 0.435 | 0.560 | 0.362 | 0.391 | 0.536 |
| littlefs | 2 | 0.589 | 0.749 | 0.482 | 0.540 | 0.705 |
| littlefs | 3 | 0.442 | 0.565 | 0.363 | 0.391 | 0.533 |
| littlefs | 4 | 0.660 | 0.848 | 0.549 | 0.590 | 0.793 |
| littlefs | 5 | 0.435 | 0.562 | 0.367 | 0.391 | 0.525 |
| freertos | 1 | 0.880 | 1.086 | 0.735 | 0.813 | 1.246 |
| freertos | 2 | 1.237 | 1.530 | 1.033 | 1.148 | 1.754 |
| freertos | 3 | 0.885 | 1.100 | 0.754 | 0.827 | 1.250 |
| freertos | 4 | 1.027 | 1.274 | 0.861 | 0.974 | 1.451 |
| freertos | 5 | 0.867 | 1.074 | 0.736 | 0.805 | 1.220 |
| lua | 1 | 4.213 | 5.112 | 3.623 | 3.959 | 5.529 |
| lua | 2 | 5.296 | 6.407 | 4.579 | 5.050 | 6.984 |
| lua | 3 | 4.271 | 5.164 | 3.600 | 3.963 | 5.628 |
| lua | 4 | 5.912 | 7.155 | 4.965 | 5.513 | 7.827 |
| lua | 5 | 4.185 | 5.080 | 3.554 | 3.898 | 5.510 |
| mbedtls | 1 | 31.682 | 39.844 | 27.471 | 30.102 | 46.152 |
| mbedtls | 2 | 31.088 | 38.762 | 26.706 | 29.383 | 45.012 |
| mbedtls | 3 | 33.971 | 41.289 | 28.962 | 32.235 | 47.866 |
| mbedtls | 4 | 34.920 | 43.613 | 29.493 | 33.294 | 50.259 |
| mbedtls | 5 | 23.228 | 29.051 | 19.899 | 22.048 | 33.537 |
| tinycc | 1 | 2.969 | 3.578 | 2.443 | 2.594 | 3.345 |
| tinycc | 2 | 2.319 | 2.796 | 2.005 | 2.100 | 2.583 |
| tinycc | 3 | 2.598 | 3.118 | 2.202 | 2.296 | 2.873 |
| tinycc | 4 | 2.439 | 2.931 | 2.055 | 2.162 | 2.694 |
| tinycc | 5 | 1.855 | 2.250 | 1.516 | 1.633 | 2.063 |
| sqlite | 1 | 7.133 | 8.703 | 6.224 | 7.262 | 7.637 |
| sqlite | 2 | 6.210 | 7.588 | 5.857 | 5.966 | 6.654 |
| sqlite | 3 | 7.659 | 9.328 | 7.011 | 7.325 | 8.271 |
| sqlite | 4 | 6.692 | 8.212 | 6.285 | 6.503 | 7.208 |
| sqlite | 5 | 4.973 | 6.096 | 4.537 | 4.768 | 5.374 |


### 5.3 What the timing results say

* STRATA vs C0 (stored hash): STRATA is slower on every trace, ratio 1.08-1.20 (pooled medians 1.110, 1.158, 1.204, 1.192, 1.176, 1.166, 1.191, 1.084), all 8 differences established; geometric mean 1.159. Equivalence within +-10 % holds on none (6 outside the margin, zlib and sqlite inconclusive).
* STRATA vs C1 (real no-hash table): ratio 0.995-1.131, geometric mean 1.062. Slower by an established amount on 6 traces, not established on zlib and sqlite. TOST equivalence within +-10 % on zlib, cjson, freertos, lua, mbedtls, sqlite; inconclusive on littlefs; outside the margin (slower) on tinycc (1.131). Thus the time gap to the arena table shrinks from about 16 % to about 6 % when the stored hash is removed from the baseline, because C1 itself is about 9 % slower than C0 (geometric mean 1.092; 7 of 8 established; C1 is not equivalent to C0 within +-10 % on 3 traces, inconclusive on 4, equivalent on tinycc).
* STRATA vs METIS-X: ratio 0.69-0.93 (STRATA faster, all 8 established); equivalence only on sqlite (0.930), tinycc inconclusive. Keyed STRATA vs unkeyed: 1.20-1.28, all established and outside the margin.
* Between-session variability: SD of the session-median ratios is below 1.3 % for METIS-X and keyed comparisons and 1-4 % for the arena comparisons, with large outliers on sqlite (STRATA/C0 session medians 1.058-1.144; C1/C0 1.017-1.165; STRATA/C1 0.982-1.043) and tinycc (STRATA/C0 1.149-1.226). The cause was not isolated; CPU frequency state (6.3) is a plausible but untested candidate. Heterogeneity is also visible in `I2_pct` (up to 95 % for zlib keyed/unkeyed, because the within-session CIs are very narrow). Verdicts with the 'not established' label (STRATA vs C1 on zlib and sqlite; C1 vs C0 on sqlite) are exactly the ones where session heterogeneity matters.
* Compared with the paper: the paper's verdicts of "STRATA slower than the arena table, faster than METIS-X" are reproduced. New with C1: the speed gap to a hash-less arena table is smaller and on zlib/sqlite not established.

### 5.4 p95 per-operation latency (secondary)

Median over the five sessions of the lookup p95 in ns (min-max over sessions in brackets). Sampling: `run_impl` in `bench_main.cpp` replays the trace three times with an `rdtscp` read before and after every single operation; samples of one operation kind are collected over **the whole trace, all translation units pooled** (the table is rebuilt at each `U` record but the sample vector is not reset), the p95 is `nth_element` at index floor(0.95 (n-1)) of the whole vector, the timer overhead (median of 4001 back-to-back `rdtscp` pairs, about 13 ns) is subtracted and the median of the three replays' p95 is stored. No per-unit aggregation is done. These values are within a few times the timer overhead and its tick (0.34 ns) and are meaningful only for comparing tables; `p95_latency.csv` has declare/enter/exit as well.

| trace | STRATA | arena C0 | arena C1 | METIS-X | STRATA keyed |
|---|---|---|---|---|---|
| zlib | 41.1 (32.2-43.9) | 39.1 (30.2-41.1) | 41.8 (32.2-42.5) | 38.4 (29.5-39.1) | 49.3 (37.7-52.1) |
| cjson | 46.6 (37.0-54.1) | 42.5 (34.3-49.3) | 43.9 (35.0-50.7) | 43.9 (34.3-50.0) | 54.1 (43.9-63.0) |
| littlefs | 38.4 (37.0-57.6) | 33.6 (32.2-50.0) | 32.9 (32.2-48.0) | 33.6 (33.6-51.4) | 45.2 (43.9-67.8) |
| freertos | 41.1 (39.7-56.9) | 37.0 (36.3-51.4) | 38.4 (37.7-53.5) | 39.1 (38.4-55.5) | 48.7 (48.0-67.2) |
| lua | 37.0 (36.3-48.7) | 35.6 (34.3-44.5) | 37.7 (35.6-45.9) | 35.6 (34.3-43.2) | 42.5 (41.8-55.5) |
| mbedtls | 49.3 (41.8-63.7) | 47.3 (40.4-64.4) | 47.3 (40.4-63.7) | 47.3 (42.5-65.8) | 61.7 (51.4-74.7) |
| tinycc | 48.0 (37.7-54.1) | 41.1 (33.6-49.3) | 42.5 (31.5-47.3) | 46.6 (35.0-52.8) | 55.5 (43.9-62.4) |
| sqlite | 48.7 (36.3-57.6) | 50.7 (35.6-66.5) | 50.0 (35.6-56.9) | 52.1 (37.0-58.3) | 58.9 (43.2-71.3) |

## 6. Measurement description and environment

### 6.1 Timer, batching, overhead
* **Replay time:** `std::chrono::steady_clock` (libstdc++: `clock_gettime(CLOCK_MONOTONIC)`, resolution 1 ns per `clock_getres`), one interval per whole-trace replay, **no batching** of replays inside an interval; table construction and destruction are inside the interval. Replay times are 0.35 ms to 50 ms, so the timer overhead (20 ns) is below 0.01 % of every interval and was not subtracted.
* **Empty-timer overhead** (`review_aux timer`, 200 001 samples, cpu 4, `results/review/timer_overhead.txt`): `steady_clock` pair: median 20.0 ns (min 17, p99 22); raw `clock_gettime`: median 18 ns; `rdtscp` pair: median 13.0 ns (0.3427 ns/tick, calibrated against `steady_clock` over 100 ms).
* **Per-operation latency** uses `rdtscp` with the median pair overhead subtracted (section 5.4).
* A volatile `guard`/`sink` keeps the compiler from removing lookups; the first 2 rounds are discarded as warm-up.

### 6.2 Machine
```
uname -a: Linux adhyan-omarchy 7.2.4-arch1-2 #1 SMP PREEMPT_DYNAMIC Tue, 08 Sep 2026 10:22:31 +0000 x86_64 GNU/Linux
g++: g++ (GCC) 16.2.1 20260810
cpu:  13th Gen Intel(R) Core(TM) i7-13620H
ldd: ldd (GNU libc) 2.44
python: Python 3.14.7 numpy 2.5.2
git: c5d8eb8ae9f313001181b73ef76c54f2376714c8 branch reviewer-report-revision
metis: 7b3dacfa5405ec3e6a03b718f485b473d779123d (git archive from /home/adhyan/Desktop/Compiler)
date: 2026-10-26T19:30:29Z
CPU max MHz:                             4900.0000
CPU min MHz:                             400.0000
L1d cache:                               416 KiB (10 instances)
L2 cache:                                9.5 MiB (7 instances)
L3 cache:                                24 MiB (1 instance)
```
`uname -a`, CPU, compiler and library as above. Differences from the paper's environment: **native Linux (Arch), not WSL2**; kernel 7.2.4-arch1-2 instead of 6.18.33.2-microsoft-standard-WSL2; CPU i7-13620H (Raptor Lake, 6 P + 4 E cores, 16 threads) instead of Core Ultra 7 258V; **g++ 16.2.1 instead of 11.4.0**; glibc 2.44 instead of 2.35. The compiler change matters for absolute and possibly relative timing and for `malloc_usable_size`-based heap figures (not used here: the memory results of this document are the fixed-buffer word counts, which are compiler-independent and did reproduce the ledger and the paper run's STRATA/C0 minima).

### 6.3 Frequency governor, pinning, other load
* cpufreq driver `intel_pstate`, **governor `powersave`** (the only intel_pstate governors are `powersave` and `performance`; I did not change it: no root), energy_performance_preference `performance`, `no_turbo = 0` (turbo allowed), cpuinfo max 4.9 GHz, min 0.4 GHz. So the frequency is NOT fixed: it ramps up under load. `scaling_cur_freq` of cpu 4 sampled at session start/end: 4.70 GHz / 0.40 GHz (s1), 0.61 / 0.40 (s2), 3.43 / 3.12 (s3), 0.62 / 3.20 (s4), 1.50 / 0.40 GHz (s5) - the end-of-session samples mostly show the idle drop after the run, but the start values show the core was not in a steady state at launch. This is a plausible, untested cause of the large differences in absolute time between sessions (up to 1.5x) and of part of the between-session ratio variability (not tested separately). Rounds inside a process interleave all tables, which is why ratios are much more stable than times.
* **Pinning:** `taskset -c 4` (logical cpu 4; its SMT sibling is cpu 5). Not isolated: no `isolcpus`, no `nohz_full`; the sibling hardware thread can be used by other processes, and was only lightly used (1.4-5.8 % busy over the sessions; the pinned cpu was 99.5-99.9 % busy).
* **Background load:** the machine is a desktop shared with a browser, a desktop session and, during preparation (not during the timing sessions), other long-running test jobs of the same project (load average 4-10 at that time). During the 5 timing sessions the coordinator ran no heavy jobs; the load average at session start was 0.40-2.54 (below); `busy_processes_start` in `context.txt` lists processes using at least 20 % of a cpu. The first list may include my own script's helper commands. This is an uncontrolled environment, not a quiet benchmark rig.

### 6.4 Per-session context (verbatim `context.txt`)
### Session 1
```
session: 1 of 5
start_utc: 2026-10-26T19:30:23Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 0
loadavg_start: 0.73 1.26 1.95 8/3172 419298
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 4700000
busy_processes_start (>=20% cpu, excluding this script):
 419242   4 66.6 MainThread
 419241  10 33.3 MainThread
 419243   8 33.3 MainThread
end_utc: 2026-10-26T19:30:35Z
loadavg_end: 0.85 1.27 1.95 1/3133 421475
cur_freq_khz_end: 400222
pinned_cpu4_busy_fraction_over_session: 0.997
sibling_cpu5_busy_fraction_over_session: 0.048
```
### Session 2
```
session: 2 of 5
start_utc: 2026-10-26T19:35:35Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 1
loadavg_start: 0.45 0.82 1.56 3/3128 462901
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 606321
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:35:47Z
loadavg_end: 1.09 0.95 1.59 1/3133 464905
cur_freq_khz_end: 400350
pinned_cpu4_busy_fraction_over_session: 0.999
sibling_cpu5_busy_fraction_over_session: 0.050
```
### Session 3
```
session: 3 of 5
start_utc: 2026-10-26T19:40:47Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 2
loadavg_start: 1.09 1.04 1.45 1/3136 508921
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 3430728
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:41:00Z
loadavg_end: 1.30 1.09 1.46 8/3127 510299
cur_freq_khz_end: 3123973
pinned_cpu4_busy_fraction_over_session: 0.998
sibling_cpu5_busy_fraction_over_session: 0.058
```
### Session 4
```
session: 4 of 5
start_utc: 2026-10-26T19:46:00Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 3
loadavg_start: 2.54 1.51 1.49 2/3152 549770
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 621541
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:46:13Z
loadavg_end: 2.65 1.59 1.52 4/3137 551184
cur_freq_khz_end: 3200032
pinned_cpu4_busy_fraction_over_session: 0.996
sibling_cpu5_busy_fraction_over_session: 0.043
```
### Session 5
```
session: 5 of 5
start_utc: 2026-10-26T19:51:13Z
core: 4 (sibling hardware thread: 5)
rotation_offset (--rot): 4
loadavg_start: 0.40 0.90 1.23 2/3112 580450
governor: powersave  epp: performance  no_turbo: 0
cur_freq_khz_start: 1502325
busy_processes_start (>=20% cpu, excluding this script):
end_utc: 2026-10-26T19:51:22Z
loadavg_end: 0.57 0.92 1.24 2/3118 581325
cur_freq_khz_end: 400137
pinned_cpu4_busy_fraction_over_session: 0.995
sibling_cpu5_busy_fraction_over_session: 0.014
```

## 7. Limitations (additional to the paper's)
* 5 sessions within about 25 minutes of one afternoon on one machine; sessions are independent processes but not days apart. The t-intervals have 4 degrees of freedom.
* The CPU frequency was not fixed (powersave governor, no root), the system was not isolated, and a different compiler than in the paper was used. The ratios, not the absolute times, are reportable.
* The TOST margin of +-10 % is a practical choice, not derived from an application requirement; with +-5 % none of the 'equivalent' labels for STRATA/C1 would survive on most traces (the 90 % CIs are 0.98-1.06).
* Replay is not compilation; hashing/compare cost differences between C0 and C1 depend on name length distribution of these 8 traces.
* Monotonicity is shown empirically for fixed mode on 8 traces; it is not a proof.
* The paper's `results/raw/20261013-143828-paper` data and manuscript were not modified by this work.

## 8. Files
`results/review/`: `r13_minbuf.csv`, `r13_savings.csv`, `r14_scan.csv`, `r14_scan_detail.csv`, `sessions/s1..s5/{replays,summary}.csv + context.txt`, `sessions_run.log`, `analysis_per_session.csv`, `analysis_pooled.csv`, `analysis.json`, `analysis_tables.md`, `p95_latency.csv`, `timer_overhead.txt`, `control_struct_sizes.txt`, `environment.txt`.
