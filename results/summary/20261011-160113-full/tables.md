# Result tables for run `20261011-160113-full`

```
run: results/raw/20261011-160113-full
date_utc: 2026-10-11T16:01:38Z
git_commit: 8169bf54ad5b03604e46fc300d2cdd6e4237e2e2
compiler: g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
flags: -std=c++14 -O2
kernel: Linux 6.18.33.2-microsoft-standard-WSL2
cpu: Intel(R) Core(TM) Ultra 7 258V
libc: ldd (Ubuntu GLIBC 2.35-0ubuntu3.15) 2.35
pinning: taskset -c 2
repetitions: 15 (+2 warm-up) whole-trace replays; 3 per-operation latency replays
metis: 7b3dacfa5405ec3e6a03b718f485b473d779123d
phmap: v1.4.1
```

## A. Compiler traces (instrumented TinyCC)

### Workloads

`peak_live_decls`: largest number of simultaneously live declarations in one translation unit.

| trace    |   units |    ops |   declares |   lookups |   enters |   distinct_names |   peak_live_decls |   peak_live_distinct |   max_depth |
|:---------|--------:|-------:|-----------:|----------:|---------:|-----------------:|------------------:|---------------------:|------------:|
| cjson    |       2 |  20874 |       5247 |      9194 |     3216 |             1366 |              1067 |                 1067 |          10 |
| freertos |       9 |  37875 |      10346 |     17417 |     5052 |             2226 |              1505 |                 1505 |          16 |
| littlefs |       2 |  21080 |       3835 |     12230 |     2507 |             1001 |               732 |                  732 |          16 |
| lua      |      34 | 188509 |      58619 |     86887 |    21485 |             3622 |              1365 |                 1365 |          14 |
| mbedtls  |     105 | 983008 |     319886 |    438876 |   112071 |             7622 |              2302 |                 2302 |          14 |
| sqlite   |       1 | 268960 |      27072 |    172426 |    34731 |             7801 |              4245 |                 4245 |          22 |
| tinycc   |       1 |  89135 |      13776 |     54623 |    10368 |             6704 |              5509 |                 5508 |          27 |
| zlib     |      15 |  58058 |      16341 |     27405 |     7149 |             1041 |               571 |                  571 |          23 |

### Correctness

80 table/trace pairs were checked against the reference model; 80 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     42.8 |                 42.8 |                 42.8 |                102.7 |              95.0 |            105.5 |            72.0 |                116.0 |                       109.9 |                      140.5 |
| freertos |     57.8 |                 57.8 |                 57.8 |                217.4 |             135.8 |            166.1 |           116.0 |                147.3 |                       128.7 |                      293.0 |
| littlefs |     25.8 |                 25.8 |                 25.8 |                107.0 |              68.4 |             77.1 |            54.1 |                 67.8 |                        57.0 |                      141.9 |
| lua      |     64.2 |                 64.2 |                 64.2 |                106.8 |              87.5 |            140.2 |            96.7 |                127.7 |                       114.7 |                      142.4 |
| mbedtls  |    144.3 |                144.3 |                144.3 |                234.5 |             234.4 |            270.2 |           189.4 |                277.7 |                       269.3 |                      310.8 |
| sqlite   |    194.7 |                194.7 |                194.7 |                451.1 |             455.4 |            474.4 |           333.1 |                513.5 |                       493.9 |                     1125.5 |
| tinycc   |    324.5 |                324.5 |                324.5 |                423.1 |             545.3 |            585.6 |           424.5 |                550.8 |                       449.6 |                      575.6 |
| zlib     |     17.2 |                 17.2 |                 17.2 |                 52.6 |              43.9 |             61.4 |            44.4 |                 60.3 |                        55.1 |                       71.1 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     41.1 |                 41.1 |                 41.1 |                 98.5 |              91.1 |            101.3 |            69.1 |                111.4 |                       105.5 |                      134.8 |
| freertos |     39.3 |                 39.3 |                 39.3 |                147.9 |              92.4 |            113.0 |            79.0 |                100.2 |                        87.6 |                      199.4 |
| littlefs |     36.0 |                 36.0 |                 36.0 |                149.6 |              95.7 |            107.8 |            75.6 |                 94.8 |                        79.8 |                      198.5 |
| lua      |     48.2 |                 48.2 |                 48.2 |                 80.1 |              65.6 |            105.2 |            72.5 |                 95.8 |                        86.0 |                      106.8 |
| mbedtls  |     64.2 |                 64.2 |                 64.2 |                104.3 |             104.3 |            120.2 |            84.3 |                123.5 |                       119.8 |                      138.3 |
| sqlite   |     47.0 |                 47.0 |                 47.0 |                108.8 |             109.9 |            114.4 |            80.4 |                123.9 |                       119.1 |                      271.5 |
| tinycc   |     60.3 |                 60.3 |                 60.3 |                 78.6 |             101.4 |            108.9 |            78.9 |                102.4 |                        83.6 |                      107.0 |
| zlib     |     30.9 |                 30.9 |                 30.9 |                 94.4 |              78.8 |            110.1 |            79.6 |                108.1 |                        98.9 |                      127.6 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |       22 |                   22 |                   22 |                 3604 |              4182 |             7341 |            7341 |                 5571 |                        5567 |                        344 |
| freertos |       81 |                   85 |                   81 |                 8282 |             10541 |            14903 |           14903 |                12444 |                       12474 |                       2051 |
| littlefs |       19 |                   19 |                   19 |                 2774 |              3192 |             5195 |            5195 |                 4051 |                        4055 |                        246 |
| lua      |      336 |                  341 |                  336 |                40494 |             46774 |            77971 |           77971 |                62526 |                       62639 |                       4408 |
| mbedtls  |     1154 |                 1164 |                 1154 |               255849 |            348278 |           466271 |          466271 |               390914 |                      391205 |                      71187 |
| sqlite   |       15 |                   15 |                   15 |                22711 |             35259 |            39130 |           39130 |                29283 |                       29285 |                       2227 |
| tinycc   |       15 |                   15 |                   15 |                 9665 |             10380 |            18835 |           18835 |                14825 |                       14685 |                       1057 |
| zlib     |      133 |                  133 |                  133 |                10412 |             14127 |            21446 |           21446 |                17657 |                       17710 |                       1532 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `compiler_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     32.6 |                 30.0 |                 32.9 |                 35.0 |             103.1 |             48.7 |            45.1 |                 34.4 |                        37.9 |                       27.2 |
| freertos |     37.6 |                 37.4 |                 37.1 |                 49.7 |             120.1 |             60.3 |            50.9 |                 43.1 |                        47.0 |                       32.9 |
| littlefs |     29.4 |                 29.3 |                 28.8 |                 38.1 |              57.1 |             57.2 |            49.9 |                 31.4 |                        31.9 |                       24.5 |
| lua      |     41.5 |                 44.3 |                 37.6 |                 53.6 |             126.6 |             56.5 |            48.3 |                 44.8 |                        45.6 |                       30.3 |
| mbedtls  |     45.7 |                 42.2 |                 45.9 |                 61.1 |             157.2 |             62.9 |            53.1 |                 53.8 |                        59.1 |                       38.8 |
| sqlite   |     29.4 |                 29.5 |                 28.9 |                 31.1 |              84.7 |             65.8 |            59.3 |                 32.2 |                        33.4 |                       27.6 |
| tinycc   |     33.4 |                 33.8 |                 34.9 |                 34.4 |             340.7 |             71.9 |            59.8 |                 37.5 |                        33.1 |                       25.7 |
| zlib     |     27.0 |                 28.3 |                 30.0 |                 43.1 |              90.1 |             52.5 |            46.0 |                 36.9 |                        47.6 |                       26.0 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     55.7 |                 50.9 |                 56.3 |                 53.9 |              60.0 |            112.0 |           110.2 |                 99.9 |                        48.4 |                       46.6 |
| freertos |     55.7 |                 50.3 |                 57.5 |                 58.7 |              63.0 |            116.9 |           116.9 |                 58.1 |                        52.1 |                       48.4 |
| littlefs |     55.1 |                 52.1 |                 55.1 |                 53.3 |              54.5 |            138.1 |           132.6 |                 55.1 |                        49.7 |                       47.8 |
| lua      |     52.7 |                 56.3 |                 52.7 |                 52.1 |              78.1 |            108.4 |           120.5 |                 56.3 |                        49.1 |                       70.9 |
| mbedtls  |     75.1 |                 67.2 |                 66.6 |                 70.3 |              72.7 |            117.5 |           113.3 |                 78.1 |                        66.0 |                       65.4 |
| sqlite   |     55.7 |                 53.3 |                 56.3 |                 57.5 |              64.8 |            173.8 |           173.2 |                 57.5 |                        56.3 |                       53.9 |
| tinycc   |     61.8 |                 52.1 |                 54.5 |                 51.5 |              74.5 |            246.5 |           156.3 |                 53.9 |                        47.9 |                       53.9 |
| zlib     |     48.4 |                 47.8 |                 49.7 |                 58.7 |              55.7 |            108.4 |           105.4 |                 58.1 |                        46.6 |                       43.6 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     78.1 |                 75.1 |                 78.7 |                150.2 |            1170.6 |            142.3 |           109.6 |                183.5 |                       109.0 |                       77.5 |
| freertos |     81.2 |                 72.1 |                 82.4 |                194.4 |            1086.4 |            152.6 |           107.8 |                119.9 |                       138.7 |                       97.5 |
| littlefs |     81.2 |                 72.1 |                 80.5 |                197.4 |             723.1 |            145.9 |           109.6 |                121.7 |                       109.0 |                       76.3 |
| lua      |     76.9 |                 78.1 |                 76.3 |                161.7 |            1279.0 |            138.1 |           113.9 |                112.0 |                       107.2 |                      118.1 |
| mbedtls  |    101.1 |                 85.4 |                 89.0 |                197.5 |            1397.3 |            178.7 |           123.6 |                147.8 |                       136.9 |                      115.7 |
| sqlite   |     83.6 |                 81.2 |                 83.6 |                182.9 |            3449.5 |            161.1 |           130.2 |                149.6 |                       119.9 |                      113.9 |
| tinycc   |     88.4 |                 78.7 |                 83.6 |                188.4 |            6628.8 |            248.3 |           106.6 |                124.2 |                       105.4 |                       87.8 |
| zlib     |     66.6 |                 68.4 |                 70.8 |                176.8 |             651.6 |            148.4 |           113.8 |                124.7 |                       110.2 |                       77.5 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     95.1 |                 84.2 |                 92.1 |                 60.0 |             167.8 |             52.7 |            47.2 |                184.7 |                       119.3 |                       10.9 |
| freertos |    117.5 |                109.6 |                113.9 |                 90.2 |             243.5 |             80.5 |            57.5 |                150.8 |                       155.6 |                       15.1 |
| littlefs |    119.3 |                112.6 |                115.7 |                 93.9 |             208.3 |             70.9 |            61.2 |                159.9 |                       153.2 |                       18.8 |
| lua      |    114.5 |                118.1 |                113.2 |                 83.0 |             256.2 |             69.0 |            60.0 |                158.1 |                       156.9 |                       23.6 |
| mbedtls  |    176.3 |                164.7 |                160.5 |                110.2 |             290.7 |            110.8 |            76.9 |                234.4 |                       226.5 |                       25.4 |
| sqlite   |    102.4 |                106.0 |                 99.3 |                 71.5 |             232.6 |             77.5 |            64.8 |                147.2 |                       135.7 |                       18.8 |
| tinycc   |    115.7 |                105.4 |                104.8 |                 75.1 |             188.4 |            111.4 |            55.7 |                132.6 |                       121.7 |                       18.8 |
| zlib     |     93.9 |                 95.1 |                 99.9 |                 75.7 |             235.6 |             66.6 |            55.7 |                158.0 |                       141.1 |                       13.3 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. 'intervals overlap = yes' means the 95% intervals of the two replay-time medians overlap, so the time difference is not established.

| trace    |   peak heap KiB old |   new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % | intervals overlap   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|:--------------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| cjson    |               102.7 |  42.8 |               58.3 |         3604 |           22 |            99.4 |             0.7 |             0.7 |             6.6 | yes                 |             53.9 |             55.7 |                -3.3 |                 48.0 |             -58.5 |             0 |
| freertos |               217.4 |  57.8 |               73.4 |         8282 |           81 |            99.0 |             1.9 |             1.4 |            24.3 | no                  |             58.7 |             55.7 |                 5.1 |                 58.2 |             -30.3 |             0 |
| littlefs |               107.0 |  25.8 |               75.9 |         2774 |           19 |            99.3 |             0.8 |             0.6 |            23.0 | no                  |             53.3 |             55.1 |                -3.4 |                 58.9 |             -27.1 |             0 |
| lua      |               106.8 |  64.2 |               39.9 |        40494 |          336 |            99.2 |            10.1 |             7.8 |            22.6 | no                  |             52.1 |             52.7 |                -1.2 |                 52.4 |             -38.0 |             0 |
| mbedtls  |               234.5 | 144.3 |               38.5 |       255849 |         1154 |            99.5 |            60.1 |            44.9 |            25.3 | no                  |             70.3 |             75.1 |                -6.8 |                 48.8 |             -60.0 |             0 |
| sqlite   |               451.1 | 194.7 |               56.8 |        22711 |           15 |            99.9 |             8.4 |             7.9 |             5.5 | yes                 |             57.5 |             55.7 |                 3.1 |                 54.3 |             -43.2 |             0 |
| tinycc   |               423.1 | 324.5 |               23.3 |         9665 |           15 |            99.8 |             3.1 |             3.0 |             2.9 | yes                 |             51.5 |             61.8 |               -20.0 |                 53.1 |             -54.1 |             0 |
| zlib     |                52.6 |  17.2 |               67.3 |        10412 |          133 |            98.7 |             2.5 |             1.6 |            37.3 | no                  |             58.7 |             48.4 |                17.5 |                 62.3 |             -24.0 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        8 |                   23.3 |     57.6 |  75.9 |                      2.9 |      22.8 |   37.3 |
| old arena table           |        8 |                   26.6 |     56.1 |  62.4 |                     48.6 |      68.5 |   90.2 |
| old scope maps            |        8 |                   44.6 |     59.2 |  72.0 |                     26.5 |      43.1 |   55.4 |
| map per scope             |        8 |                   23.6 |     41.0 |  61.2 |                     14.0 |      34.4 |   50.5 |
| std map + undo log        |        8 |                   41.1 |     61.4 |  71.5 |                      5.1 |       9.8 |   26.8 |
| Swiss node map + undo log |        8 |                   27.8 |     55.0 |  68.8 |                     -0.8 |      13.0 |   43.2 |
| Swiss flat map, interned  |        8 |                   43.6 |     72.7 |  82.7 |                    -36.8 |     -18.8 |   -4.0 |

## B. Fixed-buffer mode

### Smallest fixed buffer that replays the whole trace without a refused operation

Found by bisection to 64 bytes. The baselines have no fixed-memory mode; the comparison is with their peak heap.

| trace    |   min buffer KiB (packed) |   min buffer KiB (raw) |   min buffer KiB (sparse index) |   packing saves % |   bytes per live decl |   vs METIS-X (previous) peak heap, red. % |   vs map per scope peak heap, red. % |   vs std map + undo log peak heap, red. % |   vs Swiss flat map, interned peak heap, red. % |
|:---------|--------------------------:|-----------------------:|--------------------------------:|------------------:|----------------------:|------------------------------------------:|-------------------------------------:|------------------------------------------:|------------------------------------------------:|
| cjson    |                      30.0 |                   31.8 |                             nan |               5.5 |                  28.8 |                                      70.8 |                                 58.3 |                                      74.1 |                                            78.6 |
| freertos |                      44.0 |                   47.8 |                             nan |               7.9 |                  29.9 |                                      79.8 |                                 62.1 |                                      70.1 |                                            85.0 |
| littlefs |                      20.0 |                   21.5 |                             nan |               7.0 |                  28.0 |                                      81.3 |                                 63.0 |                                      70.5 |                                            85.9 |
| lua      |                      35.9 |                   38.1 |                             nan |               5.7 |                  27.0 |                                      66.3 |                                 62.8 |                                      71.8 |                                            74.8 |
| mbedtls  |                      80.0 |                   87.9 |                             nan |               9.0 |                  35.6 |                                      65.9 |                                 57.8 |                                      71.2 |                                            74.3 |
| sqlite   |                     140.4 |                  152.9 |                             nan |               8.2 |                  33.9 |                                      68.9 |                                 57.9 |                                      72.7 |                                            87.5 |
| tinycc   |                     156.5 |                  168.3 |                             nan |               7.0 |                  29.1 |                                      63.0 |                                 63.1 |                                      71.6 |                                            72.8 |
| zlib     |                      15.8 |                   16.7 |                             nan |               5.6 |                  28.2 |                                      70.1 |                                 64.5 |                                      73.9 |                                            77.9 |

### Replay time (ms) with a buffer of 1x, 1.25x, 2x and 4x the minimum

Median of 9 replays. Blank: that size was refused (sizing is not perfectly monotonic).

| trace    |   1.00x |   1.25x |   2.00x |   4.00x |
|:---------|--------:|--------:|--------:|--------:|
| cjson    |     0.7 |     0.7 |     0.6 |     0.6 |
| freertos |     1.3 |     1.3 |     1.3 |     1.3 |
| littlefs |     0.6 |     0.6 |     0.6 |     0.7 |
| lua      |     6.5 |     6.7 |     8.4 |     7.5 |
| mbedtls  |    39.0 |    46.4 |    39.1 |    42.6 |
| sqlite   |     7.3 |     7.9 |     7.6 |     7.8 |
| tinycc   |     2.9 |     3.7 |     2.9 |     2.8 |
| zlib     |     1.4 |     1.5 |     1.4 |     1.5 |

## C. Synthetic stress traces

### Workloads

`peak_live_decls`: largest number of simultaneously live declarations in one translation unit.

| trace           |   units |    ops |   declares |   lookups |   enters |   distinct_names |   peak_live_decls |   peak_live_distinct |   max_depth |
|:----------------|--------:|-------:|-----------:|----------:|---------:|-----------------:|------------------:|---------------------:|------------:|
| big_scope_exit  |       1 | 200140 |     200100 |         0 |       20 |            10100 |             10100 |                10100 |           1 |
| deep_nesting    |       1 | 300113 |      89949 |    120134 |    45015 |             3000 |               686 |                  616 |         200 |
| deep_shadow_400 |       1 |   2000 |        400 |       800 |      400 |                1 |               400 |                    1 |         400 |
| dense_50k       |       1 | 250000 |      50000 |    200000 |        0 |            50000 |             50000 |                50000 |           0 |
| long_ids        |       1 | 300000 |      89899 |    180089 |    15006 |             2000 |              1863 |                 1783 |          10 |
| lookup_heavy    |       1 | 300010 |      15097 |    269967 |     7473 |             3000 |               615 |                  612 |          10 |
| scope_churn     |       1 | 330050 |     150050 |    120000 |    30000 |              500 |                55 |                   55 |           1 |
| shadow_heavy    |       1 | 300031 |     134903 |    104922 |    30103 |               24 |               247 |                   24 |          40 |
| short_ids       |       1 | 300005 |      89646 |    180219 |    15070 |             2000 |              1955 |                 1837 |          10 |

### Correctness

90 table/trace pairs were checked against the reference model; 89 had no wrong or refused result.

| trace           | impl    |   wrong_lookups |   wrong_declares |   refused_declares |
|:----------------|:--------|----------------:|-----------------:|-------------------:|
| deep_shadow_400 | metis_x |             298 |                0 |                149 |

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    486.6 |                486.6 |                486.6 |                868.2 |            6289.0 |           1023.8 |           708.1 |                972.4 |                       926.2 |                     1164.5 |
| deep_nesting    |     21.7 |                 21.7 |                 25.8 |                 57.1 |            2974.5 |             92.6 |            71.2 |                 61.0 |                        54.0 |                      264.3 |
| deep_shadow_400 |     11.5 |                 11.5 |                 11.5 |                 40.1 |              34.8 |            103.1 |            90.5 |                 13.3 |                        13.2 |                       10.2 |
| dense_50k       |   2462.9 |               2462.9 |               2462.9 |               6972.3 |            2763.1 |           5351.4 |          3788.7 |               4812.7 |                      4047.9 |                     4671.1 |
| long_ids        |    273.7 |                273.7 |                216.4 |                297.1 |           10427.1 |            307.3 |           249.5 |                269.7 |                       270.3 |                      381.1 |
| lookup_heavy    |     25.8 |                 25.8 |                 25.8 |                 53.6 |             551.2 |             64.3 |            45.0 |                 59.5 |                        53.9 |                      261.0 |
| scope_churn     |      3.9 |                  3.9 |                  3.9 |                  6.4 |            2089.8 |              5.5 |             3.7 |                  4.6 |                         4.9 |                       64.4 |
| shadow_heavy    |      5.0 |                  5.0 |                  5.2 |                 26.7 |            1807.3 |             29.0 |            21.3 |                  7.9 |                         7.6 |                        6.3 |
| short_ids       |     64.2 |                 64.2 |                 64.2 |                200.8 |             599.4 |            189.0 |           127.9 |                151.4 |                       153.5 |                      260.2 |

### Peak heap bytes per live declaration (at the peak)

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     49.3 |                 49.3 |                 49.3 |                 88.0 |             637.6 |            103.8 |            71.8 |                 98.6 |                        93.9 |                      118.1 |
| deep_nesting    |     32.4 |                 32.4 |                 38.4 |                 85.3 |            4440.1 |            138.3 |           106.3 |                 91.1 |                        80.7 |                      394.5 |
| deep_shadow_400 |     29.5 |                 29.5 |                 29.5 |                102.7 |              89.0 |            263.9 |           231.8 |                 34.0 |                        33.8 |                       26.2 |
| dense_50k       |     50.4 |                 50.4 |                 50.4 |                142.8 |              56.6 |            109.6 |            77.6 |                 98.6 |                        82.9 |                       95.7 |
| long_ids        |    150.5 |                150.5 |                118.9 |                163.3 |            5731.3 |            168.9 |           137.1 |                148.3 |                       148.6 |                      209.5 |
| lookup_heavy    |     42.9 |                 42.9 |                 42.9 |                 89.3 |             917.9 |            107.0 |            75.0 |                 99.1 |                        89.8 |                      434.7 |
| scope_churn     |     72.3 |                 72.3 |                 72.3 |                118.5 |           38908.1 |            101.7 |            69.1 |                 85.7 |                        91.3 |                     1198.3 |
| shadow_heavy    |     20.5 |                 20.5 |                 21.5 |                110.8 |            7492.8 |            120.1 |            88.2 |                 32.8 |                        31.5 |                       26.0 |
| short_ids       |     33.6 |                 33.6 |                 33.6 |                105.2 |             314.0 |             99.0 |            67.0 |                 79.3 |                        80.4 |                      136.3 |

### Allocator calls during the whole replay

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      199 |                  199 |                   17 |               104082 |            158610 |           263707 |          263707 |               263527 |                      263531 |                       3216 |
| deep_nesting    |       14 |                   14 |                   10 |               103095 |             88211 |           127642 |          127741 |                97714 |                       85889 |                        304 |
| deep_shadow_400 |       11 |                   11 |                    8 |                  268 |               449 |              811 |             811 |                  422 |                          23 |                         23 |
| dense_50k       |       21 |                   21 |                   21 |                26613 |             38253 |            66587 |           66587 |                66603 |                       66606 |                      16623 |
| long_ids        |       20 |                   20 |                   14 |               130673 |            268615 |           188471 |          194169 |               179824 |                       73138 |                       2042 |
| lookup_heavy    |       10 |                   10 |                   10 |                16720 |             14381 |            21175 |           21256 |                16372 |                       14624 |                        293 |
| scope_churn     |        4 |                    4 |                    4 |               119411 |            119442 |           179448 |          180056 |               150062 |                      134420 |                         29 |
| shadow_heavy    |       93 |                   79 |                    6 |                73820 |             73856 |           138261 |          160027 |               134922 |                         187 |                         28 |
| short_ids       |       12 |                   12 |                   12 |                43608 |             43648 |           100737 |          104041 |                89672 |                       32801 |                         42 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `synthetic_replay_time.csv`.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    142.1 |                137.3 |                 73.1 |                103.8 |            9713.7 |            181.6 |           141.7 |                144.3 |                       104.5 |                       66.4 |
| deep_nesting    |     49.4 |                 47.4 |                 48.8 |                 65.0 |              82.3 |            491.7 |           475.2 |                 56.6 |                        55.3 |                       35.7 |
| deep_shadow_400 |      7.2 |                 14.5 |                  6.8 |                243.5 |             286.5 |             24.8 |            26.1 |                  8.6 |                        11.0 |                        9.3 |
| dense_50k       |     76.7 |                 77.2 |                 75.7 |                 97.7 |           10699.6 |            104.0 |           109.2 |                 97.6 |                        78.7 |                       66.9 |
| long_ids        |     92.4 |                 76.2 |                 93.3 |                145.8 |             197.2 |            188.3 |           162.3 |                 79.2 |                        63.7 |                       57.0 |
| lookup_heavy    |     64.6 |                 48.6 |                 60.4 |                 38.5 |              41.9 |            108.3 |           152.2 |                 45.8 |                        44.0 |                       36.5 |
| scope_churn     |     48.3 |                 45.2 |                 46.9 |                 55.2 |              82.3 |             59.1 |            53.1 |                 64.5 |                        51.0 |                       28.5 |
| shadow_heavy    |     35.8 |                 41.1 |                 41.0 |                 81.6 |             103.6 |             90.5 |            82.7 |                 47.9 |                        36.1 |                       37.1 |
| short_ids       |     40.5 |                 41.0 |                 40.7 |                 54.7 |             138.4 |            112.5 |           106.1 |                 52.9 |                        42.8 |                       35.6 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      0.0 |                  0.0 |                  0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| deep_nesting    |     55.7 |                 50.9 |                 55.7 |                 61.2 |              70.3 |           1993.9 |          1936.3 |                 64.2 |                        61.2 |                       84.2 |
| deep_shadow_400 |     20.0 |                 24.8 |                 20.0 |                503.3 |             750.9 |             21.2 |            19.4 |                 19.4 |                        24.2 |                       24.2 |
| dense_50k       |    225.3 |                233.8 |                214.4 |                308.2 |             309.5 |            469.9 |           321.6 |                312.5 |                       328.2 |                      299.8 |
| long_ids        |    109.0 |                 98.7 |                113.9 |                259.8 |             225.3 |            560.8 |           425.1 |                 95.7 |                        88.4 |                       81.8 |
| lookup_heavy    |     66.0 |                 58.1 |                 80.6 |                 61.8 |              76.9 |            183.5 |           181.1 |                 69.0 |                        50.9 |                       66.0 |
| scope_churn     |     51.5 |                 49.1 |                 51.5 |                 48.5 |              66.0 |            132.6 |            96.3 |                 63.0 |                        46.0 |                       49.1 |
| shadow_heavy    |     41.2 |                 53.9 |                 42.4 |                128.4 |             123.5 |            248.9 |           266.4 |                 46.0 |                        43.6 |                       46.0 |
| short_ids       |     46.6 |                 47.2 |                 47.8 |                 52.7 |             101.1 |            244.1 |           219.9 |                 72.7 |                        53.9 |                      106.6 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     83.6 |                 84.8 |                 95.1 |                167.7 |           21443.9 |            238.0 |           155.6 |                155.6 |                       113.8 |                       90.8 |
| deep_nesting    |     70.3 |                 64.2 |                 70.9 |                196.2 |             170.8 |            152.6 |           119.3 |                102.4 |                        99.9 |                      106.0 |
| deep_shadow_400 |     21.2 |                 35.1 |                 21.2 |                575.9 |             344.0 |            116.9 |            95.7 |                 39.4 |                        35.7 |                       34.5 |
| dense_50k       |     92.1 |                112.6 |                105.4 |                288.9 |          104939.3 |            261.6 |           229.5 |                243.5 |                       172.6 |                      178.7 |
| long_ids        |    119.9 |                113.3 |                126.0 |                404.6 |             493.6 |            328.8 |           199.9 |                159.3 |                       141.1 |                      100.5 |
| lookup_heavy    |    105.4 |                 91.5 |                133.9 |                215.0 |             265.9 |            165.4 |           117.5 |                135.7 |                       103.6 |                      104.2 |
| scope_churn     |     63.0 |                 57.5 |                 62.4 |                129.0 |             107.8 |            139.9 |            77.5 |                 88.4 |                        67.2 |                       60.0 |
| shadow_heavy    |     46.6 |                 59.3 |                 47.8 |                195.0 |             143.5 |            117.5 |           107.2 |                 72.7 |                        56.3 |                       58.7 |
| short_ids       |     58.8 |                 58.1 |                 60.0 |                169.0 |             530.0 |            151.4 |            95.1 |                109.6 |                        92.1 |                      124.8 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  | 381720.8 |             324410.8 |             353627.1 |             512374.6 |          953112.6 |         793476.2 |        447369.5 |             770341.6 |                    650333.7 |                    17116.1 |
| deep_nesting    |    195.6 |                195.6 |                190.8 |                191.4 |             433.7 |            151.4 |           125.4 |                291.9 |                       255.6 |                       27.9 |
| deep_shadow_400 |      7.9 |                  7.9 |                  7.3 |                113.2 |             372.4 |             21.8 |            21.8 |                  4.8 |                         4.8 |                        3.0 |
| dense_50k       |      0.0 |                  0.0 |                  0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| long_ids        |    425.7 |                471.8 |                430.6 |                675.9 |            3666.4 |            575.3 |           477.2 |                679.5 |                       602.0 |                       27.3 |
| lookup_heavy    |    258.0 |                253.2 |                251.4 |                204.7 |             556.0 |            156.9 |           131.4 |                344.0 |                       275.0 |                       31.5 |
| scope_churn     |    166.6 |                168.4 |                164.7 |                119.9 |             485.7 |            112.7 |            64.8 |                264.7 |                       214.4 |                        7.3 |
| shadow_heavy    |     36.9 |                 40.0 |                 36.9 |                196.2 |             611.0 |            154.4 |           134.4 |                 38.8 |                        35.7 |                       28.5 |
| short_ids       |    268.9 |                272.6 |                270.7 |                319.8 |             918.8 |            232.0 |           178.7 |                407.0 |                       342.2 |                       55.1 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. 'intervals overlap = yes' means the 95% intervals of the two replay-time medians overlap, so the time difference is not established.

| trace           |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % | intervals overlap   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:----------------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|:--------------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| big_scope_exit  |               868.2 |  486.6 |               44.0 |       104082 |          199 |            99.8 |            20.8 |            28.4 |           -36.8 | no                  |              0.0 |              0.0 |               nan   |                 50.1 |              25.5 |             0 |
| deep_nesting    |                57.1 |   21.7 |               62.0 |       103095 |           14 |           100.0 |            19.5 |            14.8 |            24.1 | no                  |             61.2 |             55.7 |                 9.0 |                 64.2 |              -2.2 |             0 |
| deep_shadow_400 |                40.1 |   11.5 |               71.3 |          268 |           11 |            95.9 |             0.5 |             0.0 |            97.1 | no                  |            503.3 |             20.0 |                96.0 |                 96.3 |              93.0 |           149 |
| dense_50k       |              6972.3 | 2462.9 |               64.7 |        26613 |           21 |            99.9 |            24.4 |            19.2 |            21.5 | no                  |            308.2 |            225.3 |                26.9 |                 68.1 |             nan   |             0 |
| long_ids        |               297.1 |  273.7 |                7.9 |       130673 |           20 |           100.0 |            43.7 |            27.7 |            36.7 | no                  |            259.8 |            109.0 |                58.0 |                 70.4 |              37.0 |             0 |
| lookup_heavy    |                53.6 |   25.8 |               52.0 |        16720 |           10 |            99.9 |            11.5 |            19.4 |           -67.8 | no                  |             61.8 |             66.0 |                -6.8 |                 51.0 |             -26.0 |             0 |
| scope_churn     |                 6.4 |    3.9 |               39.0 |       119411 |            4 |           100.0 |            18.2 |            16.0 |            12.4 | no                  |             48.5 |             51.5 |                -6.2 |                 51.2 |             -38.9 |             0 |
| shadow_heavy    |                26.7 |    5.0 |               81.5 |        73820 |           93 |            99.9 |            24.5 |            10.7 |            56.1 | no                  |            128.4 |             41.2 |                67.9 |                 76.1 |              81.2 |             0 |
| short_ids       |               200.8 |   64.2 |               68.0 |        43608 |           12 |           100.0 |            16.4 |            12.1 |            26.1 | no                  |             52.7 |             46.6 |                11.6 |                 65.2 |              15.9 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        9 |                    7.9 |     62.0 |  81.5 |                    -67.8 |      24.1 |   97.1 |
| old arena table           |        9 |                   10.9 |     95.3 |  99.8 |                    -54.1 |      65.4 |   99.3 |
| old scope maps            |        9 |                   10.9 |     59.9 |  88.8 |                     18.2 |      50.9 |   90.0 |
| map per scope             |        9 |                   -9.7 |     42.8 |  87.3 |                     -0.3 |      56.7 |   89.6 |
| std map + undo log        |        9 |                   -1.5 |     48.8 |  64.4 |                    -41.1 |      16.8 |   25.3 |
| Swiss node map + undo log |        9 |                   -1.3 |     39.2 |  59.8 |                    -46.7 |       2.5 |   34.7 |
| Swiss flat map, interned  |        9 |                  -12.5 |     58.2 |  94.0 |                   -113.8 |     -38.4 |   23.4 |

## D. Worst-case clustering

### STRATA lookup cost when every key is forced into one probe cluster

Best of 7 rounds, batch-timed. With all keys in one cluster a lookup scans the cluster: cost grows linearly.

|   live_names | hash                 |   ns_per_lookup_hit |   ns_per_lookup_miss |   ns_per_declare |
|-------------:|:---------------------|--------------------:|---------------------:|-----------------:|
|           16 | normal               |                 9.2 |                  8.5 |             89.8 |
|           16 | all_keys_one_cluster |                13.3 |                 16.4 |            118.1 |
|           64 | normal               |                11.1 |                  9.5 |            126.4 |
|           64 | all_keys_one_cluster |                32.9 |                 59.5 |            195.2 |
|          256 | normal               |                11.2 |                  9.4 |             83.0 |
|          256 | all_keys_one_cluster |               117.4 |                234.1 |            356.4 |
|         1024 | normal               |                12.6 |                 10.4 |             74.4 |
|         1024 | all_keys_one_cluster |               402.6 |                809.3 |           1517.4 |
|         4096 | normal               |                15.2 |                 21.8 |             60.0 |
|         4096 | all_keys_one_cluster |              1584.7 |               3302.4 |           4830.5 |

## E. Regex-extracted traces of the earlier work (supplemental)

### Workloads

`peak_live_decls`: largest number of simultaneously live declarations in one translation unit.

| trace    |   units |     ops |   declares |   lookups |   enters |   distinct_names |   peak_live_decls |   peak_live_distinct |   max_depth |
|:---------|--------:|--------:|-----------:|----------:|---------:|-----------------:|------------------:|---------------------:|------------:|
| Arduino  |       1 |   94232 |      31846 |     50273 |     6036 |            11000 |              6936 |                 6936 |          11 |
| ESP-IDF  |       1 | 2229361 |     795847 |   1115502 |   158581 |           231075 |            153522 |               153520 |          11 |
| FreeRTOS |       1 |  227222 |      72376 |    123602 |    15623 |            10386 |              6413 |                 6331 |          10 |
| Zephyr   |       1 | 2605813 |     703727 |   1523992 |   189053 |           228739 |             45930 |                44951 |          21 |

### Correctness

38 table/trace pairs were checked against the reference model; 38 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |    292.0 |                292.0 |                292.0 |                877.0 |             776.7 |            754.1 |           525.7 |                652.9 |                       551.5 |                     1182.0 |
| ESP-IDF  |   7480.9 |               8415.6 |               7480.9 |              15375.6 |             nan   |          19842.3 |         13985.2 |              18289.0 |                     18106.0 |                    41419.9 |
| FreeRTOS |    292.0 |                292.0 |                292.0 |                937.7 |            1158.9 |            758.4 |           535.0 |                651.2 |                       550.3 |                     1230.7 |
| Zephyr   |   1870.3 |               1870.3 |               2216.7 |               7572.0 |             nan   |           5792.2 |          4154.9 |               5211.4 |                      4473.8 |                    19054.6 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.1 |                 43.1 |                 43.1 |                129.5 |             114.7 |            111.3 |            77.6 |                 96.4 |                        81.4 |                      174.5 |
| ESP-IDF  |     49.9 |                 56.1 |                 49.9 |                102.6 |             nan   |            132.3 |            93.3 |                122.0 |                       120.8 |                      276.3 |
| FreeRTOS |     46.6 |                 46.6 |                 46.6 |                149.7 |             185.0 |            121.1 |            85.4 |                104.0 |                        87.9 |                      196.5 |
| Zephyr   |     41.7 |                 41.7 |                 49.4 |                168.8 |             nan   |            129.1 |            92.6 |                116.2 |                        99.7 |                      424.8 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     16.0 |                 16.0 |                 16.0 |              19804.0 |           26299.0 |          35323.0 |         43882.0 |              39468.0 |                     29565.0 |                     3385.0 |
| ESP-IDF  |     24.0 |                 27.0 |                 24.0 |             629511.0 |             nan   |        1032063.0 |       1342739.0 |            1225740.0 |                    860749.0 |                   168333.0 |
| FreeRTOS |     16.0 |                 16.0 |                 16.0 |              32473.0 |           50714.0 |          53727.0 |        115265.0 |             108616.0 |                     41135.0 |                     4786.0 |
| Zephyr   |     25.0 |                 25.0 |                 21.0 |             664319.0 |             nan   |        1056367.0 |       1116929.0 |             974653.0 |                    870284.0 |                   147498.0 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `legacy_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     44.8 |                 49.3 |                 45.6 |                 84.4 |             710.2 |             85.8 |            89.5 |                 53.7 |                        50.6 |                       48.6 |
| ESP-IDF  |     58.6 |                 57.0 |                 56.3 |                 87.3 |             nan   |            148.2 |           167.7 |                162.6 |                       112.6 |                       86.4 |
| FreeRTOS |     41.9 |                 40.5 |                 36.7 |                 52.2 |             600.0 |             56.0 |            64.1 |                 54.1 |                        39.8 |                       39.4 |
| Zephyr   |     46.4 |                 45.8 |                 50.2 |                 70.7 |             nan   |            129.4 |           112.5 |                 84.4 |                        69.9 |                       60.8 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     54.5 |                 47.2 |                 53.9 |                 93.3 |              64.2 |            112.6 |           116.9 |                 70.9 |                        46.0 |                       52.7 |
| ESP-IDF  |     74.5 |                 69.6 |                 81.8 |                 82.4 |             nan   |            162.9 |           176.2 |                108.4 |                        80.5 |                       70.2 |
| FreeRTOS |     63.0 |                 90.8 |                 67.2 |                 68.4 |              76.9 |            118.7 |           126.6 |                 61.2 |                        54.5 |                       75.7 |
| Zephyr   |     73.9 |                 61.8 |                 67.8 |                 78.1 |             nan   |            290.7 |           314.3 |                 84.8 |                        86.6 |                       79.3 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     89.6 |                 87.2 |                 88.4 |                307.0 |            7895.5 |            162.9 |           141.7 |                207.7 |                       115.7 |                      146.5 |
| ESP-IDF  |    169.0 |                172.6 |                172.6 |                373.0 |             nan   |            658.3 |           730.4 |                738.8 |                       363.4 |                      341.6 |
| FreeRTOS |    102.4 |                119.9 |                 95.1 |                182.3 |            5245.0 |            168.4 |           152.6 |                146.0 |                       133.2 |                      136.3 |
| Zephyr   |    155.0 |                159.9 |                144.7 |                324.0 |             nan   |            437.3 |           379.1 |                584.4 |                       320.4 |                      333.1 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |    317.3 |                302.8 |                312.5 |                360.9 |             710.9 |            188.9 |           176.2 |                637.1 |                       444.5 |                       27.3 |
| ESP-IDF  |    310.7 |                313.1 |                327.0 |                285.8 |             nan   |            233.2 |           224.1 |                597.7 |                       462.7 |                       27.3 |
| FreeRTOS |    188.4 |                207.7 |                183.5 |                147.8 |             495.4 |            154.4 |           138.1 |                305.9 |                       290.1 |                       26.6 |
| Zephyr   |    307.7 |                309.5 |                288.3 |                256.2 |             nan   |            278.6 |           253.8 |                548.7 |                       511.2 |                       31.5 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. 'intervals overlap = yes' means the 95% intervals of the two replay-time medians overlap, so the time difference is not established.

| trace    |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % | intervals overlap   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|:--------------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| Arduino  |               877.0 |  292.0 |               66.7 |        19804 |           16 |            99.9 |             8.0 |             4.2 |            46.9 | no                  |             93.3 |             54.5 |                41.6 |                 70.8 |              12.1 |             0 |
| ESP-IDF  |             15375.6 | 7480.9 |               51.3 |       629511 |           24 |           100.0 |           194.6 |           130.5 |            32.9 | no                  |             82.4 |             74.5 |                 9.6 |                 54.7 |              -8.7 |             0 |
| FreeRTOS |               937.7 |  292.0 |               68.9 |        32473 |           16 |           100.0 |            11.9 |             9.5 |            19.8 | yes                 |             68.4 |             63.0 |                 7.9 |                 43.8 |             -27.5 |             0 |
| Zephyr   |              7572.0 | 1870.3 |               75.3 |       664319 |           25 |           100.0 |           184.1 |           120.9 |            34.3 | no                  |             78.1 |             73.9 |                 5.4 |                 52.2 |             -20.1 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        4 |                   51.3 |     67.8 |  75.3 |                     19.8 |      33.6 |   46.9 |
| old arena table           |        2 |                   62.4 |     68.6 |  74.8 |                     93.0 |      93.4 |   93.7 |
| old scope maps            |        4 |                   61.3 |     61.9 |  67.7 |                     25.2 |      54.1 |   64.1 |
| map per scope             |        4 |                   44.5 |     46.0 |  55.0 |                     34.7 |      54.3 |   65.1 |
| std map + undo log        |        4 |                   55.2 |     57.2 |  64.1 |                     16.5 |      33.9 |   64.0 |
| Swiss node map + undo log |        4 |                   46.9 |     52.6 |  58.7 |                     -5.3 |      22.5 |   48.0 |
| Swiss flat map, interned  |        4 |                   75.3 |     79.1 |  90.2 |                     -6.4 |      15.7 |   32.2 |

