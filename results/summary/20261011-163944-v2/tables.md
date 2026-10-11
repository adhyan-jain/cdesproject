# Result tables for run `20261011-163944-v2`

```
run: results/raw/20261011-163944-v2
date_utc: 2026-10-11T16:40:20Z
git_commit: e5118190cf8bc28469efd4af7b0a10dbc5d5de6a
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

88 table/trace pairs were checked against the reference model; 88 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     42.8 |                 42.8 |                 42.8 |                    42.8 |                102.7 |              95.0 |            105.6 |            72.0 |                116.1 |                       109.9 |                      140.4 |
| freertos |     57.8 |                 57.8 |                 57.8 |                    57.8 |                217.4 |             135.8 |            166.1 |           116.0 |                147.3 |                       128.8 |                      293.1 |
| littlefs |     25.8 |                 25.8 |                 25.8 |                    25.8 |                106.9 |              68.4 |             77.1 |            54.1 |                 67.8 |                        57.2 |                      141.9 |
| lua      |     64.2 |                 64.2 |                 64.2 |                    96.2 |                106.8 |              87.5 |            140.2 |            96.7 |                127.7 |                       114.8 |                      142.3 |
| mbedtls  |    144.3 |                144.3 |                144.3 |                   144.3 |                234.4 |             234.4 |            270.1 |           189.4 |                277.7 |                       269.3 |                      310.8 |
| sqlite   |    194.7 |                194.7 |                194.7 |                   194.7 |                451.1 |             455.4 |            474.5 |           333.1 |                513.5 |                       494.0 |                     1125.5 |
| tinycc   |    324.5 |                324.5 |                324.5 |                   324.5 |                423.1 |             545.3 |            585.6 |           424.5 |                550.9 |                       449.5 |                      575.5 |
| zlib     |     17.2 |                 17.2 |                 17.2 |                    25.8 |                 52.6 |              43.9 |             61.4 |            44.4 |                 60.3 |                        55.1 |                       71.1 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     41.1 |                 41.1 |                 41.1 |                    41.1 |                 98.5 |              91.1 |            101.3 |            69.1 |                111.4 |                       105.5 |                      134.8 |
| freertos |     39.3 |                 39.3 |                 39.3 |                    39.3 |                147.9 |              92.4 |            113.0 |            79.0 |                100.2 |                        87.6 |                      199.4 |
| littlefs |     36.0 |                 36.0 |                 36.0 |                    36.0 |                149.6 |              95.7 |            107.8 |            75.6 |                 94.9 |                        80.0 |                      198.5 |
| lua      |     48.2 |                 48.2 |                 48.2 |                    72.2 |                 80.1 |              65.6 |            105.2 |            72.5 |                 95.8 |                        86.1 |                      106.8 |
| mbedtls  |     64.2 |                 64.2 |                 64.2 |                    64.2 |                104.3 |             104.3 |            120.2 |            84.3 |                123.5 |                       119.8 |                      138.3 |
| sqlite   |     47.0 |                 47.0 |                 47.0 |                    47.0 |                108.8 |             109.9 |            114.5 |            80.4 |                123.9 |                       119.2 |                      271.5 |
| tinycc   |     60.3 |                 60.3 |                 60.3 |                    60.3 |                 78.6 |             101.4 |            108.9 |            78.9 |                102.4 |                        83.6 |                      107.0 |
| zlib     |     30.9 |                 30.9 |                 30.9 |                    46.2 |                 94.4 |              78.8 |            110.0 |            79.6 |                108.2 |                        98.7 |                      127.6 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |       22 |                   22 |                   22 |                      22 |                 3604 |              4182 |             7341 |            7341 |                 5571 |                        5567 |                        344 |
| freertos |       81 |                   85 |                   81 |                      85 |                 8282 |             10541 |            14903 |           14903 |                12444 |                       12474 |                       2051 |
| littlefs |       19 |                   19 |                   19 |                      19 |                 2774 |              3192 |             5195 |            5195 |                 4051 |                        4055 |                        246 |
| lua      |      336 |                  341 |                  336 |                     350 |                40494 |             46774 |            77971 |           77971 |                62526 |                       62639 |                       4408 |
| mbedtls  |     1154 |                 1164 |                 1154 |                    1190 |               255849 |            348278 |           466271 |          466271 |               390914 |                      391205 |                      71187 |
| sqlite   |       15 |                   15 |                   15 |                      15 |                22711 |             35259 |            39130 |           39130 |                29283 |                       29285 |                       2227 |
| tinycc   |       15 |                   15 |                   15 |                      15 |                 9665 |             10380 |            18835 |           18835 |                14825 |                       14685 |                       1057 |
| zlib     |      133 |                  133 |                  133 |                     141 |                10412 |             14127 |            21446 |           21446 |                17657 |                       17710 |                       1532 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `compiler_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     47.3 |                 51.0 |                 33.0 |                    27.8 |                 33.1 |             101.6 |             46.3 |            42.8 |                 35.8 |                        35.1 |                       26.1 |
| freertos |     39.6 |                 40.5 |                 37.9 |                    32.3 |                 47.1 |             108.4 |             56.9 |            53.3 |                 41.8 |                        45.5 |                       33.5 |
| littlefs |     28.4 |                 30.6 |                 29.0 |                    23.9 |                 34.7 |              57.8 |             53.8 |            48.9 |                 35.0 |                        50.3 |                       25.5 |
| lua      |     53.9 |                 46.9 |                 60.8 |                    50.6 |                 46.8 |             130.9 |             52.8 |            67.1 |                 87.6 |                        48.7 |                       30.4 |
| mbedtls  |     56.8 |                 54.0 |                 44.8 |                    37.1 |                 59.8 |             162.8 |             65.8 |            54.3 |                 52.0 |                        67.7 |                       48.6 |
| sqlite   |     28.3 |                 27.5 |                 33.2 |                    27.0 |                 33.7 |              84.4 |             58.9 |            62.8 |                 31.2 |                        34.0 |                       27.8 |
| tinycc   |     33.5 |                 37.3 |                 32.6 |                    27.0 |                 40.7 |             292.7 |             65.5 |            55.9 |                 32.5 |                        38.6 |                       24.7 |
| zlib     |     29.7 |                 29.1 |                 29.6 |                    25.0 |                 34.5 |              86.0 |             50.1 |            44.4 |                 36.6 |                        36.1 |                       23.5 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (19 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     72.6 |                 46.6 |                 47.2 |                    46.0 |                 47.8 |              52.0 |            108.2 |           107.0 |                 54.4 |                        45.4 |                       42.9 |
| freertos |     53.8 |                 55.6 |                 54.4 |                    52.6 |                 58.7 |              64.1 |            125.2 |           125.8 |                 60.5 |                        51.4 |                       50.2 |
| littlefs |     52.1 |                 47.8 |                 53.9 |                    43.6 |                 54.5 |              52.7 |            129.0 |           135.0 |                 50.9 |                        62.4 |                       46.6 |
| lua      |     58.1 |                 51.5 |                 64.8 |                    57.5 |                 50.9 |              77.5 |            126.0 |           130.8 |                 55.7 |                       106.0 |                       47.2 |
| mbedtls  |     69.6 |                 98.7 |                 54.5 |                    78.1 |                 87.2 |              89.6 |            113.8 |           130.2 |                 98.7 |                        87.2 |                       77.5 |
| sqlite   |     58.1 |                 46.6 |                 80.5 |                    67.2 |                 93.2 |             110.2 |            145.9 |           151.4 |                 61.1 |                        52.7 |                       98.7 |
| tinycc   |     53.9 |                 52.1 |                 71.4 |                    53.3 |                 90.2 |             102.9 |            147.1 |           142.3 |                 54.5 |                        54.5 |                       54.5 |
| zlib     |     41.8 |                 41.8 |                 43.6 |                    38.1 |                 43.6 |              60.5 |            102.3 |           105.4 |                 49.6 |                        41.2 |                       40.0 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (19 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |    102.2 |                 72.0 |                 69.5 |                    66.5 |                140.9 |            1107.8 |            136.1 |           111.3 |                113.1 |                       105.2 |                       72.6 |
| freertos |     81.0 |                 79.8 |                 81.0 |                    73.8 |                184.4 |            1079.4 |            162.7 |           110.1 |                119.7 |                       118.5 |                      101.6 |
| littlefs |     78.7 |                 72.1 |                 80.5 |                    58.1 |                202.3 |             732.7 |            143.5 |           113.8 |                114.4 |                       138.1 |                       76.3 |
| lua      |     87.8 |                 75.7 |                 96.9 |                    77.5 |                153.2 |            1221.4 |            151.4 |           115.7 |                113.8 |                       211.3 |                       78.1 |
| mbedtls  |     98.7 |                123.5 |                 81.7 |                    92.0 |                234.3 |            1557.2 |            164.7 |           138.0 |                184.1 |                       173.2 |                      124.1 |
| sqlite   |     95.7 |                 72.7 |                134.4 |                    94.4 |                259.1 |            3747.7 |            141.1 |           104.7 |                127.7 |                       110.2 |                      156.2 |
| tinycc   |     86.0 |                 77.5 |                 87.2 |                    75.1 |                287.0 |            9775.7 |            153.8 |           104.1 |                122.3 |                       118.1 |                      113.8 |
| zlib     |     60.5 |                 58.1 |                 67.2 |                    50.9 |                141.1 |             684.8 |            138.1 |           104.1 |                112.0 |                       100.5 |                       66.6 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (19 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     15.7 |                 13.9 |                 13.3 |                    15.1 |                 56.2 |             149.4 |             47.2 |            45.4 |                114.3 |                       114.3 |                        6.7 |
| freertos |     20.0 |                 21.8 |                 20.0 |                    21.2 |                 90.7 |             234.0 |             85.3 |            62.9 |                153.0 |                       153.6 |                       16.3 |
| littlefs |     21.2 |                 20.6 |                 21.8 |                    20.0 |                104.2 |             215.0 |             66.6 |            57.5 |                145.9 |                       188.3 |                       15.1 |
| lua      |     16.3 |                 14.5 |                 18.2 |                    18.2 |                 77.5 |             247.1 |             76.9 |            58.1 |                154.4 |                       313.7 |                       13.9 |
| mbedtls  |     17.6 |                 43.6 |                 21.2 |                    34.5 |                124.1 |             331.8 |            103.5 |            83.5 |                276.7 |                       289.4 |                       27.2 |
| sqlite   |     26.6 |                 20.6 |                 35.7 |                    31.5 |                107.2 |             311.2 |             65.4 |            54.5 |                159.2 |                       132.0 |                       30.9 |
| tinycc   |     23.0 |                 22.4 |                 24.8 |                    25.4 |                121.7 |             254.3 |             66.0 |            52.1 |                138.7 |                       139.3 |                       23.0 |
| zlib     |     15.1 |                 15.7 |                 15.7 |                    15.1 |                 60.5 |             254.3 |             59.3 |            48.4 |                134.4 |                       130.2 |                        9.1 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |   new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| cjson    |               102.7 |  42.8 |               58.3 |         3604 |           22 |            99.4 |             0.7 |             1.0 |           -40.0 |    -50.0 |     -37.7 | yes           |             47.8 |             72.6 |               -51.9 |                 27.5 |              72.1 |             0 |
| freertos |               217.4 |  57.8 |               73.4 |         8282 |           81 |            99.0 |             1.8 |             1.5 |            18.4 |     14.9 |      31.2 | yes           |             58.7 |             53.8 |                 8.3 |                 56.1 |              77.9 |             0 |
| littlefs |               106.9 |  25.8 |               75.9 |         2774 |           19 |            99.3 |             0.7 |             0.6 |            18.1 |     13.1 |      20.9 | yes           |             54.5 |             52.1 |                 4.4 |                 61.1 |              79.7 |             0 |
| lua      |               106.8 |  64.2 |               39.9 |        40494 |          336 |            99.2 |             8.8 |            10.2 |           -16.3 |    -18.2 |      -5.8 | yes           |             50.9 |             58.1 |               -14.1 |                 42.7 |              79.0 |             0 |
| mbedtls  |               234.4 | 144.3 |               38.5 |       255849 |         1154 |            99.5 |            58.8 |            55.8 |             3.4 |     -5.4 |       9.9 | no            |             87.2 |             69.6 |                20.2 |                 57.9 |              85.8 |             0 |
| sqlite   |               451.1 | 194.7 |               56.8 |        22711 |           15 |            99.9 |             9.1 |             7.6 |            12.1 |      2.1 |      22.3 | yes           |             93.2 |             58.1 |                37.7 |                 63.1 |              75.2 |             0 |
| tinycc   |               423.1 | 324.5 |               23.3 |         9665 |           15 |            99.8 |             3.6 |             3.0 |            10.7 |      1.9 |      20.4 | yes           |             90.2 |             53.9 |                40.2 |                 70.0 |              81.1 |             0 |
| zlib     |                52.6 |  17.2 |               67.3 |        10412 |          133 |            98.7 |             2.0 |             1.7 |            13.8 |    -14.4 |      21.1 | no            |             43.6 |             41.8 |                 4.1 |                 57.1 |              75.0 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        8 |                      4 |                      2 |                   23.3 |     57.6 |  75.9 |                    -40.0 |      11.4 |   18.4 |
| old arena table           |        8 |                      8 |                      0 |                   26.6 |     56.1 |  62.4 |                     50.3 |      64.5 |   87.1 |
| old scope maps            |        8 |                      6 |                      0 |                   44.6 |     59.2 |  72.0 |                     -2.1 |      36.3 |   54.7 |
| map per scope             |        8 |                      5 |                      0 |                   23.6 |     41.0 |  61.2 |                    -11.7 |      32.7 |   50.5 |
| std map + undo log        |        8 |                      4 |                      1 |                   41.1 |     61.4 |  71.5 |                    -33.1 |      10.7 |   36.1 |
| Swiss node map + undo log |        8 |                      4 |                      1 |                   27.8 |     55.1 |  68.8 |                    -30.4 |      12.1 |   42.7 |
| Swiss flat map, interned  |        8 |                      0 |                      6 |                   43.6 |     72.7 |  82.7 |                    -80.2 |     -24.7 |   -5.7 |

## B. Fixed-buffer mode

### Smallest fixed buffer that replays the whole trace without a refused operation

Found by bisection to 64 bytes. The baselines have no fixed-memory mode; the comparison is with their peak heap.

| trace    |   min buffer KiB (packed) |   min buffer KiB (raw) |   min buffer KiB (sparse index) |   packing saves % |   bytes per live decl |   vs METIS-X (previous) peak heap, red. % |   vs map per scope peak heap, red. % |   vs std map + undo log peak heap, red. % |   vs Swiss flat map, interned peak heap, red. % |
|:---------|--------------------------:|-----------------------:|--------------------------------:|------------------:|----------------------:|------------------------------------------:|-------------------------------------:|------------------------------------------:|------------------------------------------------:|
| cjson    |                      30.0 |                   31.8 |                            38.0 |               5.5 |                  28.8 |                                      70.8 |                                 58.3 |                                      74.2 |                                            78.6 |
| freertos |                      44.0 |                   47.8 |                            52.0 |               7.9 |                  29.9 |                                      79.8 |                                 62.1 |                                      70.1 |                                            85.0 |
| littlefs |                      20.0 |                   21.5 |                            24.0 |               7.0 |                  28.0 |                                      81.3 |                                 63.0 |                                      70.5 |                                            85.9 |
| lua      |                      35.9 |                   38.1 |                            43.9 |               5.7 |                  27.0 |                                      66.3 |                                 62.8 |                                      71.8 |                                            74.8 |
| mbedtls  |                      80.0 |                   87.9 |                            96.0 |               9.0 |                  35.6 |                                      65.9 |                                 57.8 |                                      71.2 |                                            74.3 |
| sqlite   |                     140.4 |                  152.9 |                           172.4 |               8.2 |                  33.9 |                                      68.9 |                                 57.9 |                                      72.7 |                                            87.5 |
| tinycc   |                     156.5 |                  168.3 |                           188.5 |               7.0 |                  29.1 |                                      63.0 |                                 63.1 |                                      71.6 |                                            72.8 |
| zlib     |                      15.8 |                   16.7 |                            19.8 |               5.6 |                  28.2 |                                      70.1 |                                 64.5 |                                      73.9 |                                            77.9 |

### Replay time (ms) with a buffer of 1x, 1.25x, 2x and 4x the minimum

Median of 9 replays. Blank: that size was refused (sizing is not perfectly monotonic).

| trace    |   1.00x |   1.25x |   2.00x |   4.00x |
|:---------|--------:|--------:|--------:|--------:|
| cjson    |     0.6 |     0.6 |     0.6 |     0.6 |
| freertos |     1.2 |     1.2 |     1.2 |     1.2 |
| littlefs |     0.5 |     0.6 |     0.6 |     0.5 |
| lua      |     7.5 |    12.4 |     8.3 |     7.7 |
| mbedtls  |    38.8 |    38.5 |    37.4 |    38.9 |
| sqlite   |     8.7 |     8.6 |    13.0 |     9.9 |
| tinycc   |     3.0 |     2.5 |     2.5 |     3.8 |
| zlib     |     1.6 |     1.6 |     1.6 |     1.6 |

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

99 table/trace pairs were checked against the reference model; 98 had no wrong or refused result.

| trace           | impl    |   wrong_lookups |   wrong_declares |   refused_declares |
|:----------------|:--------|----------------:|-----------------:|-------------------:|
| deep_shadow_400 | metis_x |             298 |                0 |                149 |

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    486.6 |                486.6 |                486.6 |                   486.6 |                868.2 |            6289.0 |           1023.8 |           708.1 |                972.4 |                       926.4 |                     1164.5 |
| deep_nesting    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                 57.1 |            2974.5 |             92.6 |            71.2 |                 61.0 |                        54.1 |                      264.2 |
| deep_shadow_400 |     11.5 |                 11.5 |                 11.5 |                    11.5 |                 40.1 |              34.8 |            103.1 |            90.6 |                 13.3 |                        13.2 |                       10.2 |
| dense_50k       |   2462.9 |               2462.9 |               2462.9 |                  2462.9 |               6972.3 |            2763.1 |           5351.5 |          3788.7 |               4812.7 |                      4047.7 |                     4671.1 |
| long_ids        |    216.4 |                216.4 |                216.4 |                   216.4 |                297.2 |           10427.1 |            307.4 |           249.5 |                269.8 |                       270.3 |                      381.2 |
| lookup_heavy    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                 53.7 |             551.3 |             64.3 |            45.0 |                 59.6 |                        53.9 |                      261.0 |
| scope_churn     |      3.9 |                  3.9 |                  3.9 |                     3.9 |                  6.4 |            2089.8 |              5.5 |             3.7 |                  4.6 |                         4.9 |                       64.4 |
| shadow_heavy    |      4.9 |                  5.2 |                  5.2 |                     5.5 |                 26.7 |            1807.3 |             29.0 |            21.3 |                  7.9 |                         7.6 |                        6.3 |
| short_ids       |     64.2 |                 64.2 |                 64.2 |                    64.2 |                200.8 |             599.4 |            189.0 |           127.9 |                151.4 |                       153.5 |                      260.2 |

### Peak heap bytes per live declaration (at the peak)

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     49.3 |                 49.3 |                 49.3 |                    49.3 |                 88.0 |             637.6 |            103.8 |            71.8 |                 98.6 |                        93.9 |                      118.1 |
| deep_nesting    |     38.4 |                 38.4 |                 38.4 |                    38.4 |                 85.3 |            4440.1 |            138.3 |           106.3 |                 91.1 |                        80.7 |                      394.4 |
| deep_shadow_400 |     29.5 |                 29.5 |                 29.5 |                    29.5 |                102.6 |              89.0 |            263.9 |           231.8 |                 34.0 |                        33.8 |                       26.2 |
| dense_50k       |     50.4 |                 50.4 |                 50.4 |                    50.4 |                142.8 |              56.6 |            109.6 |            77.6 |                 98.6 |                        82.9 |                       95.7 |
| long_ids        |    118.9 |                118.9 |                118.9 |                   118.9 |                163.3 |            5731.3 |            169.0 |           137.2 |                148.3 |                       148.6 |                      209.5 |
| lookup_heavy    |     42.9 |                 42.9 |                 42.9 |                    42.9 |                 89.3 |             917.9 |            107.0 |            75.0 |                 99.2 |                        89.8 |                      434.6 |
| scope_churn     |     72.3 |                 72.3 |                 72.3 |                    72.3 |                118.5 |           38908.1 |            101.7 |            69.1 |                 85.7 |                        91.3 |                     1198.3 |
| shadow_heavy    |     20.5 |                 21.6 |                 21.5 |                    22.9 |                110.8 |            7492.8 |            120.1 |            88.2 |                 32.8 |                        31.5 |                       26.0 |
| short_ids       |     33.6 |                 33.6 |                 33.6 |                    33.6 |                105.2 |             314.0 |             99.0 |            67.0 |                 79.3 |                        80.4 |                      136.3 |

### Allocator calls during the whole replay

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |       17 |                   17 |                   17 |                      17 |               104082 |            158610 |           263707 |          263707 |               263527 |                      263531 |                       3216 |
| deep_nesting    |       10 |                   10 |                   10 |                      10 |               103095 |             88211 |           127642 |          127741 |                97714 |                       85889 |                        304 |
| deep_shadow_400 |       10 |                   10 |                    8 |                      10 |                  268 |               449 |              811 |             811 |                  422 |                          23 |                         23 |
| dense_50k       |       21 |                   21 |                   21 |                      21 |                26613 |             38253 |            66587 |           66587 |                66603 |                       66606 |                      16623 |
| long_ids        |       14 |                   15 |                   14 |                      14 |               130673 |            268615 |           188471 |          194169 |               179824 |                       73138 |                       2042 |
| lookup_heavy    |       10 |                   10 |                   10 |                      10 |                16720 |             14381 |            21175 |           21256 |                16372 |                       14624 |                        293 |
| scope_churn     |        4 |                    4 |                    4 |                       4 |               119411 |            119442 |           179448 |          180056 |               150062 |                      134420 |                         29 |
| shadow_heavy    |       16 |                   16 |                    6 |                      19 |                73820 |             73856 |           138261 |          160027 |               134922 |                         187 |                         28 |
| short_ids       |       12 |                   12 |                   12 |                      12 |                43608 |             43648 |           100737 |          104041 |                89672 |                       32801 |                         42 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `synthetic_replay_time.csv`.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     66.7 |                 61.3 |                 74.1 |                    57.1 |                102.9 |            9229.2 |            171.3 |           126.8 |                137.9 |                       101.7 |                       46.8 |
| deep_nesting    |     49.2 |                 36.2 |                 37.0 |                    37.7 |                 67.0 |              86.4 |            451.8 |           474.7 |                 63.4 |                        50.0 |                       32.5 |
| deep_shadow_400 |      9.3 |                 15.5 |                  8.1 |                     9.5 |                228.1 |             285.7 |             24.5 |            23.1 |                  8.5 |                        10.9 |                        9.4 |
| dense_50k       |     84.3 |                103.5 |                 82.1 |                    75.8 |                 91.8 |           10323.3 |             96.6 |           101.0 |                255.6 |                       179.6 |                       69.7 |
| long_ids        |     80.0 |                 66.5 |                 82.8 |                    75.1 |                138.3 |             201.4 |            169.0 |           156.7 |                 76.3 |                        89.1 |                       44.1 |
| lookup_heavy    |     38.6 |                 36.0 |                 39.6 |                    39.7 |                 38.4 |              41.8 |            110.4 |            97.4 |                 40.0 |                        32.2 |                       37.4 |
| scope_churn     |     42.6 |                 55.0 |                 33.7 |                    34.3 |                 46.7 |              73.9 |             52.5 |            47.3 |                 66.5 |                        48.7 |                       27.8 |
| shadow_heavy    |     41.3 |                 46.9 |                 39.2 |                    45.5 |                 75.5 |             100.7 |             85.4 |           112.1 |                 46.2 |                        34.2 |                       37.3 |
| short_ids       |     36.7 |                 39.3 |                 34.0 |                    34.5 |                 54.2 |             131.5 |            113.2 |           104.4 |                 55.8 |                        42.0 |                       31.2 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (17 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      0.0 |                  0.0 |                  0.0 |                     0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| deep_nesting    |     58.1 |                 78.1 |                 49.7 |                    50.3 |                 99.9 |              69.0 |           2324.2 |          2169.8 |                 61.2 |                        90.2 |                       55.1 |
| deep_shadow_400 |     18.2 |                 24.8 |                 18.2 |                    18.2 |                523.6 |             746.0 |             24.2 |            21.8 |                 19.4 |                        24.2 |                       24.2 |
| dense_50k       |    205.4 |                227.2 |                200.0 |                   179.4 |                323.6 |             243.0 |            365.4 |           486.0 |                823.5 |                       730.8 |                      285.4 |
| long_ids        |    113.2 |                107.2 |                111.4 |                   116.3 |                170.2 |             208.3 |            436.0 |           362.1 |                188.3 |                        78.1 |                      103.5 |
| lookup_heavy    |     52.7 |                 51.5 |                 59.9 |                    53.3 |                127.2 |              72.7 |            204.1 |           208.3 |                 63.6 |                        51.5 |                       91.4 |
| scope_churn     |     52.7 |                 81.2 |                 73.9 |                    50.3 |                 64.2 |              77.5 |             93.3 |           146.0 |                 87.2 |                        52.7 |                       45.4 |
| shadow_heavy    |     39.4 |                 42.4 |                 39.4 |                    43.0 |                 99.9 |             139.3 |            247.7 |           341.5 |                 58.7 |                        40.0 |                       50.3 |
| short_ids       |     46.6 |                 49.7 |                 47.8 |                    46.0 |                 53.3 |              91.4 |            221.0 |           251.9 |                 92.0 |                        52.7 |                       98.7 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (17 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     87.9 |                 78.2 |                 86.0 |                   119.4 |                209.0 |           18065.8 |            224.8 |           163.0 |                150.3 |                       108.5 |                      118.1 |
| deep_nesting    |     78.7 |                 95.1 |                 64.8 |                    61.8 |                272.5 |             164.7 |            185.3 |           153.8 |                 98.1 |                       141.1 |                       67.8 |
| deep_shadow_400 |     20.0 |                 26.1 |                 20.0 |                    20.0 |                572.7 |             338.7 |            120.6 |           113.3 |                 40.0 |                        35.1 |                       37.0 |
| dense_50k       |    106.7 |                169.1 |                 93.3 |                    90.3 |                291.5 |           96786.9 |            224.8 |           357.5 |                446.6 |                       359.3 |                      141.2 |
| long_ids        |    127.2 |                119.9 |                123.5 |                   127.8 |                298.5 |             502.6 |            277.3 |           160.5 |                251.9 |                       140.5 |                      120.5 |
| lookup_heavy    |     76.9 |                 75.7 |                 88.4 |                    73.9 |                374.8 |             233.1 |            193.2 |           152.0 |                118.7 |                        97.5 |                      121.7 |
| scope_churn     |     65.4 |                 94.5 |                 90.3 |                    61.8 |                156.9 |             139.9 |             95.1 |           112.7 |                125.4 |                        81.8 |                       56.9 |
| shadow_heavy    |     46.6 |                 49.1 |                 47.2 |                    53.3 |                152.6 |             165.9 |            115.7 |           112.0 |                 93.3 |                        54.5 |                       64.8 |
| short_ids       |     60.0 |                 64.2 |                 61.8 |                    55.1 |                169.0 |             505.6 |            127.2 |           129.6 |                134.4 |                        91.4 |                      118.7 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (17 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |  13247.9 |              12525.1 |              12935.3 |                 61993.0 |             444949.1 |          927371.7 |         911549.5 |        683480.3 |             854462.2 |                    641161.1 |                    12143.4 |
| deep_nesting    |     31.5 |                 44.8 |                 35.1 |                    37.5 |                241.6 |             417.9 |            164.1 |           155.0 |                292.5 |                       304.0 |                       24.2 |
| deep_shadow_400 |      7.3 |                  7.3 |                  7.3 |                     7.3 |                250.3 |             370.9 |             23.6 |            20.6 |                  4.8 |                         4.8 |                        3.0 |
| dense_50k       |      0.0 |                  0.0 |                  0.0 |                     0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| long_ids        |    107.2 |                101.7 |                102.9 |                   107.2 |                604.9 |            3725.9 |            489.3 |           409.9 |                991.3 |                       609.2 |                       29.1 |
| lookup_heavy    |     41.2 |                 41.2 |                 45.4 |                    41.8 |                353.0 |             502.0 |            175.0 |           146.5 |                328.2 |                       274.3 |                       38.8 |
| scope_churn     |     25.4 |                 46.6 |                 44.8 |                    27.9 |                153.3 |             597.3 |             65.4 |           120.5 |                378.0 |                       236.2 |                        3.6 |
| shadow_heavy    |     24.8 |                 29.1 |                 23.6 |                    32.1 |                164.1 |             697.0 |            151.4 |           153.8 |                 45.4 |                        33.9 |                       26.0 |
| short_ids       |     92.0 |                 90.8 |                 90.8 |                    92.0 |                324.0 |             837.5 |            208.9 |           196.2 |                400.3 |                       342.1 |                       46.0 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace           |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:----------------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| big_scope_exit  |               868.2 |  486.6 |               44.0 |       104082 |           17 |           100.0 |            20.6 |            13.4 |            32.4 |     29.4 |      43.7 | yes           |              0.0 |              0.0 |               nan   |                 57.9 |              97.0 |             0 |
| deep_nesting    |                57.1 |   25.8 |               54.9 |       103095 |           10 |           100.0 |            20.1 |            14.8 |            25.8 |     14.6 |      36.1 | yes           |             99.9 |             58.1 |                41.8 |                 71.1 |              87.0 |             0 |
| deep_shadow_400 |                40.1 |   11.5 |               71.3 |          268 |           10 |            96.3 |             0.5 |             0.0 |            96.0 |     95.8 |      96.2 | yes           |            523.6 |             18.2 |                96.5 |                 96.5 |              97.1 |           149 |
| dense_50k       |              6972.3 | 2462.9 |               64.7 |        26613 |           21 |            99.9 |            22.9 |            21.1 |            -4.7 |    -25.2 |      12.0 | no            |            323.6 |            205.4 |                36.5 |                 63.4 |             nan   |             0 |
| long_ids        |               297.2 |  216.4 |               27.2 |       130673 |           14 |           100.0 |            41.5 |            24.0 |            42.0 |     38.1 |      46.2 | yes           |            170.2 |            113.2 |                33.5 |                 57.4 |              82.3 |             0 |
| lookup_heavy    |                53.7 |   25.8 |               52.0 |        16720 |           10 |            99.9 |            11.5 |            11.6 |            -0.8 |     -4.6 |      10.2 | no            |            127.2 |             52.7 |                58.6 |                 79.5 |              88.3 |             0 |
| scope_churn     |                 6.4 |    3.9 |               39.0 |       119411 |            4 |           100.0 |            15.4 |            14.1 |            15.1 |      8.4 |      26.5 | yes           |             64.2 |             52.7 |                17.9 |                 58.3 |              83.4 |             0 |
| shadow_heavy    |                26.7 |    4.9 |               81.5 |        73820 |           16 |           100.0 |            22.7 |            12.4 |            45.1 |     43.2 |      54.3 | yes           |             99.9 |             39.4 |                60.6 |                 69.5 |              84.9 |             0 |
| short_ids       |               200.8 |   64.2 |               68.0 |        43608 |           12 |           100.0 |            16.3 |            11.0 |            34.5 |     30.7 |      39.1 | yes           |             53.3 |             46.6 |                12.6 |                 64.5 |              71.6 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        9 |                      7 |                      0 |                   27.2 |     54.9 |  81.5 |                     -4.7 |      32.4 |   96.0 |
| old arena table           |        9 |                      9 |                      0 |                   10.9 |     95.3 |  99.8 |                     10.3 |      60.3 |   99.3 |
| old scope maps            |        9 |                      8 |                      0 |                   28.9 |     59.9 |  88.8 |                     10.3 |      61.6 |   89.1 |
| map per scope             |        9 |                      8 |                      0 |                   -4.6 |     42.8 |  87.3 |                     -1.9 |      60.5 |   89.1 |
| std map + undo log        |        9 |                      6 |                      1 |                   13.3 |     48.8 |  57.8 |                     -6.4 |      22.0 |   59.8 |
| Swiss node map + undo log |        9 |                      6 |                      2 |                   12.8 |     39.2 |  58.2 |                    -19.1 |      14.2 |   48.4 |
| Swiss flat map, interned  |        9 |                      1 |                      6 |                  -12.5 |     58.2 |  94.0 |                    -74.8 |     -27.0 |    1.1 |

## D. Worst-case clustering

### STRATA lookup cost when every key is forced into one probe cluster

Best of 7 rounds, batch-timed. With all keys in one cluster a lookup scans the cluster: cost grows linearly.

|   live_names | hash                 |   ns_per_lookup_hit |   ns_per_lookup_miss |   ns_per_declare |
|-------------:|:---------------------|--------------------:|---------------------:|-----------------:|
|           16 | normal               |                 9.1 |                  7.8 |            131.9 |
|           16 | all_keys_one_cluster |                11.4 |                 16.2 |            139.6 |
|           64 | normal               |                10.0 |                  8.7 |            150.6 |
|           64 | all_keys_one_cluster |                29.7 |                 55.4 |            251.5 |
|          256 | normal               |                10.5 |                  8.8 |            105.5 |
|          256 | all_keys_one_cluster |               115.6 |                215.6 |            477.8 |
|         1024 | normal               |                11.0 |                 10.2 |            129.3 |
|         1024 | all_keys_one_cluster |               432.2 |                840.4 |           2254.7 |
|         4096 | normal               |                14.7 |                 19.5 |             94.0 |
|         4096 | all_keys_one_cluster |              1696.8 |               3197.8 |           6368.0 |

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

42 table/trace pairs were checked against the reference model; 42 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |    292.0 |                292.0 |                292.0 |                   292.0 |                876.9 |             776.7 |            753.9 |           525.7 |                652.8 |                       551.8 |                     1182.0 |
| ESP-IDF  |   7480.9 |               7480.9 |               7480.9 |                  7480.9 |              15375.5 |             nan   |          19841.8 |         13985.2 |              18289.1 |                     18105.5 |                    41419.9 |
| FreeRTOS |    292.0 |                292.0 |                292.0 |                   292.0 |                937.9 |            1158.9 |            758.3 |           534.9 |                651.2 |                       550.3 |                     1230.7 |
| Zephyr   |   1870.3 |               1870.3 |               2216.7 |                  1870.3 |               7572.0 |             nan   |           5792.1 |          4154.9 |               5211.4 |                      4474.0 |                    19054.7 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.1 |                 43.1 |                 43.1 |                    43.1 |                129.5 |             114.7 |            111.3 |            77.6 |                 96.4 |                        81.5 |                      174.5 |
| ESP-IDF  |     49.9 |                 49.9 |                 49.9 |                    49.9 |                102.6 |             nan   |            132.3 |            93.3 |                122.0 |                       120.8 |                      276.3 |
| FreeRTOS |     46.6 |                 46.6 |                 46.6 |                    46.6 |                149.8 |             185.0 |            121.1 |            85.4 |                104.0 |                        87.9 |                      196.5 |
| Zephyr   |     41.7 |                 41.7 |                 49.4 |                    41.7 |                168.8 |             nan   |            129.1 |            92.6 |                116.2 |                        99.7 |                      424.8 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     16.0 |                 16.0 |                 16.0 |                    16.0 |              19804.0 |           26299.0 |          35323.0 |         43882.0 |              39468.0 |                     29565.0 |                     3385.0 |
| ESP-IDF  |     24.0 |                 24.0 |                 24.0 |                    24.0 |             629511.0 |             nan   |        1032063.0 |       1342739.0 |            1225740.0 |                    860749.0 |                   168333.0 |
| FreeRTOS |     16.0 |                 16.0 |                 16.0 |                    16.0 |              32473.0 |           50714.0 |          53727.0 |        115265.0 |             108616.0 |                     41135.0 |                     4786.0 |
| Zephyr   |     25.0 |                 25.0 |                 21.0 |                    25.0 |             664319.0 |             nan   |        1056367.0 |       1116929.0 |             974653.0 |                    870284.0 |                   147498.0 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `legacy_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     45.9 |                 52.3 |                 45.8 |                    40.0 |                 52.5 |             707.6 |             68.0 |            60.7 |                 68.7 |                        51.4 |                       38.3 |
| ESP-IDF  |     61.2 |                 54.1 |                 59.3 |                    55.4 |                 82.8 |             nan   |            149.3 |           151.2 |                150.1 |                       107.9 |                       81.6 |
| FreeRTOS |     39.9 |                 70.1 |                 51.3 |                    32.6 |                 45.0 |             584.0 |             63.2 |            75.1 |                 49.2 |                        43.4 |                       38.0 |
| Zephyr   |     40.9 |                 44.2 |                 36.4 |                    41.3 |                 70.4 |             nan   |            133.2 |           116.8 |                 79.7 |                        62.9 |                       61.5 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     50.9 |                 49.1 |                 50.3 |                    47.9 |                 56.3 |              73.9 |            116.9 |           121.8 |                 52.7 |                        51.5 |                       49.7 |
| ESP-IDF  |     63.6 |                 66.6 |                 62.4 |                    64.8 |                 86.0 |             nan   |            154.4 |           190.8 |                 95.7 |                        79.9 |                       77.5 |
| FreeRTOS |    104.8 |                 94.5 |                 76.3 |                    52.1 |                 74.5 |              86.0 |            128.4 |           133.8 |                 63.6 |                        55.7 |                       55.7 |
| Zephyr   |     64.2 |                 76.9 |                 77.5 |                    69.7 |                 81.2 |             nan   |            253.8 |           307.7 |                 98.7 |                        83.6 |                       82.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     83.0 |                 86.0 |                 81.2 |                    76.3 |                232.0 |            8005.9 |            173.8 |           132.0 |                155.7 |                       138.1 |                      101.8 |
| ESP-IDF  |    151.4 |                159.9 |                155.0 |                   150.2 |                359.7 |             nan   |            663.1 |           664.9 |                677.7 |                       315.5 |                      341.6 |
| FreeRTOS |    155.6 |                142.3 |                108.4 |                    75.7 |                170.2 |            5392.6 |            170.8 |           163.5 |                149.6 |                       135.6 |                      117.5 |
| Zephyr   |    136.9 |                156.3 |                147.8 |                   135.7 |                318.6 |             nan   |            393.7 |           361.0 |                591.2 |                       269.5 |                      317.4 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     42.4 |                 41.8 |                 41.2 |                    41.8 |                252.6 |             765.0 |            200.5 |           169.0 |                492.5 |                       450.7 |                       24.8 |
| ESP-IDF  |     44.8 |                 48.4 |                 44.8 |                    47.2 |                294.3 |             nan   |            230.7 |           231.9 |                538.4 |                       463.9 |                       27.9 |
| FreeRTOS |     66.0 |                 49.7 |                 43.0 |                    34.5 |                155.6 |             509.3 |            160.5 |           145.9 |                304.0 |                       301.0 |                       22.4 |
| Zephyr   |     50.9 |                 56.9 |                 52.7 |                    53.9 |                265.9 |             nan   |            249.6 |           249.0 |                587.5 |                       479.1 |                       30.9 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| Arduino  |               876.9 |  292.0 |               66.7 |        19804 |           16 |            99.9 |             4.9 |             4.3 |            18.1 |     12.7 |      29.9 | yes           |             56.3 |             50.9 |                 9.6 |                 64.2 |              83.2 |             0 |
| ESP-IDF  |             15375.5 | 7480.9 |               51.3 |       629511 |           24 |           100.0 |           184.6 |           136.5 |            25.5 |     14.4 |      34.7 | yes           |             86.0 |             63.6 |                26.0 |                 57.9 |              84.8 |             0 |
| FreeRTOS |               937.9 |  292.0 |               68.9 |        32473 |           16 |           100.0 |            10.2 |             9.1 |             6.7 |    -13.0 |      18.2 | no            |             74.5 |            104.8 |               -40.7 |                  8.6 |              57.6 |             0 |
| Zephyr   |              7572.0 | 1870.3 |               75.3 |       664319 |           25 |           100.0 |           183.4 |           106.5 |            40.5 |     35.4 |      52.4 | yes           |             81.2 |             64.2 |                20.9 |                 57.0 |              80.9 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        4 |                      3 |                      0 |                   51.3 |     67.8 |  75.3 |                      6.7 |      21.8 |   40.5 |
| old arena table           |        2 |                      2 |                      0 |                   62.4 |     68.6 |  74.8 |                     92.8 |      93.2 |   93.6 |
| old scope maps            |        4 |                      4 |                      0 |                   61.3 |     61.9 |  67.7 |                     31.1 |      45.9 |   67.7 |
| map per scope             |        4 |                      4 |                      0 |                   44.4 |     46.0 |  55.0 |                     27.0 |      48.3 |   65.3 |
| std map + undo log        |        4 |                      3 |                      0 |                   55.2 |     57.2 |  64.1 |                     13.2 |      42.4 |   61.2 |
| Swiss node map + undo log |        4 |                      3 |                      0 |                   46.9 |     52.6 |  58.7 |                     -3.5 |      24.2 |   41.8 |
| Swiss flat map, interned  |        4 |                      2 |                      2 |                   75.3 |     79.1 |  90.2 |                    -17.7 |       7.4 |   30.5 |

