# Result tables for run `20261011-161306-final`

```
run: results/raw/20261011-161306-final
date_utc: 2026-10-11T16:13:24Z
git_commit: 3aee3811874f05212b8108fe70cb3a75051613fb
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
| cjson    |     32.2 |                 30.7 |                 32.6 |                    28.2 |                 36.2 |             114.4 |             47.6 |            41.6 |                 35.1 |                        35.4 |                       26.3 |
| freertos |     39.2 |                 35.9 |                 40.4 |                    33.7 |                 76.5 |             115.0 |             62.0 |            49.0 |                 41.9 |                        64.3 |                       49.3 |
| littlefs |     29.8 |                 29.8 |                 29.8 |                    25.6 |                 34.8 |              59.9 |             54.6 |            51.6 |                 31.2 |                        32.4 |                       23.4 |
| lua      |     38.7 |                 39.8 |                 52.2 |                    33.3 |                 50.0 |             124.8 |             58.4 |            53.1 |                 44.9 |                        48.7 |                       34.3 |
| mbedtls  |     46.7 |                 42.4 |                 46.1 |                    43.5 |                 62.0 |             163.9 |             69.3 |            56.1 |                 57.3 |                        56.9 |                       39.2 |
| sqlite   |     30.0 |                 30.3 |                 39.7 |                    28.2 |                 36.9 |              86.3 |             64.3 |            61.6 |                 29.6 |                        31.8 |                       28.1 |
| tinycc   |     33.6 |                 32.8 |                 33.5 |                    28.2 |                 35.6 |             275.5 |             67.4 |            59.3 |                 42.0 |                        32.4 |                       25.2 |
| zlib     |     27.8 |                 27.6 |                 29.0 |                    24.2 |                 36.5 |             122.2 |             57.1 |            46.7 |                 40.2 |                        38.2 |                       24.8 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (19 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     52.7 |                 47.2 |                 53.3 |                    48.4 |                 66.0 |              55.7 |            114.5 |           109.0 |                 59.3 |                        45.4 |                       44.8 |
| freertos |     55.7 |                 50.3 |                 55.7 |                    50.9 |                 65.4 |              62.4 |            169.0 |           123.5 |                 58.1 |                        86.6 |                       85.4 |
| littlefs |     58.1 |                 50.9 |                 52.7 |                    46.0 |                 49.7 |              55.1 |            138.7 |           128.4 |                 50.9 |                        46.6 |                       46.6 |
| lua      |     78.7 |                 69.0 |                 55.7 |                    81.2 |                 54.5 |              71.5 |            114.5 |           115.7 |                 85.4 |                        55.7 |                       54.5 |
| mbedtls  |     71.5 |                 72.7 |                 64.2 |                    60.6 |                 73.9 |              82.4 |            114.5 |           127.2 |                 72.7 |                        57.5 |                       64.2 |
| sqlite   |     56.9 |                 64.2 |                 53.3 |                    55.1 |                 64.2 |              63.6 |            249.5 |           182.9 |                 87.8 |                        63.0 |                       74.5 |
| tinycc   |     61.7 |                 51.5 |                 53.9 |                    47.2 |                 51.5 |              54.5 |            145.9 |           141.0 |                 75.1 |                        47.8 |                       48.4 |
| zlib     |     47.8 |                 47.2 |                 46.0 |                    45.4 |                 46.0 |              56.3 |            119.3 |           110.2 |                 51.5 |                        43.6 |                       82.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (19 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     74.5 |                 68.4 |                 76.3 |                    63.0 |                155.0 |            1099.2 |            146.6 |           107.8 |                115.1 |                       106.0 |                       73.3 |
| freertos |     82.4 |                 73.3 |                 83.6 |                    65.4 |                221.0 |            1074.3 |            218.0 |           122.3 |                119.3 |                       193.8 |                      156.2 |
| littlefs |     89.6 |                 77.5 |                 83.0 |                    63.0 |                192.0 |             724.3 |            155.0 |           116.9 |                119.9 |                       104.8 |                       78.1 |
| lua      |     95.7 |                 95.1 |                 80.5 |                   102.4 |                164.1 |            1061.1 |            142.3 |           114.5 |                159.9 |                       118.1 |                       88.4 |
| mbedtls  |     98.1 |                 94.5 |                 89.6 |                    75.1 |                198.0 |            1441.9 |            166.5 |           139.3 |                133.2 |                       121.7 |                      115.7 |
| sqlite   |     84.2 |                 96.9 |                 83.0 |                    77.5 |                195.0 |            3445.2 |            219.9 |           150.2 |                182.9 |                       112.7 |                      189.6 |
| tinycc   |    145.9 |                 80.5 |                 86.0 |                    65.4 |                182.8 |            6504.4 |            146.5 |           108.4 |                168.9 |                       104.1 |                       86.6 |
| zlib     |     69.7 |                 73.3 |                 65.4 |                    59.4 |                152.0 |             653.5 |            161.7 |           118.7 |                113.3 |                       105.4 |                      132.0 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (19 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     92.1 |                 83.0 |                 90.2 |                    76.9 |                 63.6 |             155.0 |             54.5 |            41.2 |                121.7 |                       120.5 |                        9.7 |
| freertos |    117.5 |                111.4 |                116.9 |                    98.1 |                 97.5 |             233.2 |            113.2 |            64.8 |                149.0 |                       250.7 |                       31.5 |
| littlefs |    123.5 |                118.1 |                117.5 |                    92.7 |                109.6 |             216.2 |             69.6 |            59.4 |                147.2 |                       144.7 |                       15.1 |
| lua      |    129.6 |                139.3 |                116.9 |                   139.3 |                 84.2 |             210.2 |             73.3 |            60.0 |                187.1 |                       166.5 |                       18.2 |
| mbedtls  |    171.4 |                179.9 |                159.3 |                   136.9 |                110.8 |             307.6 |            101.7 |            84.2 |                220.4 |                       210.7 |                       24.8 |
| sqlite   |    100.5 |                118.7 |                 97.5 |                    94.5 |                 73.9 |             239.3 |            104.8 |            66.0 |                172.6 |                       139.3 |                       27.9 |
| tinycc   |    121.1 |                105.9 |                105.3 |                    81.7 |                 76.9 |             167.1 |             61.1 |            50.8 |                174.9 |                       115.6 |                       15.1 |
| zlib     |     97.5 |                102.4 |                 92.7 |                    84.8 |                 64.8 |             228.9 |             72.7 |            59.4 |                142.3 |                       135.7 |                       27.3 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |   new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| cjson    |               102.7 |  42.8 |               58.3 |         3604 |           22 |            99.4 |             0.8 |             0.7 |             7.7 |      4.4 |      15.7 | yes           |             66.0 |             52.7 |                20.2 |                 51.9 |             -44.8 |             0 |
| freertos |               217.4 |  57.8 |               73.4 |         8282 |           81 |            99.0 |             2.9 |             1.5 |            45.8 |     33.2 |      53.6 | yes           |             65.4 |             55.7 |                14.8 |                 62.7 |             -20.5 |             0 |
| littlefs |               106.9 |  25.8 |               75.9 |         2774 |           19 |            99.3 |             0.7 |             0.6 |            15.6 |     10.7 |      36.5 | yes           |             49.7 |             58.1 |               -16.9 |                 53.3 |             -12.7 |             0 |
| lua      |               106.8 |  64.2 |               39.9 |        40494 |          336 |            99.2 |             9.4 |             7.3 |            15.3 |      9.9 |      26.5 | yes           |             54.5 |             78.7 |               -44.4 |                 41.7 |             -53.9 |             0 |
| mbedtls  |               234.4 | 144.3 |               38.5 |       255849 |         1154 |            99.5 |            61.0 |            45.9 |            26.1 |     16.9 |      28.7 | yes           |             73.9 |             71.5 |                 3.2 |                 50.5 |             -54.7 |             0 |
| sqlite   |               451.1 | 194.7 |               56.8 |        22711 |           15 |            99.9 |             9.9 |             8.1 |            18.1 |      2.4 |      26.2 | yes           |             64.2 |             56.9 |                11.4 |                 56.8 |             -36.0 |             0 |
| tinycc   |               423.1 | 324.5 |               23.3 |         9665 |           15 |            99.8 |             3.2 |             3.0 |             7.0 |     -2.9 |      19.1 | no            |             51.5 |             61.7 |               -19.8 |                 20.2 |             -57.5 |             0 |
| zlib     |                52.6 |  17.2 |               67.3 |        10412 |          133 |            98.7 |             2.1 |             1.6 |            24.8 |     15.8 |      30.7 | yes           |             46.0 |             47.8 |                -3.9 |                 54.1 |             -50.5 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        8 |                      7 |                      0 |                   23.3 |     57.6 |  75.9 |                      7.0 |      16.8 |   45.8 |
| old arena table           |        8 |                      8 |                      0 |                   26.6 |     56.1 |  62.4 |                     50.2 |      70.9 |   87.4 |
| old scope maps            |        8 |                      8 |                      0 |                   44.6 |     59.2 |  72.0 |                     31.7 |      41.9 |   53.5 |
| map per scope             |        8 |                      8 |                      0 |                   23.6 |     41.0 |  61.2 |                     15.9 |      31.8 |   49.4 |
| std map + undo log        |        8 |                      6 |                      0 |                   41.1 |     61.4 |  71.5 |                      1.4 |       7.7 |   32.8 |
| Swiss node map + undo log |        8 |                      6 |                      0 |                   27.8 |     55.1 |  68.8 |                    -10.0 |      11.9 |   36.9 |
| Swiss flat map, interned  |        8 |                      1 |                      5 |                   43.6 |     72.7 |  82.7 |                    -31.3 |     -16.7 |   18.9 |

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
| freertos |     1.3 |     1.3 |     1.4 |     1.3 |
| littlefs |     0.6 |     0.6 |     0.6 |     0.6 |
| lua      |     6.6 |     6.8 |     6.6 |     7.0 |
| mbedtls  |    41.5 |    41.0 |    40.4 |    41.1 |
| sqlite   |     8.3 |     9.0 |     7.6 |     7.4 |
| tinycc   |     3.8 |     3.3 |     2.9 |     2.7 |
| zlib     |     1.4 |     1.5 |     1.5 |     1.6 |

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
| deep_nesting    |     21.7 |                 21.7 |                 25.8 |                    25.8 |                 57.1 |            2974.5 |             92.6 |            71.2 |                 61.0 |                        54.1 |                      264.2 |
| deep_shadow_400 |     11.5 |                 11.5 |                 11.5 |                    11.5 |                 40.1 |              34.8 |            103.1 |            90.6 |                 13.3 |                        13.2 |                       10.2 |
| dense_50k       |   2462.9 |               2462.9 |               2462.9 |                  2462.9 |               6972.3 |            2763.1 |           5351.5 |          3788.7 |               4812.7 |                      4047.7 |                     4671.1 |
| long_ids        |    273.7 |                273.7 |                216.4 |                   243.4 |                297.2 |           10427.1 |            307.4 |           249.5 |                269.8 |                       270.3 |                      381.2 |
| lookup_heavy    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                 53.7 |             551.3 |             64.3 |            45.0 |                 59.6 |                        53.9 |                      261.0 |
| scope_churn     |      3.9 |                  3.9 |                  3.9 |                     3.9 |                  6.4 |            2089.8 |              5.5 |             3.7 |                  4.6 |                         4.9 |                       64.4 |
| shadow_heavy    |      5.0 |                  5.0 |                  5.2 |                     5.3 |                 26.7 |            1807.3 |             29.0 |            21.3 |                  7.9 |                         7.6 |                        6.3 |
| short_ids       |     64.2 |                 64.2 |                 64.2 |                    64.2 |                200.8 |             599.4 |            189.0 |           127.9 |                151.4 |                       153.5 |                      260.2 |

### Peak heap bytes per live declaration (at the peak)

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     49.3 |                 49.3 |                 49.3 |                    49.3 |                 88.0 |             637.6 |            103.8 |            71.8 |                 98.6 |                        93.9 |                      118.1 |
| deep_nesting    |     32.4 |                 32.4 |                 38.4 |                    38.4 |                 85.3 |            4440.1 |            138.3 |           106.3 |                 91.1 |                        80.7 |                      394.4 |
| deep_shadow_400 |     29.5 |                 29.5 |                 29.5 |                    29.5 |                102.6 |              89.0 |            263.9 |           231.8 |                 34.0 |                        33.8 |                       26.2 |
| dense_50k       |     50.4 |                 50.4 |                 50.4 |                    50.4 |                142.8 |              56.6 |            109.6 |            77.6 |                 98.6 |                        82.9 |                       95.7 |
| long_ids        |    150.5 |                150.5 |                118.9 |                   133.8 |                163.3 |            5731.3 |            169.0 |           137.2 |                148.3 |                       148.6 |                      209.5 |
| lookup_heavy    |     42.9 |                 42.9 |                 42.9 |                    42.9 |                 89.3 |             917.9 |            107.0 |            75.0 |                 99.2 |                        89.8 |                      434.6 |
| scope_churn     |     72.3 |                 72.3 |                 72.3 |                    72.3 |                118.5 |           38908.1 |            101.7 |            69.1 |                 85.7 |                        91.3 |                     1198.3 |
| shadow_heavy    |     20.5 |                 20.5 |                 21.5 |                    21.8 |                110.8 |            7492.8 |            120.1 |            88.2 |                 32.8 |                        31.5 |                       26.0 |
| short_ids       |     33.6 |                 33.6 |                 33.6 |                    33.6 |                105.2 |             314.0 |             99.0 |            67.0 |                 79.3 |                        80.4 |                      136.3 |

### Allocator calls during the whole replay

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      199 |                  199 |                   17 |                      17 |               104082 |            158610 |           263707 |          263707 |               263527 |                      263531 |                       3216 |
| deep_nesting    |       14 |                   14 |                   10 |                      10 |               103095 |             88211 |           127642 |          127741 |                97714 |                       85889 |                        304 |
| deep_shadow_400 |       11 |                   11 |                    8 |                      11 |                  268 |               449 |              811 |             811 |                  422 |                          23 |                         23 |
| dense_50k       |       21 |                   21 |                   21 |                      21 |                26613 |             38253 |            66587 |           66587 |                66603 |                       66606 |                      16623 |
| long_ids        |       20 |                   20 |                   14 |                      17 |               130673 |            268615 |           188471 |          194169 |               179824 |                       73138 |                       2042 |
| lookup_heavy    |       10 |                   10 |                   10 |                      10 |                16720 |             14381 |            21175 |           21256 |                16372 |                       14624 |                        293 |
| scope_churn     |        4 |                    4 |                    4 |                       4 |               119411 |            119442 |           179448 |          180056 |               150062 |                      134420 |                         29 |
| shadow_heavy    |       93 |                   79 |                    6 |                      71 |                73820 |             73856 |           138261 |          160027 |               134922 |                         187 |                         28 |
| short_ids       |       12 |                   12 |                   12 |                      12 |                43608 |             43648 |           100737 |          104041 |                89672 |                       32801 |                         42 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `synthetic_replay_time.csv`.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    137.9 |                146.3 |                 73.1 |                    60.6 |                105.9 |            9641.8 |            192.2 |           140.2 |                140.5 |                       118.8 |                       47.7 |
| deep_nesting    |     50.6 |                 46.9 |                 51.5 |                    44.4 |                 64.7 |              86.2 |            484.0 |           477.1 |                 62.1 |                        54.8 |                       34.5 |
| deep_shadow_400 |      8.4 |                 14.1 |                  8.2 |                     7.5 |                228.7 |             291.4 |             24.9 |            23.1 |                  8.5 |                         9.6 |                        9.4 |
| dense_50k       |     74.3 |                 85.3 |                131.1 |                    77.2 |                103.3 |           10356.5 |            109.4 |            89.3 |                 94.0 |                        79.8 |                       70.2 |
| long_ids        |     99.1 |                 78.0 |                100.4 |                    93.1 |                137.5 |             208.1 |            187.3 |           164.2 |                 85.5 |                        60.9 |                       48.2 |
| lookup_heavy    |     46.0 |                 40.7 |                 48.7 |                    37.5 |                 41.1 |              48.7 |            105.8 |           103.2 |                 43.5 |                        35.0 |                       43.7 |
| scope_churn     |     55.7 |                 51.2 |                 50.9 |                    51.6 |                 56.9 |              77.6 |             58.1 |            50.8 |                 69.6 |                        57.4 |                       31.4 |
| shadow_heavy    |     37.5 |                 37.8 |                 37.1 |                    39.1 |                 81.0 |              98.1 |             99.4 |            84.2 |                 48.8 |                        34.2 |                       38.2 |
| short_ids       |     38.9 |                 43.0 |                 40.7 |                    36.8 |                 58.6 |             142.1 |            120.2 |           107.7 |                 53.5 |                        41.0 |                       31.4 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      0.0 |                  0.0 |                  0.0 |                     0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| deep_nesting    |     85.4 |                 74.5 |                 71.5 |                    64.2 |                 66.0 |              86.0 |           2337.0 |          1897.9 |                 74.5 |                       106.0 |                       98.7 |
| deep_shadow_400 |     18.2 |                 21.8 |                 17.6 |                    17.6 |                537.2 |             729.8 |             18.8 |            17.6 |                 17.0 |                        22.4 |                       21.8 |
| dense_50k       |    227.7 |                423.4 |                496.6 |                   210.2 |                389.4 |             262.9 |            399.1 |           330.7 |                271.3 |                       343.4 |                      354.3 |
| long_ids        |    135.0 |                101.7 |                124.1 |                   110.8 |                182.9 |             189.5 |            408.7 |           393.6 |                104.1 |                        91.4 |                       86.6 |
| lookup_heavy    |     62.4 |                 55.7 |                 83.0 |                    56.3 |                 72.1 |              67.8 |            266.4 |           188.3 |                 73.9 |                        55.1 |                       60.6 |
| scope_churn     |     84.2 |                 50.3 |                 53.9 |                    53.9 |                 53.9 |              68.4 |             95.1 |            92.7 |                 61.2 |                        47.8 |                       50.9 |
| shadow_heavy    |     40.0 |                 46.6 |                 40.6 |                    38.8 |                108.4 |             138.7 |            264.7 |           250.7 |                 47.2 |                        44.2 |                       64.2 |
| short_ids       |     87.8 |                 74.5 |                 51.5 |                    61.8 |                 52.7 |              89.0 |            358.5 |           242.2 |                 92.1 |                        73.3 |                       91.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    101.7 |                 95.1 |                 89.0 |                    81.2 |                167.8 |           19888.4 |            265.3 |           155.0 |                163.5 |                       166.6 |                       93.3 |
| deep_nesting    |    103.0 |                 93.9 |                 87.8 |                    78.7 |                202.3 |             210.1 |            196.8 |           118.1 |                114.5 |                       161.1 |                      122.3 |
| deep_shadow_400 |     20.0 |                 23.6 |                 20.0 |                    20.0 |                567.5 |             337.9 |            111.4 |           112.0 |                 33.9 |                        38.2 |                       34.5 |
| dense_50k       |     95.1 |                179.9 |                136.9 |                   121.7 |                267.7 |          105371.5 |            360.4 |           261.6 |                221.1 |                       176.2 |                      164.7 |
| long_ids        |    147.1 |                118.7 |                138.0 |                   121.1 |                322.1 |             503.1 |            251.9 |           180.4 |                175.0 |                       145.9 |                      104.1 |
| lookup_heavy    |     90.8 |                 85.4 |                108.4 |                    78.7 |                223.5 |             218.0 |            227.7 |           147.8 |                139.3 |                       111.4 |                       93.9 |
| scope_churn     |    101.7 |                 60.0 |                 64.2 |                    66.0 |                137.5 |             106.0 |             95.7 |            76.3 |                 87.2 |                        70.3 |                       61.2 |
| shadow_heavy    |     47.8 |                 53.3 |                 47.8 |                    44.8 |                163.5 |             166.5 |            124.1 |            95.7 |                 74.5 |                        57.5 |                       83.0 |
| short_ids       |    104.2 |                 88.4 |                 65.4 |                    74.5 |                169.6 |             508.1 |            191.4 |           109.6 |                130.2 |                       110.2 |                      111.4 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  | 350067.5 |             352640.0 |             326034.6 |                264268.4 |             336804.0 |          918017.1 |        1274788.5 |        645027.3 |             648349.3 |                    742352.2 |                     9539.0 |
| deep_nesting    |    213.8 |                228.3 |                222.3 |                   172.6 |                203.5 |             463.9 |            186.5 |           128.4 |                308.2 |                       365.8 |                       34.5 |
| deep_shadow_400 |      5.5 |                  5.5 |                  4.2 |                     5.5 |                110.2 |             374.3 |             20.6 |            21.8 |                  2.4 |                         2.4 |                        0.6 |
| dense_50k       |      0.0 |                  0.0 |                  0.0 |                     0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| long_ids        |    448.7 |                469.2 |                430.5 |                   380.8 |                635.7 |            3532.9 |            492.8 |           451.1 |                672.7 |                       616.4 |                       28.5 |
| lookup_heavy    |    233.1 |                227.1 |                238.6 |                   190.1 |                219.8 |             451.7 |            194.4 |           147.2 |                334.9 |                       282.8 |                       30.3 |
| scope_churn     |    250.1 |                171.4 |                167.8 |                   170.2 |                133.8 |             472.4 |             69.6 |            62.4 |                261.0 |                       189.6 |                        7.3 |
| shadow_heavy    |     38.2 |                 38.8 |                 39.4 |                    38.8 |                172.0 |             641.3 |            155.6 |           126.6 |                 38.2 |                        37.5 |                       35.1 |
| short_ids       |    366.4 |                307.7 |                294.3 |                   242.9 |                324.0 |             823.6 |            304.0 |           195.6 |                439.1 |                       366.4 |                       38.2 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace           |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:----------------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| big_scope_exit  |               868.2 |  486.6 |               44.0 |       104082 |          199 |            99.8 |            21.2 |            27.6 |           -30.7 |    -38.8 |     -17.8 | yes           |              0.0 |              0.0 |               nan   |                 39.4 |              -3.9 |             0 |
| deep_nesting    |                57.1 |   21.7 |               62.0 |       103095 |           14 |           100.0 |            19.4 |            15.2 |            21.1 |     15.8 |      30.2 | yes           |             66.0 |             85.4 |               -29.4 |                 49.1 |              -5.1 |             0 |
| deep_shadow_400 |                40.1 |   11.5 |               71.3 |          268 |           11 |            95.9 |             0.5 |             0.0 |            96.3 |     96.3 |      96.5 | yes           |            537.2 |             18.2 |                96.6 |                 96.5 |              95.0 |           149 |
| dense_50k       |              6972.3 | 2462.9 |               64.7 |        26613 |           21 |            99.9 |            25.8 |            18.6 |            26.4 |     23.0 |      35.1 | yes           |            389.4 |            227.7 |                41.5 |                 64.5 |             nan   |             0 |
| long_ids        |               297.2 |  273.7 |                7.9 |       130673 |           20 |           100.0 |            41.2 |            29.7 |            28.8 |     24.6 |      43.1 | yes           |            182.9 |            135.0 |                26.2 |                 54.3 |              29.4 |             0 |
| lookup_heavy    |                53.7 |   25.8 |               52.0 |        16720 |           10 |            99.9 |            12.3 |            13.8 |            -7.3 |    -28.3 |      17.6 | no            |             72.1 |             62.4 |                13.5 |                 59.4 |              -6.1 |             0 |
| scope_churn     |                 6.4 |    3.9 |               39.0 |       119411 |            4 |           100.0 |            18.8 |            18.4 |             4.0 |     -7.7 |      15.9 | no            |             53.9 |             84.2 |               -56.2 |                 26.0 |             -86.9 |             0 |
| shadow_heavy    |                26.7 |    5.0 |               81.5 |        73820 |           93 |            99.9 |            24.3 |            11.2 |            55.1 |     47.0 |      58.5 | yes           |            108.4 |             40.0 |                63.1 |                 70.8 |              77.8 |             0 |
| short_ids       |               200.8 |   64.2 |               68.0 |        43608 |           12 |           100.0 |            17.6 |            11.7 |            29.6 |     20.1 |      42.4 | yes           |             52.7 |             87.8 |               -66.6 |                 38.6 |             -13.1 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        9 |                      6 |                      1 |                    7.9 |     62.0 |  81.5 |                    -30.7 |      26.4 |   96.3 |
| old arena table           |        9 |                      8 |                      0 |                   10.9 |     95.3 |  99.8 |                      0.4 |      60.9 |   99.3 |
| old scope maps            |        9 |                      8 |                      0 |                   10.9 |     59.9 |  88.8 |                      6.7 |      56.4 |   89.7 |
| map per scope             |        9 |                      6 |                      0 |                   -9.7 |     42.8 |  87.3 |                     -9.7 |      56.6 |   89.5 |
| std map + undo log        |        9 |                      5 |                      1 |                   -1.4 |     48.8 |  64.4 |                    -17.2 |      16.4 |   28.4 |
| Swiss node map + undo log |        9 |                      2 |                      4 |                   -1.3 |     39.2 |  59.8 |                    -58.6 |      -4.9 |   13.0 |
| Swiss flat map, interned  |        9 |                      1 |                      4 |                  -12.5 |     58.2 |  94.0 |                   -183.5 |     -26.6 |   10.7 |

## D. Worst-case clustering

### STRATA lookup cost when every key is forced into one probe cluster

Best of 7 rounds, batch-timed. With all keys in one cluster a lookup scans the cluster: cost grows linearly.

|   live_names | hash                 |   ns_per_lookup_hit |   ns_per_lookup_miss |   ns_per_declare |
|-------------:|:---------------------|--------------------:|---------------------:|-----------------:|
|           16 | normal               |                 9.3 |                  8.5 |            107.1 |
|           16 | all_keys_one_cluster |                11.5 |                 16.8 |            129.8 |
|           64 | normal               |                10.9 |                  9.3 |            102.7 |
|           64 | all_keys_one_cluster |                31.9 |                 62.9 |            197.7 |
|          256 | normal               |                12.1 |                  9.9 |             85.3 |
|          256 | all_keys_one_cluster |               115.3 |                218.0 |            352.3 |
|         1024 | normal               |                12.7 |                 10.2 |             73.7 |
|         1024 | all_keys_one_cluster |               456.2 |                821.9 |           1514.5 |
|         4096 | normal               |                14.5 |                 20.0 |             60.1 |
|         4096 | all_keys_one_cluster |              1743.9 |               3230.3 |           4607.2 |

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
| ESP-IDF  |   7480.9 |               8415.6 |               7480.9 |                  7480.9 |              15375.5 |             nan   |          19841.8 |         13985.2 |              18289.1 |                     18105.5 |                    41419.9 |
| FreeRTOS |    292.0 |                292.0 |                292.0 |                   292.0 |                937.9 |            1158.9 |            758.3 |           534.9 |                651.2 |                       550.3 |                     1230.7 |
| Zephyr   |   1870.3 |               1870.3 |               2216.7 |                  1870.3 |               7572.0 |             nan   |           5792.1 |          4154.9 |               5211.4 |                      4474.0 |                    19054.7 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.1 |                 43.1 |                 43.1 |                    43.1 |                129.5 |             114.7 |            111.3 |            77.6 |                 96.4 |                        81.5 |                      174.5 |
| ESP-IDF  |     49.9 |                 56.1 |                 49.9 |                    49.9 |                102.6 |             nan   |            132.3 |            93.3 |                122.0 |                       120.8 |                      276.3 |
| FreeRTOS |     46.6 |                 46.6 |                 46.6 |                    46.6 |                149.8 |             185.0 |            121.1 |            85.4 |                104.0 |                        87.9 |                      196.5 |
| Zephyr   |     41.7 |                 41.7 |                 49.4 |                    41.7 |                168.8 |             nan   |            129.1 |            92.6 |                116.2 |                        99.7 |                      424.8 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     16.0 |                 16.0 |                 16.0 |                    16.0 |              19804.0 |           26299.0 |          35323.0 |         43882.0 |              39468.0 |                     29565.0 |                     3385.0 |
| ESP-IDF  |     24.0 |                 27.0 |                 24.0 |                    24.0 |             629511.0 |             nan   |        1032063.0 |       1342739.0 |            1225740.0 |                    860749.0 |                   168333.0 |
| FreeRTOS |     16.0 |                 16.0 |                 16.0 |                    16.0 |              32473.0 |           50714.0 |          53727.0 |        115265.0 |             108616.0 |                     41135.0 |                     4786.0 |
| Zephyr   |     25.0 |                 25.0 |                 21.0 |                    25.0 |             664319.0 |             nan   |        1056367.0 |       1116929.0 |             974653.0 |                    870284.0 |                   147498.0 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `legacy_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     49.6 |                 46.2 |                 46.8 |                    43.2 |                 55.2 |             695.7 |             80.6 |            66.6 |                 60.6 |                        56.8 |                       38.7 |
| ESP-IDF  |     56.5 |                 56.4 |                 59.5 |                    52.7 |                 96.4 |             nan   |            171.2 |           169.8 |                174.3 |                       122.4 |                       92.1 |
| FreeRTOS |     44.0 |                 56.1 |                 55.7 |                    43.3 |                 55.1 |             599.3 |             67.8 |            67.9 |                 48.4 |                        38.0 |                       32.4 |
| Zephyr   |     50.4 |                 45.2 |                 47.6 |                    44.4 |                 70.6 |             nan   |            131.7 |           121.7 |                 84.7 |                        71.8 |                       61.0 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     55.7 |                 61.2 |                 55.1 |                    50.3 |                 53.3 |              71.5 |            123.5 |           133.8 |                 53.9 |                        50.9 |                       50.9 |
| ESP-IDF  |     73.3 |                 72.1 |                 83.0 |                    72.7 |                 78.1 |             nan   |            201.1 |           158.1 |                 93.3 |                        75.1 |                       75.7 |
| FreeRTOS |     72.7 |                 93.3 |                106.6 |                    56.9 |                128.4 |             121.1 |            140.5 |           133.2 |                 91.4 |                        90.2 |                       53.9 |
| Zephyr   |     67.8 |                 62.4 |                 76.9 |                    66.6 |                 83.0 |             nan   |            279.2 |           287.7 |                 86.0 |                        85.4 |                       82.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     89.6 |                104.2 |                 90.8 |                    82.4 |                188.3 |            8272.0 |            172.0 |           189.6 |                166.5 |                       132.0 |                      114.5 |
| ESP-IDF  |    169.0 |                181.1 |                173.8 |                   178.7 |                393.6 |             nan   |            705.5 |           724.9 |                760.7 |                       370.0 |                      395.5 |
| FreeRTOS |    106.0 |                130.8 |                156.9 |                    98.1 |                292.5 |            6827.6 |            195.0 |           169.0 |                209.5 |                       174.4 |                      107.2 |
| Zephyr   |    146.0 |                158.1 |                163.5 |                   147.2 |                333.1 |             nan   |            407.0 |           368.2 |                559.6 |                       322.8 |                      357.3 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |    310.7 |                357.3 |                310.7 |                   259.2 |                259.2 |             721.9 |            196.8 |           190.2 |                499.6 |                       443.3 |                       26.6 |
| ESP-IDF  |    310.1 |                320.4 |                332.5 |                   261.6 |                287.7 |             nan   |            255.0 |           202.9 |                512.3 |                       447.5 |                       26.0 |
| FreeRTOS |    210.1 |                241.0 |                285.8 |                   148.4 |                244.1 |             715.2 |            172.6 |           139.9 |                358.5 |                       346.4 |                       20.6 |
| Zephyr   |    303.4 |                307.0 |                315.5 |                   272.5 |                258.0 |             nan   |            263.4 |           236.2 |                543.2 |                       484.5 |                       32.7 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| Arduino  |               876.9 |  292.0 |               66.7 |        19804 |           16 |            99.9 |             5.2 |             4.7 |            18.8 |     -2.8 |      50.2 | no            |             53.3 |             55.7 |                -4.5 |                 52.4 |             -19.9 |             0 |
| ESP-IDF  |             15375.5 | 7480.9 |               51.3 |       629511 |           24 |           100.0 |           214.9 |           126.0 |            38.8 |     32.5 |      50.4 | yes           |             78.1 |             73.3 |                 6.1 |                 57.1 |              -7.8 |             0 |
| FreeRTOS |               937.9 |  292.0 |               68.9 |        32473 |           16 |           100.0 |            12.5 |            10.0 |            21.7 |    -32.7 |      32.9 | no            |            128.4 |             72.7 |                43.4 |                 63.8 |              13.9 |             0 |
| Zephyr   |              7572.0 | 1870.3 |               75.3 |       664319 |           25 |           100.0 |           183.9 |           131.4 |            30.5 |     16.6 |      36.4 | yes           |             83.0 |             67.8 |                18.3 |                 56.2 |             -17.6 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                  |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| METIS-X (previous)        |        4 |                      2 |                      0 |                   51.3 |     67.8 |  75.3 |                     18.8 |      26.1 |   38.8 |
| old arena table           |        2 |                      2 |                      0 |                   62.4 |     68.6 |  74.8 |                     92.4 |      92.9 |   93.3 |
| old scope maps            |        4 |                      4 |                      0 |                   61.3 |     61.9 |  67.7 |                     34.0 |      49.3 |   66.9 |
| map per scope             |        4 |                      4 |                      0 |                   44.4 |     46.0 |  55.0 |                     25.5 |      51.0 |   64.7 |
| std map + undo log        |        4 |                      3 |                      0 |                   55.2 |     57.2 |  64.1 |                     -0.5 |      32.9 |   65.9 |
| Swiss node map + undo log |        4 |                      3 |                      0 |                   46.9 |     52.6 |  58.7 |                    -14.8 |      28.4 |   53.7 |
| Swiss flat map, interned  |        4 |                      2 |                      2 |                   75.3 |     79.1 |  90.2 |                    -36.6 |      -2.7 |   37.5 |

