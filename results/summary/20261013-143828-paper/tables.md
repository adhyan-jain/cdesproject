# Result tables for run `20261013-143828-paper`

```
run: results/raw/20261013-143828-paper
date_utc: 2026-10-13T14:39:09Z
git_commit: 36f9f6c0d0d4723beca2d9850cec0b9e195378eb
compiler: g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
flags: -std=c++14 -O2
kernel: Linux 6.18.33.2-microsoft-standard-WSL2
cpu: Intel(R) Core(TM) Ultra 7 258V
libc: ldd (Ubuntu GLIBC 2.35-0ubuntu3.15) 2.35
pinning: taskset -c 2
rounds: 31 (+2 warm-up); in each round every table replays the trace once, order rotated; 3 per-operation latency replays
metis: 7b3dacfa5405ec3e6a03b718f485b473d779123d
phmap: v1.4.1
extra experiments: git 36f9f6c, 2026-10-13T14:47:33Z, all
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

104 table/trace pairs were checked against the reference model; 104 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     42.9 |                 42.9 |                 42.9 |                    42.9 |                  42.9 |                              42.8 |                102.7 |              95.0 |            105.6 |            72.0 |                116.0 |                       110.0 |                      140.4 |
| freertos |     57.8 |                 57.8 |                 57.8 |                    57.8 |                  57.8 |                              57.7 |                217.3 |             135.8 |            166.2 |           116.1 |                147.3 |                       128.8 |                      293.1 |
| littlefs |     25.8 |                 25.8 |                 25.8 |                    25.8 |                  25.8 |                              25.7 |                106.9 |              68.4 |             77.1 |            54.1 |                 67.8 |                        57.0 |                      141.9 |
| lua      |     64.2 |                 64.2 |                 64.2 |                    96.3 |                  64.2 |                              96.2 |                106.8 |              87.5 |            140.2 |            96.7 |                127.7 |                       114.7 |                      142.3 |
| mbedtls  |    144.3 |                144.3 |                144.3 |                   144.3 |                 144.3 |                             144.2 |                234.4 |             234.4 |            270.0 |           189.4 |                277.7 |                       269.3 |                      310.9 |
| sqlite   |    194.8 |                194.8 |                194.8 |                   194.8 |                 194.8 |                             194.7 |                451.0 |             455.4 |            474.8 |           333.3 |                513.5 |                       493.9 |                     1125.6 |
| tinycc   |    324.5 |                324.5 |                324.5 |                   324.5 |                 324.5 |                             324.4 |                423.0 |             545.3 |            585.6 |           424.5 |                550.8 |                       449.4 |                      575.6 |
| zlib     |     17.2 |                 17.2 |                 17.2 |                    25.8 |                  17.2 |                              25.7 |                 52.6 |              43.9 |             61.4 |            44.4 |                 60.3 |                        55.0 |                       71.1 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     41.1 |                 41.1 |                 41.1 |                    41.1 |                  41.1 |                              41.0 |                 98.5 |              91.1 |            101.3 |            69.1 |                111.4 |                       105.6 |                      134.8 |
| freertos |     39.3 |                 39.3 |                 39.3 |                    39.3 |                  39.3 |                              39.3 |                147.9 |              92.4 |            113.1 |            79.0 |                100.2 |                        87.6 |                      199.4 |
| littlefs |     36.1 |                 36.1 |                 36.1 |                    36.1 |                  36.1 |                              35.9 |                149.6 |              95.7 |            107.8 |            75.6 |                 94.8 |                        79.8 |                      198.5 |
| lua      |     48.2 |                 48.2 |                 48.2 |                    72.2 |                  48.2 |                              72.1 |                 80.1 |              65.6 |            105.2 |            72.5 |                 95.8 |                        86.0 |                      106.8 |
| mbedtls  |     64.2 |                 64.2 |                 64.2 |                    64.2 |                  64.2 |                              64.1 |                104.3 |             104.3 |            120.1 |            84.2 |                123.5 |                       119.8 |                      138.3 |
| sqlite   |     47.0 |                 47.0 |                 47.0 |                    47.0 |                  47.0 |                              47.0 |                108.8 |             109.9 |            114.5 |            80.4 |                123.9 |                       119.1 |                      271.5 |
| tinycc   |     60.3 |                 60.3 |                 60.3 |                    60.3 |                  60.3 |                              60.3 |                 78.6 |             101.4 |            108.9 |            78.9 |                102.4 |                        83.5 |                      107.0 |
| zlib     |     30.9 |                 30.9 |                 30.9 |                    46.2 |                  30.9 |                              46.1 |                 94.4 |              78.8 |            110.1 |            79.6 |                108.1 |                        98.6 |                      127.6 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |       22 |                   22 |                   22 |                      22 |                    22 |                                22 |                 3604 |              4182 |             7341 |            7341 |                 5571 |                        5567 |                        344 |
| freertos |       81 |                   85 |                   81 |                      85 |                    81 |                                86 |                 8282 |             10541 |            14903 |           14903 |                12444 |                       12474 |                       2051 |
| littlefs |       19 |                   19 |                   19 |                      19 |                    19 |                                19 |                 2774 |              3192 |             5195 |            5195 |                 4051 |                        4055 |                        246 |
| lua      |      336 |                  341 |                  336 |                     350 |                   336 |                               349 |                40494 |             46774 |            77971 |           77971 |                62526 |                       62639 |                       4408 |
| mbedtls  |     1154 |                 1164 |                 1154 |                    1190 |                  1154 |                              1203 |               255849 |            348278 |           466271 |          466271 |               390914 |                      391205 |                      71187 |
| sqlite   |       15 |                   15 |                   15 |                      15 |                    15 |                                15 |                22711 |             35259 |            39130 |           39130 |                29283 |                       29285 |                       2227 |
| tinycc   |       15 |                   15 |                   15 |                      15 |                    15 |                                15 |                 9665 |             10380 |            18835 |           18835 |                14825 |                       14685 |                       1057 |
| zlib     |      133 |                  133 |                  133 |                     141 |                   133 |                               141 |                10412 |             14127 |            21446 |           21446 |                17657 |                       17710 |                       1532 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `compiler_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     27.6 |                 27.8 |                 26.5 |                    24.0 |                  32.9 |                              27.7 |                 35.7 |             105.4 |             45.3 |            42.5 |                 36.0 |                        36.2 |                       27.4 |
| freertos |     32.2 |                 32.8 |                 31.3 |                    28.8 |                  38.0 |                              31.9 |                 48.6 |             107.5 |             57.5 |            50.0 |                 44.1 |                        44.4 |                       34.8 |
| littlefs |     29.5 |                 31.4 |                 28.7 |                    25.3 |                  35.5 |                              27.1 |                 37.4 |              61.7 |             53.5 |            51.6 |                 32.6 |                        33.2 |                       26.1 |
| lua      |     31.4 |                 34.3 |                 32.0 |                    28.3 |                  39.9 |                              33.3 |                 47.4 |             124.3 |             54.6 |            50.4 |                 46.8 |                        46.8 |                       31.1 |
| mbedtls  |     36.8 |                 37.1 |                 38.8 |                    34.2 |                  47.0 |                              37.0 |                 58.7 |             159.2 |             65.8 |            54.4 |                 54.9 |                        56.0 |                       40.2 |
| sqlite   |     26.9 |                 27.2 |                 28.3 |                    26.2 |                  32.5 |                              26.3 |                 31.9 |              85.4 |             62.7 |            62.9 |                 29.9 |                        29.4 |                       26.9 |
| tinycc   |     28.1 |                 32.3 |                 28.6 |                    25.4 |                  34.7 |                              26.3 |                 36.4 |             259.4 |             62.1 |            58.4 |                 32.2 |                        31.6 |                       24.5 |
| zlib     |     27.0 |                 28.0 |                 25.5 |                    23.9 |                  35.1 |                              29.1 |                 37.9 |              89.6 |             51.1 |            47.3 |                 40.9 |                        39.0 |                       27.2 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     49.2 |                 48.0 |                 52.2 |                    45.1 |                  56.3 |                              40.9 |                 48.6 |              52.2 |            108.5 |           110.3 |                 53.4 |                        44.5 |                       42.7 |
| freertos |     51.6 |                 51.0 |                 51.6 |                    48.0 |                  62.3 |                              43.9 |                 54.0 |              56.3 |            116.2 |           118.0 |                 56.3 |                        49.2 |                       45.1 |
| littlefs |     51.0 |                 48.6 |                 51.0 |                    46.8 |                  59.9 |                              40.9 |                 48.6 |              52.2 |            125.1 |           125.7 |                 50.4 |                        44.5 |                       45.1 |
| lua      |     53.3 |                 52.7 |                 53.9 |                    47.2 |                  69.0 |                              89.0 |                 54.5 |              56.3 |            146.6 |           168.4 |                 65.4 |                        50.3 |                       55.1 |
| mbedtls  |     65.6 |                 57.2 |                 60.2 |                    56.0 |                  71.7 |                              53.6 |                 69.3 |              74.1 |            104.8 |           104.2 |                 68.1 |                        74.7 |                       53.0 |
| sqlite   |     52.1 |                 55.1 |                 60.0 |                    50.3 |                  80.5 |                              52.7 |                 65.4 |              70.9 |            152.6 |           173.8 |                 56.3 |                        52.1 |                       56.3 |
| tinycc   |     51.4 |                 55.5 |                 50.8 |                    43.1 |                  57.9 |                              43.7 |                 51.4 |              53.7 |            139.4 |           136.4 |                 52.6 |                        44.3 |                       48.4 |
| zlib     |     43.7 |                 47.2 |                 44.3 |                    40.2 |                  52.0 |                              41.3 |                 43.7 |              58.5 |            112.8 |           105.1 |                 63.8 |                        44.9 |                       41.3 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     62.3 |                 61.7 |                 64.6 |                    59.9 |                  70.6 |                              71.1 |                141.1 |            1103.9 |            141.7 |           106.7 |                109.1 |                       107.3 |                       71.7 |
| freertos |     68.2 |                 63.4 |                 68.2 |                    64.0 |                  78.9 |                              72.9 |                180.2 |            1048.2 |            159.5 |           107.9 |                119.2 |                       115.6 |                       89.5 |
| littlefs |     64.6 |                 65.8 |                 67.6 |                    65.2 |                  75.3 |                              72.3 |                187.3 |             703.7 |            143.5 |           102.6 |                118.6 |                       104.3 |                       75.9 |
| lua      |     66.0 |                 64.2 |                 66.6 |                    61.2 |                  86.6 |                             130.2 |                164.1 |             984.7 |            189.0 |           172.0 |                129.0 |                       110.2 |                       90.2 |
| mbedtls  |     78.9 |                 69.3 |                 74.1 |                    68.7 |                  86.1 |                              77.7 |                202.4 |            1395.5 |            160.8 |           118.0 |                135.5 |                       148.2 |                      111.4 |
| sqlite   |     70.9 |                 70.3 |                 78.1 |                    69.6 |                 109.0 |                              86.0 |                204.1 |            3532.6 |            143.5 |           130.8 |                134.4 |                       117.5 |                      116.9 |
| tinycc   |     66.1 |                 69.1 |                 68.5 |                    60.8 |                  75.6 |                              75.0 |                187.8 |            6233.0 |            145.3 |           104.5 |                122.3 |                        95.7 |                       80.9 |
| zlib     |     56.1 |                 58.5 |                 59.6 |                    53.7 |                  67.9 |                              67.9 |                136.4 |             648.5 |            154.1 |           106.3 |                138.2 |                       107.5 |                       67.9 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     13.0 |                 14.2 |                 14.8 |                    13.6 |                  13.6 |                              19.0 |                 55.7 |             157.7 |             49.2 |            44.5 |                110.3 |                       118.6 |                        7.7 |
| freertos |     15.4 |                 16.6 |                 14.8 |                    16.0 |                  16.6 |                              23.1 |                 86.6 |             227.7 |             78.9 |            57.5 |                151.2 |                       152.4 |                       14.8 |
| littlefs |     19.0 |                 19.0 |                 18.4 |                    20.8 |                  19.0 |                              25.5 |                 90.1 |             218.2 |             65.8 |            55.7 |                144.1 |                       141.1 |                       16.6 |
| lua      |     21.2 |                 21.8 |                 21.2 |                    21.2 |                  28.5 |                              56.3 |                 84.2 |             202.3 |             98.1 |            92.7 |                169.0 |                       159.9 |                       19.4 |
| mbedtls  |     27.1 |                 24.1 |                 24.1 |                    24.7 |                  24.7 |                              35.5 |                109.0 |             302.3 |             99.4 |            71.1 |                215.6 |                       231.3 |                       21.1 |
| sqlite   |     21.8 |                 23.0 |                 23.6 |                    22.4 |                  30.9 |                              27.9 |                 75.7 |             245.3 |             66.6 |            59.4 |                146.6 |                       129.6 |                       18.8 |
| tinycc   |     19.5 |                 21.3 |                 18.9 |                    19.5 |                  18.9 |                              23.6 |                 75.6 |             181.3 |             60.2 |            49.6 |                131.7 |                       112.8 |                       15.4 |
| zlib     |     15.9 |                 17.7 |                 15.9 |                    15.9 |                  16.5 |                              23.0 |                 59.1 |             254.5 |             67.9 |            51.4 |                164.8 |                       134.1 |                       11.8 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |   new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| cjson    |               102.7 |  42.9 |               58.2 |         3604 |           22 |            99.4 |             0.7 |             0.6 |            22.8 |     19.0 |      27.5 | yes           |             48.6 |             49.2 |                -1.2 |                 55.8 |              76.7 |             0 |
| freertos |               217.3 |  57.8 |               73.4 |         8282 |           81 |            99.0 |             1.8 |             1.2 |            33.9 |     31.3 |      39.0 | yes           |             54.0 |             51.6 |                 4.4 |                 62.2 |              82.2 |             0 |
| littlefs |               106.9 |  25.8 |               75.9 |         2774 |           19 |            99.3 |             0.8 |             0.6 |            24.5 |     18.1 |      27.2 | yes           |             48.6 |             51.0 |                -4.9 |                 65.5 |              78.9 |             0 |
| lua      |               106.8 |  64.2 |               39.9 |        40494 |          336 |            99.2 |             8.9 |             5.9 |            30.9 |     29.2 |      35.3 | yes           |             54.5 |             53.3 |                 2.2 |                 59.8 |              74.8 |             0 |
| mbedtls  |               234.4 | 144.3 |               38.4 |       255849 |         1154 |            99.5 |            57.7 |            36.1 |            36.7 |     32.4 |      39.6 | yes           |             69.3 |             65.6 |                 5.3 |                 61.0 |              75.1 |             0 |
| sqlite   |               451.0 | 194.8 |               56.8 |        22711 |           15 |            99.9 |             8.6 |             7.2 |            15.9 |      6.3 |      20.7 | yes           |             65.4 |             52.1 |                20.3 |                 65.3 |              71.2 |             0 |
| tinycc   |               423.0 | 324.5 |               23.3 |         9665 |           15 |            99.8 |             3.2 |             2.5 |            20.4 |     18.7 |      28.2 | yes           |             51.4 |             51.4 |                 0.0 |                 64.8 |              74.2 |             0 |
| zlib     |                52.6 |  17.2 |               67.3 |        10412 |          133 |            98.7 |             2.2 |             1.6 |            29.9 |     27.4 |      32.8 | yes           |             43.7 |             43.7 |                 0.0 |                 58.9 |              73.1 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                        |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| arena + chains (allocator-free) |        8 |                      0 |                      2 |                   -0.4 |     -0.1 |  33.2 |                    -10.7 |      -0.2 |   10.6 |
| METIS-X (previous)              |        8 |                      8 |                      0 |                   23.3 |     57.5 |  75.9 |                     15.9 |      27.2 |   36.7 |
| old arena table                 |        8 |                      8 |                      0 |                   26.6 |     56.1 |  62.3 |                     53.3 |      71.8 |   89.1 |
| old scope maps                  |        8 |                      8 |                      0 |                   44.6 |     59.2 |  71.9 |                     39.7 |      45.5 |   56.5 |
| map per scope                   |        8 |                      8 |                      0 |                   23.6 |     41.0 |  61.2 |                     32.2 |      40.0 |   55.6 |
| std map + undo log              |        8 |                      8 |                      0 |                   41.1 |     61.4 |  71.4 |                      7.4 |      24.7 |   34.2 |
| Swiss node map + undo log       |        8 |                      8 |                      0 |                   27.8 |     54.9 |  68.7 |                      7.2 |      25.5 |   33.0 |
| Swiss flat map, interned        |        8 |                      1 |                      2 |                   43.6 |     72.6 |  82.7 |                    -14.5 |      -1.7 |    8.4 |

## B. Fixed-buffer mode

### Smallest fixed buffer that replays the whole trace without a refused operation

Found by bisection to 64 bytes. The baselines have no fixed-memory mode; the comparison is with their peak heap.

| trace    |   min buffer KiB (packed) |   min buffer KiB (raw) |   min buffer KiB (sparse index) |   packing saves % |   bytes per live decl |   arena + chains min buffer KiB |   vs arena + chains, red. % |   vs METIS-X (previous) peak heap, red. % |   vs map per scope peak heap, red. % |   vs std map + undo log peak heap, red. % |   vs Swiss flat map, interned peak heap, red. % |
|:---------|--------------------------:|-----------------------:|--------------------------------:|------------------:|----------------------:|--------------------------------:|----------------------------:|------------------------------------------:|-------------------------------------:|------------------------------------------:|------------------------------------------------:|
| cjson    |                      30.0 |                   31.8 |                            38.0 |               5.5 |                  28.8 |                            35.9 |                        16.4 |                                      70.8 |                                 58.3 |                                      74.1 |                                            78.6 |
| freertos |                      44.0 |                   47.8 |                            52.0 |               7.9 |                  29.9 |                            53.6 |                        17.9 |                                      79.8 |                                 62.1 |                                      70.1 |                                            85.0 |
| littlefs |                      20.0 |                   21.5 |                            24.0 |               7.0 |                  28.0 |                            24.2 |                        17.5 |                                      81.3 |                                 63.0 |                                      70.5 |                                            85.9 |
| lua      |                      35.9 |                   38.1 |                            43.9 |               5.7 |                  27.0 |                            43.4 |                        17.3 |                                      66.3 |                                 62.8 |                                      71.8 |                                            74.8 |
| mbedtls  |                      80.0 |                   87.9 |                            96.0 |               9.0 |                  35.6 |                            96.9 |                        17.4 |                                      65.9 |                                 57.8 |                                      71.2 |                                            74.3 |
| sqlite   |                     140.4 |                  152.9 |                           172.4 |               8.2 |                  33.9 |                           169.4 |                        17.2 |                                      68.9 |                                 57.9 |                                      72.7 |                                            87.5 |
| tinycc   |                     156.5 |                  168.3 |                           188.5 |               7.0 |                  29.1 |                           189.8 |                        17.5 |                                      63.0 |                                 63.1 |                                      71.6 |                                            72.8 |
| zlib     |                      15.8 |                   16.7 |                            19.8 |               5.6 |                  28.2 |                            18.9 |                        16.6 |                                      70.1 |                                 64.5 |                                      73.9 |                                            77.9 |

### Replay time (ms) with a buffer of 1x, 1.25x, 2x and 4x the minimum

Median of 9 replays. Blank: that size was refused (sizing is not perfectly monotonic).

| trace    |   1.00x |   1.25x |   2.00x |   4.00x |
|:---------|--------:|--------:|--------:|--------:|
| cjson    |     0.5 |     0.5 |     0.5 |     0.5 |
| freertos |     1.1 |     1.1 |     1.1 |     1.2 |
| littlefs |     0.5 |     0.5 |     0.5 |     0.6 |
| lua      |     5.9 |     5.8 |     5.8 |     6.0 |
| mbedtls  |    34.3 |    34.5 |    35.1 |    34.2 |
| sqlite   |     8.4 |     6.7 |     6.7 |     7.0 |
| tinycc   |     3.1 |     2.6 |     2.7 |     4.5 |
| zlib     |     1.2 |     1.3 |     1.3 |     1.3 |

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

117 table/trace pairs were checked against the reference model; 116 had no wrong or refused result.

| trace           | impl    |   wrong_lookups |   wrong_declares |   refused_declares |
|:----------------|:--------|----------------:|-----------------:|-------------------:|
| deep_shadow_400 | metis_x |             298 |                0 |                149 |

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    486.6 |                486.6 |                486.6 |                   486.6 |                 486.6 |                             486.6 |                868.3 |            6289.0 |           1023.8 |           708.1 |                972.4 |                       926.6 |                     1164.5 |
| deep_nesting    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                  25.8 |                              25.7 |                 57.1 |            2974.5 |             92.6 |            71.2 |                 61.0 |                        54.1 |                      264.3 |
| deep_shadow_400 |     11.5 |                 11.5 |                 11.5 |                    11.5 |                  11.5 |                              11.5 |                 40.1 |              34.7 |            103.1 |            90.6 |                 13.3 |                        13.2 |                       10.2 |
| dense_50k       |   2463.0 |               2463.0 |               2463.0 |                  2463.0 |                2463.0 |                            2462.9 |               6972.3 |            2763.1 |           5351.4 |          3788.7 |               4812.8 |                      4047.6 |                     4671.1 |
| long_ids        |    216.4 |                216.4 |                216.4 |                   216.4 |                 216.4 |                             216.3 |                297.1 |           10427.1 |            307.4 |           249.4 |                269.8 |                       270.3 |                      381.1 |
| lookup_heavy    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                  25.8 |                              25.7 |                 53.7 |             551.3 |             64.3 |            45.0 |                 59.6 |                        53.9 |                      261.0 |
| scope_churn     |      3.9 |                  3.9 |                  3.9 |                     3.9 |                   3.9 |                               3.8 |                  6.4 |            2089.8 |              5.5 |             3.7 |                  4.6 |                         4.9 |                       64.4 |
| shadow_heavy    |      5.0 |                  5.2 |                  5.2 |                     5.5 |                   5.0 |                               7.7 |                 26.7 |            1807.3 |             29.0 |            21.3 |                  7.9 |                         7.6 |                        6.3 |
| short_ids       |     64.2 |                 64.2 |                 64.2 |                    64.2 |                  64.2 |                              64.1 |                200.8 |             599.4 |            189.0 |           127.9 |                151.4 |                       153.5 |                      260.2 |

### Peak heap bytes per live declaration (at the peak)

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     49.3 |                 49.3 |                 49.3 |                    49.3 |                  49.3 |                              49.3 |                 88.0 |             637.6 |            103.8 |            71.8 |                 98.6 |                        93.9 |                      118.1 |
| deep_nesting    |     38.5 |                 38.5 |                 38.5 |                    38.5 |                  38.5 |                              38.3 |                 85.3 |            4440.1 |            138.3 |           106.3 |                 91.1 |                        80.7 |                      394.5 |
| deep_shadow_400 |     29.6 |                 29.6 |                 29.6 |                    29.6 |                  29.6 |                              29.3 |                102.5 |              88.8 |            263.8 |           231.9 |                 34.0 |                        33.8 |                       26.2 |
| dense_50k       |     50.4 |                 50.4 |                 50.4 |                    50.4 |                  50.4 |                              50.4 |                142.8 |              56.6 |            109.6 |            77.6 |                 98.6 |                        82.9 |                       95.7 |
| long_ids        |    118.9 |                118.9 |                118.9 |                   118.9 |                 118.9 |                             118.9 |                163.3 |            5731.3 |            169.0 |           137.1 |                148.3 |                       148.6 |                      209.5 |
| lookup_heavy    |     42.9 |                 42.9 |                 42.9 |                    42.9 |                  42.9 |                              42.8 |                 89.3 |             917.9 |            107.0 |            75.0 |                 99.2 |                        89.8 |                      434.6 |
| scope_churn     |     72.9 |                 72.9 |                 72.9 |                    72.9 |                  72.9 |                              71.1 |                118.5 |           38908.1 |            101.7 |            69.1 |                 85.7 |                        91.3 |                     1198.3 |
| shadow_heavy    |     20.5 |                 21.6 |                 21.6 |                    23.0 |                  20.5 |                              31.7 |                110.8 |            7492.8 |            120.1 |            88.2 |                 32.8 |                        31.6 |                       26.0 |
| short_ids       |     33.6 |                 33.6 |                 33.6 |                    33.6 |                  33.6 |                              33.6 |                105.2 |             314.0 |             99.0 |            67.0 |                 79.3 |                        80.4 |                      136.3 |

### Allocator calls during the whole replay

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |       17 |                   17 |                   17 |                      17 |                    17 |                                17 |               104082 |            158610 |           263707 |          263707 |               263527 |                      263531 |                       3216 |
| deep_nesting    |       10 |                   10 |                   10 |                      10 |                    10 |                                10 |               103095 |             88211 |           127642 |          127741 |                97714 |                       85889 |                        304 |
| deep_shadow_400 |       10 |                   10 |                    8 |                      10 |                    10 |                                 8 |                  268 |               449 |              811 |             811 |                  422 |                          23 |                         23 |
| dense_50k       |       21 |                   21 |                   21 |                      21 |                    21 |                                21 |                26613 |             38253 |            66587 |           66587 |                66603 |                       66606 |                      16623 |
| long_ids        |       14 |                   15 |                   14 |                      14 |                    14 |                                15 |               130673 |            268615 |           188471 |          194169 |               179824 |                       73138 |                       2042 |
| lookup_heavy    |       10 |                   10 |                   10 |                      10 |                    10 |                                10 |                16720 |             14381 |            21175 |           21256 |                16372 |                       14624 |                        293 |
| scope_churn     |        4 |                    4 |                    4 |                       4 |                     4 |                                 4 |               119411 |            119442 |           179448 |          180056 |               150062 |                      134420 |                         29 |
| shadow_heavy    |       16 |                   16 |                    6 |                      19 |                    16 |                                 7 |                73820 |             73856 |           138261 |          160027 |               134922 |                         187 |                         28 |
| short_ids       |       12 |                   12 |                   12 |                      12 |                    12 |                                12 |                43608 |             43648 |           100737 |          104041 |                89672 |                       32801 |                         42 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `synthetic_replay_time.csv`.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     48.0 |                 46.5 |                 45.1 |                    42.7 |                  56.2 |                              78.5 |                104.0 |            9436.2 |            183.5 |           136.5 |                131.4 |                       103.3 |                       51.7 |
| deep_nesting    |     41.9 |                 39.6 |                 42.2 |                    37.2 |                  46.6 |                              46.0 |                 61.3 |              85.2 |            466.2 |           473.8 |                 57.4 |                        55.7 |                       35.4 |
| deep_shadow_400 |      9.3 |                 14.4 |                  7.3 |                     7.6 |                  11.8 |                              16.4 |                219.9 |             270.7 |             25.1 |            23.3 |                  9.3 |                         9.3 |                        9.1 |
| dense_50k       |     69.0 |                 70.4 |                 66.2 |                    58.7 |                  84.7 |                              66.9 |                 89.9 |           10107.2 |             93.2 |            84.4 |                 94.3 |                        75.9 |                       69.6 |
| long_ids        |     83.9 |                 72.3 |                 81.3 |                    79.6 |                 112.6 |                              79.7 |                135.5 |             200.5 |            170.1 |           166.4 |                 81.0 |                        62.1 |                       46.7 |
| lookup_heavy    |     41.9 |                 40.9 |                 42.5 |                    37.3 |                  52.5 |                              38.0 |                 41.7 |              44.1 |            106.9 |           104.5 |                 42.5 |                        33.5 |                       35.0 |
| scope_churn     |     36.4 |                 37.8 |                 35.8 |                    35.0 |                  43.7 |                              48.2 |                 47.6 |              76.8 |             54.1 |            49.0 |                 64.1 |                        46.5 |                       27.9 |
| shadow_heavy    |     33.2 |                 33.6 |                 32.6 |                    31.7 |                  40.1 |                              43.4 |                 74.2 |              97.0 |             82.1 |            75.5 |                 44.8 |                        32.4 |                       33.8 |
| short_ids       |     34.3 |                 39.4 |                 35.4 |                    32.9 |                  41.6 |                              41.2 |                 53.0 |             124.9 |            103.8 |            98.5 |                 48.8 |                        38.3 |                       30.2 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      0.0 |                  0.0 |                  0.0 |                     0.0 |                   0.0 |                               0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| deep_nesting    |     56.9 |                 52.1 |                 59.4 |                    85.4 |                  74.5 |                              53.9 |                 67.2 |              76.9 |           1883.5 |          1887.7 |                 91.4 |                        56.9 |                       59.4 |
| deep_shadow_400 |     25.7 |                 23.4 |                 17.7 |                    17.7 |                  21.7 |                              29.1 |                461.4 |             687.6 |             18.8 |            25.1 |                 18.3 |                        25.1 |                       22.8 |
| dense_50k       |    184.5 |                191.3 |                176.5 |                   198.2 |                 197.6 |                             227.3 |                290.1 |             250.1 |            277.5 |           337.5 |                307.8 |                       205.0 |                      246.7 |
| long_ids        |     81.9 |                140.6 |                 80.7 |                    95.5 |                 117.5 |                             115.7 |                243.2 |             168.5 |            329.3 |           478.8 |                102.0 |                        86.0 |                      108.0 |
| lookup_heavy    |     62.4 |                 55.9 |                 63.0 |                    74.3 |                  92.1 |                              67.1 |                 60.6 |              66.6 |            189.0 |           178.9 |                 63.0 |                        50.5 |                       61.2 |
| scope_churn     |     49.7 |                 51.4 |                 51.4 |                    81.6 |                  80.4 |                              47.9 |                 47.9 |              81.6 |            111.7 |            89.3 |                 90.4 |                        56.2 |                       46.7 |
| shadow_heavy    |     42.2 |                 38.7 |                 47.0 |                    35.1 |                  47.6 |                              83.3 |                101.7 |             118.9 |            240.3 |           258.1 |                 45.2 |                        79.7 |                       47.6 |
| short_ids       |     42.2 |                 32.1 |                 29.7 |                    33.3 |                  35.7 |                              38.6 |                 46.4 |              76.1 |            197.3 |           168.8 |                 76.7 |                        54.1 |                       57.6 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     63.8 |                 67.3 |                 65.6 |                    57.3 |                  75.0 |                              86.2 |                166.5 |           16293.6 |            241.5 |           153.6 |                155.9 |                       133.5 |                       78.5 |
| deep_nesting    |     66.0 |                 61.2 |                 70.9 |                   101.1 |                  87.2 |                              84.2 |                209.5 |             188.3 |            141.7 |           129.6 |                144.1 |                        94.5 |                       72.1 |
| deep_shadow_400 |     25.1 |                 24.6 |                 19.4 |                    18.8 |                  23.4 |                              34.3 |                543.1 |             319.8 |            104.5 |           133.1 |                 34.3 |                        37.7 |                       32.6 |
| dense_50k       |     71.4 |                125.1 |                 73.7 |                    73.1 |                  84.5 |                             163.3 |                289.5 |          100211.4 |            262.1 |           273.0 |                322.1 |                       125.1 |                      186.2 |
| long_ids        |     89.0 |                153.7 |                 88.4 |                   106.8 |                 128.7 |                             149.5 |                422.4 |             481.1 |            189.3 |           212.4 |                163.7 |                       147.7 |                      129.3 |
| lookup_heavy    |     82.0 |                 71.3 |                 82.0 |                    93.9 |                 111.7 |                             108.1 |                208.0 |             215.7 |            163.4 |           119.4 |                120.6 |                        99.8 |                      105.2 |
| scope_churn     |     56.7 |                 58.5 |                 59.7 |                    94.0 |                  93.4 |                              78.6 |                124.7 |             140.1 |            112.9 |            73.3 |                136.5 |                        94.6 |                       57.3 |
| shadow_heavy    |     50.0 |                 45.2 |                 55.9 |                    45.2 |                  55.9 |                             142.7 |                157.0 |             139.2 |            108.2 |            99.3 |                 74.3 |                       107.0 |                       60.1 |
| short_ids       |     49.9 |                 37.4 |                 36.8 |                    41.0 |                  42.2 |                              42.2 |                163.4 |             486.1 |            115.3 |            68.3 |                115.3 |                        86.2 |                       65.4 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |  16901.9 |              16621.4 |              17330.1 |                 23023.9 |               51913.0 |                          128042.3 |             284038.1 |          765315.5 |         889390.2 |        405798.0 |             854766.6 |                    711748.6 |                    14577.4 |
| deep_nesting    |     40.6 |                 38.2 |                 43.0 |                    56.9 |                  41.8 |                              40.0 |                209.5 |             477.2 |            144.7 |           131.4 |                332.5 |                       253.8 |                       27.3 |
| deep_shadow_400 |     12.6 |                  6.9 |                  6.9 |                     7.4 |                   6.9 |                               7.4 |                107.9 |             326.1 |             21.7 |            28.0 |                  4.6 |                         4.6 |                        3.4 |
| dense_50k       |      0.0 |                  0.0 |                  0.0 |                     0.0 |                   0.0 |                               0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| long_ids        |     80.7 |                 99.1 |                 79.5 |                    87.2 |                  83.7 |                              85.4 |                824.0 |            3430.9 |            410.5 |           491.2 |                661.5 |                       614.6 |                       18.4 |
| lookup_heavy    |     45.2 |                 42.2 |                 45.2 |                    58.8 |                  61.8 |                              55.9 |                205.6 |             471.2 |            156.3 |           129.5 |                322.1 |                       262.6 |                       30.3 |
| scope_churn     |     30.7 |                 30.1 |                 31.3 |                    53.2 |                  46.1 |                              41.4 |                119.4 |             626.6 |             83.9 |            61.5 |                399.0 |                       274.9 |                        5.3 |
| shadow_heavy    |     26.8 |                 26.2 |                 27.4 |                    26.2 |                  26.8 |                             113.0 |                164.7 |             624.4 |            143.3 |           127.9 |                 38.1 |                        55.3 |                       29.7 |
| short_ids       |     85.0 |                 60.0 |                 61.8 |                    75.5 |                  67.2 |                              60.0 |                287.0 |             756.0 |            176.5 |           133.1 |                394.6 |                       312.6 |                       22.0 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace           |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:----------------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| big_scope_exit  |               868.3 |  486.6 |               44.0 |       104082 |           17 |           100.0 |            20.8 |             9.6 |            53.6 |     48.1 |      56.0 | yes           |              0.0 |              0.0 |               nan   |                 61.7 |              94.0 |             0 |
| deep_nesting    |                57.1 |   25.8 |               54.9 |       103095 |           10 |           100.0 |            18.4 |            12.6 |            32.1 |     29.0 |      34.7 | yes           |             67.2 |             56.9 |                15.3 |                 68.5 |              80.6 |             0 |
| deep_shadow_400 |                40.1 |   11.5 |               71.2 |          268 |           10 |            96.3 |             0.4 |             0.0 |            96.4 |     96.3 |      96.6 | yes           |            461.4 |             25.7 |                94.4 |                 95.4 |              88.3 |           149 |
| dense_50k       |              6972.3 | 2463.0 |               64.7 |        26613 |           21 |            99.9 |            22.5 |            17.3 |            26.8 |     20.9 |      33.3 | yes           |            290.1 |            184.5 |                36.4 |                 75.3 |             nan   |             0 |
| long_ids        |               297.1 |  216.4 |               27.2 |       130673 |           14 |           100.0 |            40.7 |            25.2 |            38.9 |     37.9 |      41.0 | yes           |            243.2 |             81.9 |                66.3 |                 78.9 |              90.2 |             0 |
| lookup_heavy    |                53.7 |   25.8 |               52.0 |        16720 |           10 |            99.9 |            12.5 |            12.6 |             0.1 |     -2.8 |       1.5 | no            |             60.6 |             62.4 |                -3.0 |                 60.6 |              78.0 |             0 |
| scope_churn     |                 6.4 |    3.9 |               38.5 |       119411 |            4 |           100.0 |            15.7 |            12.0 |            26.3 |     19.5 |      29.5 | yes           |             47.9 |             49.7 |                -3.8 |                 54.5 |              74.3 |             0 |
| shadow_heavy    |                26.7 |    5.0 |               81.5 |        73820 |           16 |           100.0 |            22.3 |            10.0 |            54.3 |     51.1 |      56.1 | yes           |            101.7 |             42.2 |                58.5 |                 68.2 |              83.7 |             0 |
| short_ids       |               200.8 |   64.2 |               68.0 |        43608 |           12 |           100.0 |            15.9 |            10.3 |            36.0 |     30.8 |      37.6 | yes           |             46.4 |             42.2 |                 9.1 |                 69.5 |              70.4 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                        |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| arena + chains (allocator-free) |        9 |                      6 |                      1 |                   -2.5 |     -0.1 |  35.3 |                    -12.5 |      16.3 |   51.3 |
| METIS-X (previous)              |        9 |                      8 |                      0 |                   27.2 |     54.9 |  81.5 |                      0.1 |      36.0 |   96.4 |
| old arena table                 |        9 |                      9 |                      0 |                   10.9 |     95.3 |  99.8 |                      4.8 |      64.3 |   99.5 |
| old scope maps                  |        9 |                      9 |                      0 |                   28.3 |     59.9 |  88.8 |                     28.8 |      61.2 |   90.9 |
| map per scope                   |        9 |                      9 |                      0 |                   -5.5 |     42.8 |  87.3 |                     21.4 |      59.6 |   91.3 |
| std map + undo log              |        9 |                      7 |                      0 |                   13.1 |     48.8 |  57.8 |                     -2.0 |      26.8 |   64.4 |
| Swiss node map + undo log       |        9 |                      5 |                      2 |                   12.5 |     39.1 |  58.2 |                    -34.2 |       9.3 |   56.1 |
| Swiss flat map, interned        |        9 |                      1 |                      5 |                  -12.8 |     58.2 |  93.9 |                    -74.0 |     -13.9 |   11.0 |

## D. Worst-case clustering

### STRATA lookup cost when every key is forced into one probe cluster

Best of 7 rounds, batch-timed. With all keys in one cluster a lookup scans the cluster: cost grows linearly.

|   live_names | hash                 |   ns_per_lookup_hit |   ns_per_lookup_miss |   ns_per_declare |
|-------------:|:---------------------|--------------------:|---------------------:|-----------------:|
|           16 | normal               |                12.7 |                 10.1 |            127.5 |
|           16 | all_keys_one_cluster |                14.4 |                 22.0 |            145.9 |
|           64 | normal               |                10.3 |                  9.5 |             76.8 |
|           64 | all_keys_one_cluster |                41.5 |                 67.4 |            141.1 |
|          256 | normal               |                10.9 |                  9.8 |             62.6 |
|          256 | all_keys_one_cluster |               110.2 |                206.6 |            212.7 |
|         1024 | normal               |                11.1 |                 10.7 |             49.8 |
|         1024 | all_keys_one_cluster |               398.4 |                770.0 |            649.5 |
|         4096 | normal               |                16.0 |                 19.2 |             49.4 |
|         4096 | all_keys_one_cluster |              1589.7 |               3078.2 |           2506.2 |

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

48 table/trace pairs were checked against the reference model; 48 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |    292.0 |                292.0 |                292.0 |                   292.0 |                 292.0 |                             292.0 |                877.0 |             776.7 |            754.6 |           525.7 |                652.8 |                       551.6 |                     1182.1 |
| ESP-IDF  |   7481.0 |               7481.0 |               7481.0 |                  7481.0 |                 nan   |                            7480.9 |              15375.6 |             nan   |          19842.2 |         13985.2 |              18289.0 |                     18105.5 |                    41420.0 |
| FreeRTOS |    292.0 |                292.0 |                292.0 |                   292.0 |                 292.0 |                             292.0 |                937.6 |            1158.9 |            758.1 |           534.9 |                651.2 |                       550.4 |                     1230.7 |
| Zephyr   |   1870.3 |               1870.3 |               2216.7 |                  1870.3 |                 nan   |                            2216.6 |               7572.2 |             nan   |           5792.1 |          4154.9 |               5211.4 |                      4473.8 |                    19054.5 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.1 |                 43.1 |                 43.1 |                    43.1 |                  43.1 |                              43.1 |                129.5 |             114.7 |            111.4 |            77.6 |                 96.4 |                        81.4 |                      174.5 |
| ESP-IDF  |     49.9 |                 49.9 |                 49.9 |                    49.9 |                 nan   |                              49.9 |                102.6 |             nan   |            132.3 |            93.3 |                122.0 |                       120.8 |                      276.3 |
| FreeRTOS |     46.6 |                 46.6 |                 46.6 |                    46.6 |                  46.6 |                              46.6 |                149.7 |             185.0 |            121.1 |            85.4 |                104.0 |                        87.9 |                      196.5 |
| Zephyr   |     41.7 |                 41.7 |                 49.4 |                    41.7 |                 nan   |                              49.4 |                168.8 |             nan   |            129.1 |            92.6 |                116.2 |                        99.7 |                      424.8 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     16.0 |                 16.0 |                 16.0 |                    16.0 |                  16.0 |                              16.0 |              19804.0 |           26299.0 |          35323.0 |         43882.0 |              39468.0 |                     29565.0 |                     3385.0 |
| ESP-IDF  |     24.0 |                 24.0 |                 24.0 |                    24.0 |                 nan   |                              24.0 |             629511.0 |             nan   |        1032063.0 |       1342739.0 |            1225740.0 |                    860749.0 |                   168333.0 |
| FreeRTOS |     16.0 |                 16.0 |                 16.0 |                    16.0 |                  16.0 |                              16.0 |              32473.0 |           50714.0 |          53727.0 |        115265.0 |             108616.0 |                     41135.0 |                     4786.0 |
| Zephyr   |     25.0 |                 25.0 |                 21.0 |                    25.0 |                 nan   |                              21.0 |             664319.0 |             nan   |        1056367.0 |       1116929.0 |             974653.0 |                    870284.0 |                   147498.0 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `legacy_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     39.5 |                 43.5 |                 47.2 |                    39.7 |                  48.5 |                              41.5 |                 65.1 |             743.6 |             84.2 |            78.0 |                 65.7 |                        55.6 |                       45.7 |
| ESP-IDF  |     46.0 |                 37.4 |                 33.4 |                    46.0 |                 nan   |                              41.1 |                 90.4 |             nan   |            145.6 |           149.2 |                130.4 |                       106.3 |                       78.1 |
| FreeRTOS |     38.2 |                 38.0 |                 37.3 |                    37.5 |                  48.5 |                              40.0 |                 48.0 |             623.8 |             65.5 |            70.7 |                 52.0 |                        42.6 |                       36.1 |
| Zephyr   |     53.8 |                 44.2 |                 50.9 |                    48.0 |                 nan   |                              49.4 |                 95.0 |             nan   |            168.5 |           118.8 |                119.5 |                        93.3 |                       79.4 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (17 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     53.3 |                 51.5 |                 52.1 |                    46.7 |                  60.9 |                              46.2 |                 59.8 |              66.9 |            121.9 |           120.1 |                 61.5 |                        63.3 |                       62.1 |
| ESP-IDF  |     73.0 |                 52.8 |                 65.3 |                    58.7 |                 nan   |                              52.8 |                 94.9 |             nan   |            163.1 |           167.9 |                112.7 |                       110.9 |                       90.2 |
| FreeRTOS |     62.7 |                 52.0 |                 55.6 |                    48.5 |                  72.2 |                              64.5 |                 71.0 |              78.7 |            117.7 |           146.1 |                 65.1 |                        53.8 |                       53.8 |
| Zephyr   |     61.1 |                 50.4 |                 54.0 |                    60.5 |                 nan   |                              51.0 |                 68.8 |             nan   |            278.7 |           249.1 |                 85.4 |                        64.6 |                       66.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (17 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     75.7 |                 78.7 |                 75.7 |                    75.7 |                  88.8 |                              95.9 |                211.2 |            7190.8 |            188.7 |           160.9 |                165.7 |                       153.2 |                      124.8 |
| ESP-IDF  |    178.5 |                151.9 |                148.3 |                   156.6 |                 nan   |                             245.6 |                479.3 |             nan   |            619.3 |           623.4 |               1169.8 |                       511.9 |                      485.8 |
| FreeRTOS |     86.4 |                 71.6 |                 74.5 |                    73.9 |                  94.6 |                             113.0 |                186.9 |            5228.4 |            195.8 |           205.8 |                172.1 |                       117.1 |                      100.5 |
| Zephyr   |    119.2 |                128.7 |                117.4 |                   137.6 |                 nan   |                             188.0 |                305.4 |             nan   |            407.4 |           323.2 |                520.1 |                       315.5 |                      329.7 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (17 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   STRATA (keyed hash) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.8 |                 42.0 |                 42.0 |                    43.8 |                  43.8 |                              55.6 |                263.3 |             709.4 |            203.5 |           163.3 |                547.3 |                       507.7 |                       34.3 |
| ESP-IDF  |     35.6 |                 38.0 |                 40.3 |                    42.7 |                 nan   |                              49.8 |                434.8 |             nan   |            229.0 |           208.2 |                799.0 |                       663.8 |                       22.5 |
| FreeRTOS |     30.8 |                 30.2 |                 29.6 |                    31.3 |                  33.7 |                              49.7 |                150.8 |             510.4 |            150.8 |           163.2 |                300.5 |                       281.5 |                       21.3 |
| Zephyr   |     46.3 |                 44.5 |                 43.9 |                    52.2 |                 nan   |                              54.0 |                245.5 |             nan   |            270.4 |           208.2 |                542.6 |                       449.5 |                       23.7 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| Arduino  |               877.0 |  292.0 |               66.7 |        19804 |           16 |            99.9 |             6.1 |             3.7 |            34.6 |     27.2 |      42.6 | yes           |             59.8 |             53.3 |                10.9 |                 64.2 |              83.4 |             0 |
| ESP-IDF  |             15375.6 | 7481.0 |               51.3 |       629511 |           24 |           100.0 |           201.6 |           102.5 |            39.9 |     38.4 |      59.0 | yes           |             94.9 |             73.0 |                23.1 |                 62.8 |              91.8 |             0 |
| FreeRTOS |               937.6 |  292.0 |               68.9 |        32473 |           16 |           100.0 |            10.9 |             8.7 |            18.7 |      2.8 |      27.4 | yes           |             71.0 |             62.7 |                11.7 |                 53.8 |              79.6 |             0 |
| Zephyr   |              7572.2 | 1870.3 |               75.3 |       664319 |           25 |           100.0 |           247.7 |           140.3 |            42.5 |     31.3 |      47.1 | yes           |             68.8 |             61.1 |                11.2 |                 61.0 |              81.1 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                        |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| arena + chains (allocator-free) |        4 |                      0 |                      0 |                   -0.0 |     -0.0 |  15.6 |                     -3.3 |       1.3 |    5.4 |
| METIS-X (previous)              |        4 |                      4 |                      0 |                   51.3 |     67.8 |  75.3 |                     18.7 |      37.2 |   42.5 |
| old arena table                 |        2 |                      2 |                      0 |                   62.4 |     68.6 |  74.8 |                     93.5 |      94.1 |   94.7 |
| old scope maps                  |        4 |                      4 |                      0 |                   61.3 |     61.9 |  67.7 |                     39.7 |      58.7 |   69.5 |
| map per scope                   |        4 |                      4 |                      0 |                   44.4 |     46.0 |  55.0 |                     45.9 |      55.5 |   69.8 |
| std map + undo log              |        4 |                      4 |                      0 |                   55.2 |     57.2 |  64.1 |                     28.9 |      44.9 |   65.9 |
| Swiss node map + undo log       |        4 |                      3 |                      0 |                   46.9 |     52.6 |  58.7 |                     13.5 |      37.4 |   57.0 |
| Swiss flat map, interned        |        4 |                      2 |                      0 |                   75.3 |     79.1 |  90.2 |                     -5.7 |      22.5 |   43.2 |

