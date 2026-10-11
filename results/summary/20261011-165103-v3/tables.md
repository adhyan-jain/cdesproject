# Result tables for run `20261011-165103-v3`

```
run: results/raw/20261011-165103-v3
date_utc: 2026-10-11T16:51:36Z
git_commit: 8786eacda9f4dbd1d9ba48c7495aa40b5a1bd4f4
compiler: g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
flags: -std=c++14 -O2
kernel: Linux 6.18.33.2-microsoft-standard-WSL2
cpu: Intel(R) Core(TM) Ultra 7 258V
libc: ldd (Ubuntu GLIBC 2.35-0ubuntu3.15) 2.35
pinning: taskset -c 2
repetitions: 31 (+2 warm-up) whole-trace replays; 3 per-operation latency replays
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

96 table/trace pairs were checked against the reference model; 96 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     42.8 |                 42.8 |                 42.8 |                    42.8 |                              42.8 |                102.7 |              95.0 |            105.6 |            72.0 |                116.0 |                       110.0 |                      140.4 |
| freertos |     57.8 |                 57.8 |                 57.8 |                    57.8 |                              57.7 |                217.3 |             135.8 |            166.1 |           116.0 |                147.3 |                       128.8 |                      293.0 |
| littlefs |     25.8 |                 25.8 |                 25.8 |                    25.8 |                              25.7 |                106.9 |              68.4 |             77.0 |            54.1 |                 67.8 |                        57.1 |                      141.9 |
| lua      |     64.2 |                 64.2 |                 64.2 |                    96.2 |                              96.2 |                106.8 |              87.5 |            140.2 |            96.7 |                127.7 |                       114.7 |                      142.3 |
| mbedtls  |    144.3 |                144.3 |                144.3 |                   144.3 |                             144.2 |                234.4 |             234.4 |            270.0 |           189.4 |                277.7 |                       269.3 |                      310.9 |
| sqlite   |    194.7 |                194.7 |                194.7 |                   194.7 |                             194.7 |                451.0 |             455.4 |            474.8 |           332.9 |                513.4 |                       494.0 |                     1125.6 |
| tinycc   |    324.5 |                324.5 |                324.5 |                   324.5 |                             324.4 |                423.1 |             545.3 |            585.6 |           424.5 |                550.9 |                       449.6 |                      575.6 |
| zlib     |     17.2 |                 17.2 |                 17.2 |                    25.8 |                              25.7 |                 52.7 |              43.9 |             61.4 |            44.4 |                 60.3 |                        55.0 |                       71.1 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     41.1 |                 41.1 |                 41.1 |                    41.1 |                              41.0 |                 98.5 |              91.1 |            101.3 |            69.1 |                111.4 |                       105.6 |                      134.8 |
| freertos |     39.3 |                 39.3 |                 39.3 |                    39.3 |                              39.3 |                147.9 |              92.4 |            113.0 |            79.0 |                100.2 |                        87.6 |                      199.4 |
| littlefs |     36.0 |                 36.0 |                 36.0 |                    36.0 |                              35.9 |                149.6 |              95.7 |            107.8 |            75.7 |                 94.9 |                        79.9 |                      198.5 |
| lua      |     48.2 |                 48.2 |                 48.2 |                    72.2 |                              72.1 |                 80.1 |              65.6 |            105.2 |            72.5 |                 95.8 |                        86.1 |                      106.7 |
| mbedtls  |     64.2 |                 64.2 |                 64.2 |                    64.2 |                              64.1 |                104.3 |             104.3 |            120.1 |            84.2 |                123.5 |                       119.8 |                      138.3 |
| sqlite   |     47.0 |                 47.0 |                 47.0 |                    47.0 |                              47.0 |                108.8 |             109.9 |            114.5 |            80.3 |                123.9 |                       119.2 |                      271.5 |
| tinycc   |     60.3 |                 60.3 |                 60.3 |                    60.3 |                              60.3 |                 78.6 |             101.4 |            108.8 |            78.9 |                102.4 |                        83.6 |                      107.0 |
| zlib     |     30.9 |                 30.9 |                 30.9 |                    46.2 |                              46.1 |                 94.4 |              78.8 |            110.1 |            79.6 |                108.1 |                        98.7 |                      127.6 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |       22 |                   22 |                   22 |                      22 |                                22 |                 3604 |              4182 |             7341 |            7341 |                 5571 |                        5567 |                        344 |
| freertos |       81 |                   85 |                   81 |                      85 |                                86 |                 8282 |             10541 |            14903 |           14903 |                12444 |                       12474 |                       2051 |
| littlefs |       19 |                   19 |                   19 |                      19 |                                19 |                 2774 |              3192 |             5195 |            5195 |                 4051 |                        4055 |                        246 |
| lua      |      336 |                  341 |                  336 |                     350 |                               349 |                40494 |             46774 |            77971 |           77971 |                62526 |                       62639 |                       4408 |
| mbedtls  |     1154 |                 1164 |                 1154 |                    1190 |                              1203 |               255849 |            348278 |           466271 |          466271 |               390914 |                      391205 |                      71187 |
| sqlite   |       15 |                   15 |                   15 |                      15 |                                15 |                22711 |             35259 |            39130 |           39130 |                29283 |                       29285 |                       2227 |
| tinycc   |       15 |                   15 |                   15 |                      15 |                                15 |                 9665 |             10380 |            18835 |           18835 |                14825 |                       14685 |                       1057 |
| zlib     |      133 |                  133 |                  133 |                     141 |                               141 |                10412 |             14127 |            21446 |           21446 |                17657 |                       17710 |                       1532 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `compiler_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     53.4 |                 48.8 |                 49.7 |                    43.8 |                              33.1 |                 49.7 |             154.0 |             70.7 |            60.8 |                 55.0 |                        53.2 |                       39.6 |
| freertos |     42.9 |                 45.0 |                 41.3 |                    35.5 |                              33.1 |                 48.6 |             108.3 |             58.1 |            52.6 |                 43.0 |                        46.6 |                       35.1 |
| littlefs |     44.2 |                 44.7 |                 43.2 |                    36.3 |                              32.0 |                 49.5 |              82.5 |             76.3 |            69.3 |                 49.5 |                        44.5 |                       36.6 |
| lua      |     43.5 |                 43.6 |                 44.2 |                    38.3 |                              33.0 |                 47.6 |             120.2 |             56.6 |            51.2 |                 46.0 |                        46.4 |                       32.3 |
| mbedtls  |     45.5 |                 46.2 |                 44.8 |                    39.9 |                              35.4 |                 55.6 |             153.5 |             62.6 |            51.1 |                 49.6 |                        52.8 |                       38.1 |
| sqlite   |     29.0 |                 29.4 |                 29.7 |                    28.5 |                              28.9 |                 32.7 |              82.7 |             60.1 |            60.3 |                 29.4 |                        30.6 |                       25.0 |
| tinycc   |     33.0 |                 36.8 |                 32.9 |                    28.8 |                              26.5 |                 35.0 |             263.6 |             61.1 |            60.1 |                 33.3 |                        31.5 |                       26.4 |
| zlib     |     33.7 |                 34.9 |                 33.3 |                    30.0 |                              29.3 |                 37.5 |              84.6 |             51.7 |            49.8 |                 39.8 |                        40.1 |                       28.7 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     68.4 |                 61.7 |                 67.8 |                    63.5 |                              56.3 |                 64.7 |              76.2 |            156.1 |           164.6 |                 95.0 |                        57.5 |                       56.9 |
| freertos |     53.2 |                 52.6 |                 53.8 |                    49.0 |                              47.8 |                 59.3 |              59.9 |            122.2 |           127.1 |                 61.1 |                        50.8 |                       49.0 |
| littlefs |     59.9 |                 56.3 |                 62.9 |                    53.2 |                              44.8 |                 58.1 |              58.7 |            170.6 |           181.5 |                 73.2 |                        53.2 |                       52.6 |
| lua      |     65.4 |                 50.3 |                 49.1 |                    45.4 |                              44.8 |                 52.1 |              59.4 |            113.3 |           110.2 |                 66.6 |                        51.5 |                       55.1 |
| mbedtls  |     60.2 |                 68.7 |                 71.1 |                    55.3 |                              74.8 |                 83.9 |              75.4 |            119.2 |           109.5 |                104.6 |                        66.3 |                       66.9 |
| sqlite   |     50.9 |                 49.1 |                 50.9 |                    49.7 |                              50.9 |                 63.0 |              63.0 |            153.9 |           164.2 |                 54.5 |                        61.8 |                       83.6 |
| tinycc   |     52.7 |                 52.7 |                 52.1 |                    44.2 |                              90.9 |                 50.9 |              53.9 |            138.7 |           278.7 |                 52.1 |                        46.6 |                       53.3 |
| zlib     |     44.7 |                 44.1 |                 41.7 |                    39.9 |                              41.1 |                 44.7 |              50.8 |            105.2 |           104.6 |                 49.6 |                        42.9 |                       86.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |    104.1 |                 95.0 |                 98.0 |                    88.9 |                              71.4 |                197.2 |            1623.3 |            184.5 |           141.6 |                169.4 |                       134.9 |                      112.5 |
| freertos |     80.5 |                 76.2 |                 79.9 |                    68.4 |                              79.9 |                187.0 |            1058.2 |            160.3 |           122.8 |                124.0 |                       113.7 |                       92.0 |
| littlefs |     86.5 |                 91.4 |                 91.4 |                    73.2 |                              60.5 |                233.5 |             877.9 |            176.1 |           131.9 |                159.7 |                       120.4 |                       85.9 |
| lua      |     87.8 |                 71.5 |                 73.3 |                    61.8 |                              72.1 |                156.9 |            1040.0 |            139.9 |           106.0 |                131.4 |                       115.1 |                       95.7 |
| mbedtls  |     85.7 |                 91.2 |                 94.9 |                    71.1 |                              88.8 |                238.4 |            1427.2 |            173.3 |           126.5 |                191.6 |                       147.8 |                      132.6 |
| sqlite   |     79.4 |                 73.9 |                 76.4 |                    70.3 |                              85.4 |                180.6 |            3427.5 |            144.2 |           129.7 |                120.0 |                       109.1 |                      157.0 |
| tinycc   |     82.4 |                 78.1 |                 79.4 |                    63.0 |                             101.8 |                183.6 |            6428.2 |            142.4 |           220.5 |                113.9 |                       114.5 |                       84.8 |
| zlib     |     67.7 |                 62.9 |                 63.5 |                    53.2 |                              68.9 |                143.8 |             617.1 |            137.8 |           105.8 |                113.0 |                       103.3 |                      124.5 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (18 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| cjson    |     13.9 |                 12.7 |                 12.1 |                    12.7 |                              21.8 |                 82.9 |             217.8 |             61.1 |            53.2 |                173.0 |                       160.3 |                       10.9 |
| freertos |     20.0 |                 20.0 |                 20.0 |                    19.4 |                              26.6 |                 88.3 |             233.5 |             82.3 |            65.9 |                153.1 |                       153.1 |                       16.9 |
| littlefs |     16.9 |                 16.9 |                 15.7 |                    16.9 |                              23.0 |                144.0 |             274.7 |             78.0 |            63.5 |                193.0 |                       177.3 |                       13.9 |
| lua      |     26.7 |                 20.0 |                 19.4 |                    19.4 |                              26.0 |                 80.6 |             206.6 |             69.1 |            54.5 |                170.2 |                       162.9 |                       18.2 |
| mbedtls  |     28.0 |                 31.0 |                 29.8 |                    26.1 |                              40.1 |                148.4 |             301.0 |            108.2 |            76.6 |                324.7 |                       266.3 |                       18.9 |
| sqlite   |     23.0 |                 23.0 |                 23.0 |                    23.0 |                              28.5 |                 75.8 |             229.1 |             68.5 |            61.2 |                146.0 |                       141.8 |                       30.9 |
| tinycc   |     21.2 |                 20.6 |                 20.0 |                    20.0 |                              37.0 |                 74.5 |             172.0 |             59.4 |           104.8 |                133.3 |                       115.1 |                       15.8 |
| zlib     |     16.9 |                 17.5 |                 15.1 |                    15.7 |                              22.4 |                 61.0 |             223.0 |             61.0 |            47.7 |                140.8 |                       137.2 |                       30.8 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |   new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| cjson    |               102.7 |  42.8 |               58.3 |         3604 |           22 |            99.4 |             1.0 |             1.1 |            -6.0 |    -20.8 |      -1.0 | yes           |             64.7 |             68.4 |                -5.7 |                 47.2 |              83.2 |             0 |
| freertos |               217.3 |  57.8 |               73.4 |         8282 |           81 |            99.0 |             1.8 |             1.6 |            14.4 |     10.2 |      18.3 | yes           |             59.3 |             53.2 |                10.3 |                 57.0 |              77.3 |             0 |
| littlefs |               106.9 |  25.8 |               75.9 |         2774 |           19 |            99.3 |             1.0 |             0.9 |            11.2 |      7.1 |      18.5 | yes           |             58.1 |             59.9 |                -3.1 |                 63.0 |              88.3 |             0 |
| lua      |               106.8 |  64.2 |               39.9 |        40494 |          336 |            99.2 |             9.0 |             8.2 |             8.8 |      3.0 |      14.6 | yes           |             52.1 |             65.4 |               -25.5 |                 44.0 |              66.9 |             0 |
| mbedtls  |               234.4 | 144.3 |               38.5 |       255849 |         1154 |            99.5 |            54.6 |            44.8 |            18.6 |     16.4 |      21.1 | yes           |             83.9 |             60.2 |                28.2 |                 64.1 |              81.1 |             0 |
| sqlite   |               451.0 | 194.7 |               56.8 |        22711 |           15 |            99.9 |             8.8 |             7.8 |            10.7 |      4.5 |      17.7 | yes           |             63.0 |             50.9 |                19.2 |                 56.0 |              69.7 |             0 |
| tinycc   |               423.1 | 324.5 |               23.3 |         9665 |           15 |            99.8 |             3.1 |             2.9 |             5.4 |      2.1 |      13.3 | yes           |             50.9 |             52.7 |                -3.5 |                 55.1 |              71.5 |             0 |
| zlib     |                52.7 |  17.2 |               67.3 |        10412 |          133 |            98.7 |             2.2 |             2.0 |            10.7 |      3.8 |      14.9 | yes           |             44.7 |             44.7 |                 0.0 |                 52.9 |              72.3 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                        |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| arena + chains (allocator-free) |        8 |                      0 |                      7 |                   -0.2 |     -0.0 |  33.2 |                    -63.4 |     -29.5 |   -2.9 |
| METIS-X (previous)              |        8 |                      7 |                      1 |                   23.3 |     57.6 |  75.9 |                     -6.0 |      10.7 |   18.6 |
| old arena table                 |        8 |                      8 |                      0 |                   26.6 |     56.1 |  62.4 |                     45.7 |      63.7 |   87.1 |
| old scope maps                  |        8 |                      8 |                      0 |                   44.6 |     59.2 |  72.0 |                     22.5 |      30.6 |   52.1 |
| map per scope                   |        8 |                      8 |                      0 |                   23.6 |     41.0 |  61.2 |                      9.9 |      24.0 |   50.2 |
| std map + undo log              |        8 |                      4 |                      0 |                   41.1 |     61.4 |  71.5 |                     -0.8 |       3.4 |   13.3 |
| Swiss node map + undo log       |        8 |                      4 |                      0 |                   27.8 |     55.0 |  68.7 |                     -5.8 |       5.2 |   13.0 |
| Swiss flat map, interned        |        8 |                      0 |                      8 |                   43.6 |     72.7 |  82.7 |                    -33.1 |     -21.5 |  -11.3 |

## B. Fixed-buffer mode

### Smallest fixed buffer that replays the whole trace without a refused operation

Found by bisection to 64 bytes. The baselines have no fixed-memory mode; the comparison is with their peak heap.

| trace    |   min buffer KiB (packed) |   min buffer KiB (raw) |   min buffer KiB (sparse index) |   packing saves % |   bytes per live decl |   arena + chains min buffer KiB |   vs arena + chains, red. % |   vs METIS-X (previous) peak heap, red. % |   vs map per scope peak heap, red. % |   vs std map + undo log peak heap, red. % |   vs Swiss flat map, interned peak heap, red. % |
|:---------|--------------------------:|-----------------------:|--------------------------------:|------------------:|----------------------:|--------------------------------:|----------------------------:|------------------------------------------:|-------------------------------------:|------------------------------------------:|------------------------------------------------:|
| cjson    |                      30.0 |                   31.8 |                            38.0 |               5.5 |                  28.8 |                            35.9 |                        16.4 |                                      70.8 |                                 58.3 |                                      74.1 |                                            78.6 |
| freertos |                      44.0 |                   47.8 |                            52.0 |               7.9 |                  29.9 |                            53.6 |                        17.9 |                                      79.8 |                                 62.1 |                                      70.1 |                                            85.0 |
| littlefs |                      20.0 |                   21.5 |                            24.0 |               7.0 |                  28.0 |                            24.2 |                        17.5 |                                      81.3 |                                 63.0 |                                      70.5 |                                            85.9 |
| lua      |                      35.9 |                   38.1 |                            43.9 |               5.7 |                  27.0 |                            43.4 |                        17.3 |                                      66.3 |                                 62.8 |                                      71.8 |                                            74.7 |
| mbedtls  |                      80.0 |                   87.9 |                            96.0 |               9.0 |                  35.6 |                            96.9 |                        17.4 |                                      65.9 |                                 57.8 |                                      71.2 |                                            74.3 |
| sqlite   |                     140.4 |                  152.9 |                           172.4 |               8.2 |                  33.9 |                           169.4 |                        17.2 |                                      68.9 |                                 57.8 |                                      72.7 |                                            87.5 |
| tinycc   |                     156.5 |                  168.3 |                           188.5 |               7.0 |                  29.1 |                           189.8 |                        17.5 |                                      63.0 |                                 63.1 |                                      71.6 |                                            72.8 |
| zlib     |                      15.8 |                   16.7 |                            19.8 |               5.6 |                  28.2 |                            18.9 |                        16.6 |                                      70.1 |                                 64.5 |                                      73.9 |                                            77.9 |

### Replay time (ms) with a buffer of 1x, 1.25x, 2x and 4x the minimum

Median of 9 replays. Blank: that size was refused (sizing is not perfectly monotonic).

| trace    |   1.00x |   1.25x |   2.00x |   4.00x |
|:---------|--------:|--------:|--------:|--------:|
| cjson    |     0.6 |     0.6 |     0.6 |     0.6 |
| freertos |     1.7 |     1.7 |     1.7 |     1.6 |
| littlefs |     0.5 |     0.6 |     0.5 |     0.5 |
| lua      |     6.2 |     6.5 |     6.1 |     6.4 |
| mbedtls  |    37.7 |    40.1 |    36.6 |    36.2 |
| sqlite   |     7.2 |     6.7 |     7.2 |     6.6 |
| tinycc   |     2.5 |     2.5 |     2.5 |     2.5 |
| zlib     |     1.5 |     1.6 |     1.4 |     1.4 |

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

108 table/trace pairs were checked against the reference model; 107 had no wrong or refused result.

| trace           | impl    |   wrong_lookups |   wrong_declares |   refused_declares |
|:----------------|:--------|----------------:|-----------------:|-------------------:|
| deep_shadow_400 | metis_x |             298 |                0 |                149 |

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |    486.6 |                486.6 |                486.6 |                   486.6 |                             486.6 |                868.2 |            6289.0 |           1023.8 |           708.1 |                972.4 |                       926.7 |                     1164.5 |
| deep_nesting    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                              25.7 |                 57.1 |            2974.5 |             92.6 |            71.2 |                 61.0 |                        54.0 |                      264.2 |
| deep_shadow_400 |     11.5 |                 11.5 |                 11.5 |                    11.5 |                              11.5 |                 40.1 |              34.7 |            103.1 |            90.6 |                 13.3 |                        13.2 |                       10.2 |
| dense_50k       |   2462.9 |               2462.9 |               2462.9 |                  2462.9 |                            2462.9 |               6972.3 |            2763.1 |           5351.5 |          3788.7 |               4812.7 |                      4047.6 |                     4671.2 |
| long_ids        |    216.4 |                216.4 |                216.4 |                   216.4 |                             216.3 |                297.1 |           10427.1 |            307.4 |           249.4 |                269.8 |                       270.3 |                      381.1 |
| lookup_heavy    |     25.8 |                 25.8 |                 25.8 |                    25.8 |                              25.7 |                 53.7 |             551.3 |             64.3 |            45.0 |                 59.6 |                        53.9 |                      261.0 |
| scope_churn     |      3.9 |                  3.9 |                  3.9 |                     3.9 |                               3.8 |                  6.4 |            2089.8 |              5.5 |             3.7 |                  4.6 |                         4.9 |                       64.4 |
| shadow_heavy    |      4.9 |                  5.2 |                  5.2 |                     5.5 |                               7.7 |                 26.7 |            1807.3 |             29.0 |            21.3 |                  7.9 |                         7.6 |                        6.3 |
| short_ids       |     64.2 |                 64.2 |                 64.2 |                    64.2 |                              64.1 |                200.8 |             599.4 |            189.0 |           127.9 |                151.4 |                       153.5 |                      260.2 |

### Peak heap bytes per live declaration (at the peak)

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     49.3 |                 49.3 |                 49.3 |                    49.3 |                              49.3 |                 88.0 |             637.6 |            103.8 |            71.8 |                 98.6 |                        94.0 |                      118.1 |
| deep_nesting    |     38.4 |                 38.4 |                 38.4 |                    38.4 |                              38.3 |                 85.3 |            4440.1 |            138.3 |           106.3 |                 91.1 |                        80.7 |                      394.4 |
| deep_shadow_400 |     29.5 |                 29.5 |                 29.5 |                    29.5 |                              29.3 |                102.5 |              88.9 |            263.9 |           231.8 |                 34.0 |                        33.8 |                       26.2 |
| dense_50k       |     50.4 |                 50.4 |                 50.4 |                    50.4 |                              50.4 |                142.8 |              56.6 |            109.6 |            77.6 |                 98.6 |                        82.9 |                       95.7 |
| long_ids        |    118.9 |                118.9 |                118.9 |                   118.9 |                             118.9 |                163.3 |            5731.3 |            168.9 |           137.1 |                148.3 |                       148.6 |                      209.5 |
| lookup_heavy    |     42.9 |                 42.9 |                 42.9 |                    42.9 |                              42.8 |                 89.3 |             917.9 |            107.0 |            75.0 |                 99.2 |                        89.8 |                      434.6 |
| scope_churn     |     72.3 |                 72.3 |                 72.3 |                    72.3 |                              71.1 |                118.5 |           38908.1 |            101.7 |            69.1 |                 85.7 |                        91.3 |                     1198.3 |
| shadow_heavy    |     20.5 |                 21.6 |                 21.6 |                    22.9 |                              31.7 |                110.8 |            7492.8 |            120.1 |            88.2 |                 32.8 |                        31.6 |                       26.0 |
| short_ids       |     33.6 |                 33.6 |                 33.6 |                    33.6 |                              33.6 |                105.2 |             314.0 |             99.0 |            67.0 |                 79.3 |                        80.4 |                      136.3 |

### Allocator calls during the whole replay

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |       17 |                   17 |                   17 |                      17 |                                17 |               104082 |            158610 |           263707 |          263707 |               263527 |                      263531 |                       3216 |
| deep_nesting    |       10 |                   10 |                   10 |                      10 |                                10 |               103095 |             88211 |           127642 |          127741 |                97714 |                       85889 |                        304 |
| deep_shadow_400 |       10 |                   10 |                    8 |                      10 |                                 8 |                  268 |               449 |              811 |             811 |                  422 |                          23 |                         23 |
| dense_50k       |       21 |                   21 |                   21 |                      21 |                                21 |                26613 |             38253 |            66587 |           66587 |                66603 |                       66606 |                      16623 |
| long_ids        |       14 |                   15 |                   14 |                      14 |                                15 |               130673 |            268615 |           188471 |          194169 |               179824 |                       73138 |                       2042 |
| lookup_heavy    |       10 |                   10 |                   10 |                      10 |                                10 |                16720 |             14381 |            21175 |           21256 |                16372 |                       14624 |                        293 |
| scope_churn     |        4 |                    4 |                    4 |                       4 |                                 4 |               119411 |            119442 |           179448 |          180056 |               150062 |                      134420 |                         29 |
| shadow_heavy    |       16 |                   16 |                    6 |                      19 |                                 7 |                73820 |             73856 |           138261 |          160027 |               134922 |                         187 |                         28 |
| short_ids       |       12 |                   12 |                   12 |                      12 |                                12 |                43608 |             43648 |           100737 |          104041 |                89672 |                       32801 |                         42 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `synthetic_replay_time.csv`.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     50.4 |                 50.3 |                 49.7 |                    41.3 |                              75.2 |                 97.4 |            9132.6 |            170.6 |           142.4 |                133.2 |                       101.6 |                       50.9 |
| deep_nesting    |     41.6 |                 38.6 |                 42.1 |                    38.9 |                              45.6 |                 62.5 |              82.8 |            460.7 |           465.0 |                 54.9 |                        51.1 |                       34.4 |
| deep_shadow_400 |     12.5 |                 16.6 |                  8.6 |                     8.8 |                              17.0 |                226.4 |             278.4 |             23.6 |            21.9 |                 12.2 |                         9.6 |                        9.4 |
| dense_50k       |     85.2 |                101.4 |                 84.8 |                    82.5 |                              67.4 |                 89.6 |           10010.6 |            103.7 |            88.3 |                 86.9 |                        71.7 |                       62.3 |
| long_ids        |     79.8 |                 69.9 |                 80.8 |                    77.2 |                              72.3 |                134.3 |             196.2 |            171.5 |           156.0 |                 77.3 |                        59.9 |                       45.7 |
| lookup_heavy    |     42.6 |                 42.1 |                 41.1 |                    36.3 |                              37.0 |                 40.9 |              42.4 |            104.5 |           101.2 |                 42.0 |                        35.1 |                       35.3 |
| scope_churn     |     37.1 |                 37.8 |                 36.2 |                    36.7 |                              49.0 |                 51.1 |              77.6 |             54.4 |            49.4 |                 66.6 |                        46.8 |                       29.3 |
| shadow_heavy    |     35.6 |                 36.4 |                 35.3 |                    32.5 |                              41.6 |                 73.4 |              99.0 |             84.8 |            77.9 |                 44.0 |                        33.6 |                       33.5 |
| short_ids       |     36.3 |                 39.8 |                 35.7 |                    33.5 |                              39.7 |                 52.8 |             124.8 |            103.7 |            99.0 |                 50.1 |                        37.6 |                       30.1 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |      0.0 |                  0.0 |                  0.0 |                     0.0 |                               0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| deep_nesting    |     52.1 |                 86.0 |                 53.3 |                    51.5 |                              64.8 |                 63.0 |              76.9 |           1875.5 |          2481.1 |                 66.0 |                        60.0 |                       60.6 |
| deep_shadow_400 |     18.2 |                 24.3 |                 23.1 |                    18.2 |                              34.0 |                552.2 |             750.1 |             20.0 |            21.8 |                 19.4 |                        24.3 |                       24.3 |
| dense_50k       |    315.5 |                299.2 |                329.5 |                   189.3 |                             211.2 |                309.5 |             219.7 |            350.1 |           203.3 |                283.4 |                       272.5 |                      255.5 |
| long_ids        |    116.9 |                125.3 |                 97.5 |                    90.2 |                             121.7 |                148.4 |             215.0 |            358.5 |           365.1 |                 87.8 |                       103.5 |                       74.5 |
| lookup_heavy    |     76.9 |                 52.7 |                 54.5 |                    60.6 |                              56.3 |                 59.3 |              62.4 |            186.5 |           187.1 |                 69.6 |                        48.4 |                       61.2 |
| scope_churn     |     49.1 |                 50.9 |                 49.1 |                    49.1 |                              47.3 |                 61.8 |              66.1 |            149.1 |            95.7 |                 70.3 |                        46.1 |                       48.5 |
| shadow_heavy    |     38.2 |                 39.4 |                 38.8 |                    37.6 |                              37.0 |                100.6 |             115.7 |            250.3 |           256.3 |                 44.2 |                        36.4 |                       43.0 |
| short_ids       |     49.1 |                 56.3 |                 42.4 |                    43.0 |                              56.3 |                 53.3 |              88.5 |            256.3 |           230.2 |                 64.8 |                        52.1 |                       59.4 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |     70.8 |                 77.5 |                 74.5 |                    59.9 |                              87.2 |                176.2 |           17137.7 |            184.7 |           158.6 |                147.1 |                       117.5 |                       76.9 |
| deep_nesting    |     67.2 |                106.0 |                 69.0 |                    62.4 |                             101.1 |                187.7 |             188.3 |            139.9 |           139.9 |                101.7 |                        98.1 |                       72.1 |
| deep_shadow_400 |     20.6 |                 26.1 |                 25.5 |                    20.0 |                              46.7 |                568.6 |             335.6 |            109.2 |            94.7 |                 36.4 |                        35.8 |                       38.2 |
| dense_50k       |    122.6 |                158.4 |                117.7 |                    81.3 |                             149.9 |                237.9 |           97449.7 |            274.9 |           195.4 |                226.3 |                       131.1 |                      136.5 |
| long_ids        |    131.4 |                136.2 |                110.2 |                   100.5 |                             153.8 |                274.3 |             517.1 |            204.1 |           167.7 |                142.9 |                       177.4 |                       88.4 |
| lookup_heavy    |    107.2 |                 78.1 |                 80.5 |                    84.8 |                              95.7 |                209.5 |             212.0 |            164.1 |           124.1 |                130.2 |                       101.7 |                      101.1 |
| scope_churn     |     58.8 |                 60.0 |                 58.8 |                    58.8 |                              82.4 |                151.5 |             106.1 |            152.1 |            77.0 |                 98.2 |                        68.5 |                       59.4 |
| shadow_heavy    |     44.2 |                 46.7 |                 44.2 |                    44.2 |                              68.5 |                153.9 |             134.5 |            108.5 |            95.7 |                 70.9 |                        50.9 |                       54.5 |
| short_ids       |     63.0 |                 72.1 |                 54.5 |                    52.7 |                              60.0 |                168.4 |             499.9 |            143.6 |           100.6 |                 97.6 |                        90.3 |                       70.3 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace           |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:----------------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| big_scope_exit  |  16755.0 |              21537.8 |              18323.8 |                 24169.8 |                          134744.4 |             387534.4 |          965422.2 |         693697.1 |        636576.7 |             558523.1 |                    482705.9 |                     8375.1 |
| deep_nesting    |     38.2 |                 50.9 |                 38.8 |                    38.2 |                              47.2 |                190.8 |             434.8 |            145.3 |           141.1 |                287.0 |                       257.4 |                       28.5 |
| deep_shadow_400 |      7.3 |                  7.3 |                 10.3 |                     7.3 |                              11.5 |                114.1 |             376.3 |             21.2 |            21.8 |                  4.2 |                         4.9 |                        3.0 |
| dense_50k       |      0.0 |                  0.0 |                  0.0 |                     0.0 |                               0.0 |                  0.0 |               0.0 |              0.0 |             0.0 |                  0.0 |                         0.0 |                        0.0 |
| long_ids        |    104.2 |                101.7 |                 96.3 |                    93.3 |                             112.6 |                582.5 |            3643.6 |            437.8 |           420.2 |                644.3 |                       855.6 |                       25.4 |
| lookup_heavy    |     50.3 |                 41.2 |                 41.2 |                    46.6 |                              44.8 |                205.3 |             464.5 |            155.6 |           131.4 |                348.2 |                       273.1 |                       29.7 |
| scope_churn     |     29.7 |                 29.7 |                 29.1 |                    29.7 |                              43.6 |                166.7 |             476.3 |            124.8 |            73.3 |                287.9 |                       191.5 |                        5.5 |
| shadow_heavy    |     32.7 |                 33.3 |                 31.5 |                    35.1 |                              53.9 |                170.3 |             595.7 |            145.4 |           127.3 |                 35.1 |                        33.9 |                       24.8 |
| short_ids       |     93.3 |                 96.3 |                 87.9 |                    89.1 |                              85.4 |                327.8 |             841.0 |            239.9 |           182.4 |                410.8 |                       342.3 |                       32.7 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace           |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:----------------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| big_scope_exit  |               868.2 |  486.6 |               44.0 |       104082 |           17 |           100.0 |            19.5 |            10.1 |            49.7 |     45.7 |      51.2 | yes           |              0.0 |              0.0 |               nan   |                 59.8 |              95.7 |             0 |
| deep_nesting    |                57.1 |   25.8 |               54.9 |       103095 |           10 |           100.0 |            18.8 |            12.5 |            32.7 |     27.8 |      36.5 | yes           |             63.0 |             52.1 |                17.3 |                 64.2 |              80.0 |             0 |
| deep_shadow_400 |                40.1 |   11.5 |               71.3 |          268 |           10 |            96.3 |             0.5 |             0.0 |            94.5 |     94.4 |      94.5 | yes           |            552.2 |             18.2 |                96.7 |                 96.4 |              93.6 |           149 |
| dense_50k       |              6972.3 | 2462.9 |               64.7 |        26613 |           21 |            99.9 |            22.4 |            21.3 |             0.7 |     -3.1 |       9.1 | no            |            309.5 |            315.5 |                -1.9 |                 48.5 |             nan   |             0 |
| long_ids        |               297.1 |  216.4 |               27.2 |       130673 |           14 |           100.0 |            40.3 |            24.0 |            39.4 |     35.8 |      42.0 | yes           |            148.4 |            116.9 |                21.2 |                 52.1 |              82.1 |             0 |
| lookup_heavy    |                53.7 |   25.8 |               52.0 |        16720 |           10 |            99.9 |            12.3 |            12.8 |            -2.0 |     -3.5 |       1.8 | no            |             59.3 |             76.9 |               -29.7 |                 48.8 |              75.5 |             0 |
| scope_churn     |                 6.4 |    3.9 |               39.0 |       119411 |            4 |           100.0 |            16.9 |            12.3 |            29.4 |     23.9 |      33.4 | yes           |             61.8 |             49.1 |                20.6 |                 61.2 |              82.2 |             0 |
| shadow_heavy    |                26.7 |    4.9 |               81.5 |        73820 |           16 |           100.0 |            22.0 |            10.7 |            52.2 |     49.5 |      55.4 | yes           |            100.6 |             38.2 |                62.0 |                 71.3 |              80.8 |             0 |
| short_ids       |               200.8 |   64.2 |               68.0 |        43608 |           12 |           100.0 |            15.9 |            10.9 |            29.9 |     27.3 |      33.0 | yes           |             53.3 |             49.1 |                 7.9 |                 62.6 |              71.5 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                        |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| arena + chains (allocator-free) |        9 |                      5 |                      3 |                   -1.6 |     -0.1 |  35.5 |                    -26.8 |       9.5 |   32.1 |
| METIS-X (previous)              |        9 |                      7 |                      0 |                   27.2 |     54.9 |  81.5 |                     -2.0 |      32.7 |   94.5 |
| old arena table                 |        9 |                      8 |                      0 |                   10.9 |     95.3 |  99.8 |                      0.4 |      64.4 |   99.4 |
| old scope maps                  |        9 |                      9 |                      0 |                   28.9 |     59.9 |  88.8 |                     11.4 |      58.0 |   91.2 |
| map per scope                   |        9 |                      8 |                      0 |                   -4.6 |     42.8 |  87.3 |                      2.3 |      53.7 |   90.6 |
| std map + undo log              |        9 |                      5 |                      1 |                   13.3 |     48.8 |  57.8 |                     -3.5 |      18.2 |   61.4 |
| Swiss node map + undo log       |        9 |                      4 |                      4 |                   12.8 |     39.2 |  58.2 |                    -31.8 |      -7.6 |   50.8 |
| Swiss flat map, interned        |        9 |                      0 |                      8 |                  -12.5 |     58.2 |  94.0 |                    -76.3 |     -20.4 |   -3.1 |

## D. Worst-case clustering

### STRATA lookup cost when every key is forced into one probe cluster

Best of 7 rounds, batch-timed. With all keys in one cluster a lookup scans the cluster: cost grows linearly.

|   live_names | hash                 |   ns_per_lookup_hit |   ns_per_lookup_miss |   ns_per_declare |
|-------------:|:---------------------|--------------------:|---------------------:|-----------------:|
|           16 | normal               |                 8.9 |                  8.1 |            130.3 |
|           16 | all_keys_one_cluster |                10.9 |                 15.5 |            144.1 |
|           64 | normal               |                10.1 |                  8.5 |            133.6 |
|           64 | all_keys_one_cluster |                30.0 |                 54.2 |            229.7 |
|          256 | normal               |                10.6 |                  8.6 |            103.5 |
|          256 | all_keys_one_cluster |               108.7 |                213.8 |            471.5 |
|         1024 | normal               |                11.3 |                 10.2 |            127.5 |
|         1024 | all_keys_one_cluster |               420.1 |                807.7 |           2236.4 |
|         4096 | normal               |                13.7 |                 18.7 |             98.0 |
|         4096 | all_keys_one_cluster |              1587.5 |               3125.5 |           6064.3 |

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

44 table/trace pairs were checked against the reference model; 44 had no wrong or refused result.

### Peak heap (KiB)

Process heap held by the table at its peak (malloc_usable_size, allocator rounding included; a realloc that moves a block is charged for both copies).

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |    292.0 |                292.0 |                292.0 |                   292.0 |                             292.0 |                877.0 |             776.7 |            754.0 |           525.7 |                652.8 |                       551.5 |                     1182.0 |
| ESP-IDF  |   7480.9 |               7480.9 |               7480.9 |                  7480.9 |                             nan   |              15375.6 |             nan   |          19842.6 |         13985.6 |              18289.0 |                     18105.8 |                    41420.0 |
| FreeRTOS |    292.0 |                292.0 |                292.0 |                   292.0 |                             292.0 |                937.6 |            1158.9 |            758.1 |           534.9 |                651.2 |                       550.4 |                     1230.7 |
| Zephyr   |   1870.3 |               1870.3 |               2216.7 |                  1870.3 |                             nan   |               7572.2 |             nan   |           5792.1 |          4154.9 |               5211.4 |                      4473.8 |                    19054.6 |

### Peak heap bytes per live declaration (at the peak)

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.1 |                 43.1 |                 43.1 |                    43.1 |                              43.1 |                129.5 |             114.7 |            111.3 |            77.6 |                 96.4 |                        81.4 |                      174.5 |
| ESP-IDF  |     49.9 |                 49.9 |                 49.9 |                    49.9 |                             nan   |                102.6 |             nan   |            132.4 |            93.3 |                122.0 |                       120.8 |                      276.3 |
| FreeRTOS |     46.6 |                 46.6 |                 46.6 |                    46.6 |                              46.6 |                149.7 |             185.0 |            121.1 |            85.4 |                104.0 |                        87.9 |                      196.5 |
| Zephyr   |     41.7 |                 41.7 |                 49.4 |                    41.7 |                             nan   |                168.8 |             nan   |            129.1 |            92.6 |                116.2 |                        99.7 |                      424.8 |

### Allocator calls during the whole replay

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     16.0 |                 16.0 |                 16.0 |                    16.0 |                              16.0 |              19804.0 |           26299.0 |          35323.0 |         43882.0 |              39468.0 |                     29565.0 |                     3385.0 |
| ESP-IDF  |     24.0 |                 24.0 |                 24.0 |                    24.0 |                             nan   |             629511.0 |             nan   |        1032063.0 |       1342739.0 |            1225740.0 |                    860749.0 |                   168333.0 |
| FreeRTOS |     16.0 |                 16.0 |                 16.0 |                    16.0 |                              16.0 |              32473.0 |           50714.0 |          53727.0 |        115265.0 |             108616.0 |                     41135.0 |                     4786.0 |
| Zephyr   |     25.0 |                 25.0 |                 21.0 |                    25.0 |                             nan   |             664319.0 |             nan   |        1056367.0 |       1116929.0 |             974653.0 |                    870284.0 |                   147498.0 |

### Whole-trace replay time (ns per trace operation, median)

One timer around each complete replay, table construction and destruction included. Per-table 95% bootstrap intervals of the median are in `legacy_replay_time.csv`.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.3 |                 51.3 |                 43.5 |                    46.5 |                              40.1 |                 64.5 |             701.9 |             70.0 |            70.8 |                 58.1 |                        53.3 |                       38.3 |
| ESP-IDF  |     67.5 |                 58.4 |                 58.2 |                    54.3 |                             nan   |                 85.7 |             nan   |            131.7 |           138.5 |                141.8 |                       107.8 |                       82.9 |
| FreeRTOS |     39.8 |                 40.2 |                 49.2 |                    34.2 |                              38.4 |                 44.9 |             568.6 |             58.7 |            65.1 |                 46.9 |                        38.3 |                       33.6 |
| Zephyr   |     41.2 |                 41.9 |                 38.6 |                    38.1 |                             nan   |                 72.1 |             nan   |            119.7 |           105.4 |                 77.0 |                        67.9 |                       63.6 |

### Lookup latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     52.7 |                 51.5 |                 52.1 |                    47.9 |                              44.8 |                 58.2 |              67.2 |            150.9 |           120.0 |                 53.3 |                        50.9 |                       53.9 |
| ESP-IDF  |     69.0 |                 60.6 |                 81.7 |                    78.7 |                             nan   |                115.7 |             nan   |            180.4 |           174.4 |                101.1 |                       101.1 |                      115.7 |
| FreeRTOS |     53.9 |                 52.7 |                 53.3 |                    48.4 |                              50.2 |                 69.0 |              82.3 |            121.1 |           118.1 |                 63.0 |                        60.5 |                       78.1 |
| Zephyr   |     68.4 |                 63.6 |                 58.7 |                    62.4 |                             nan   |                 85.4 |             nan   |            293.7 |           277.3 |                 89.0 |                        84.8 |                       84.2 |

### Declare latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     83.6 |                 87.8 |                 81.8 |                    75.7 |                              92.7 |                203.0 |            7840.0 |            204.2 |           144.8 |                144.2 |                       120.6 |                      103.0 |
| ESP-IDF  |    152.0 |                164.1 |                159.3 |                   159.9 |                             nan   |                434.2 |             nan   |            611.6 |           641.9 |                781.7 |                       365.1 |                      403.9 |
| FreeRTOS |     79.9 |                 80.5 |                 78.1 |                    73.9 |                              86.6 |                166.5 |            5173.3 |            170.1 |           136.8 |                141.1 |                       125.3 |                      141.1 |
| Zephyr   |    132.6 |                141.1 |                113.2 |                   127.2 |                             nan   |                314.3 |             nan   |            418.4 |           326.4 |                500.8 |                       297.3 |                      311.3 |

### Exit latency, p95 (ns)

Per-call TSC timing; the calibrated cost of one timed interval (16 ns here) is subtracted. p50 and p99 are in the summary CSV.

| trace    |   STRATA |   STRATA (raw names) |   STRATA (no shrink) |   STRATA (sparse index) |   arena + chains (allocator-free) |   METIS-X (previous) |   old arena table |   old scope maps |   map per scope |   std map + undo log |   Swiss node map + undo log |   Swiss flat map, interned |
|:---------|---------:|---------------------:|---------------------:|------------------------:|----------------------------------:|---------------------:|------------------:|-----------------:|----------------:|---------------------:|----------------------------:|---------------------------:|
| Arduino  |     43.0 |                 43.6 |                 42.4 |                    45.4 |                              55.7 |                256.9 |             708.8 |            225.4 |           171.4 |                492.5 |                       442.3 |                       29.1 |
| ESP-IDF  |     49.0 |                 46.6 |                 54.5 |                    56.9 |                             nan   |                419.6 |             nan   |            247.7 |           221.6 |                557.7 |                       516.5 |                       41.2 |
| FreeRTOS |     31.5 |                 31.5 |                 30.3 |                    31.5 |                              38.1 |                152.0 |             507.3 |            152.6 |           132.6 |                298.5 |                       308.8 |                       30.3 |
| Zephyr   |     53.3 |                 52.1 |                 47.8 |                    50.9 |                             nan   |                266.4 |             nan   |            276.1 |           236.2 |                558.9 |                       505.0 |                       32.1 |

### Previous implementation (METIS-X) versus STRATA

Reduction = (old - new) / old x 100; negative means STRATA is worse. The replay reduction is the median of the per-round reductions (samples paired by round) with a 95% bootstrap interval; 'established = yes' means the interval excludes zero.

| trace    |   peak heap KiB old |    new |   peak heap red. % |   allocs old |   allocs new |   allocs red. % |   replay ms old |   replay ms new |   replay red. % |   CI low |   CI high | established   |   lookup p95 old |   lookup p95 new |   lookup p95 red. % |   declare p95 red. % |   exit p95 red. % |   old refused |
|:---------|--------------------:|-------:|-------------------:|-------------:|-------------:|----------------:|----------------:|----------------:|----------------:|---------:|----------:|:--------------|-----------------:|-----------------:|--------------------:|---------------------:|------------------:|--------------:|
| Arduino  |               877.0 |  292.0 |               66.7 |        19804 |           16 |            99.9 |             6.1 |             4.1 |            32.9 |    -72.8 |      40.6 | no            |             58.2 |             52.7 |                 9.5 |                 58.8 |              83.3 |             0 |
| ESP-IDF  |             15375.6 | 7480.9 |               51.3 |       629511 |           24 |           100.0 |           191.0 |           150.4 |            19.7 |    -10.3 |      36.0 | no            |            115.7 |             69.0 |                40.4 |                 65.0 |              88.3 |             0 |
| FreeRTOS |               937.6 |  292.0 |               68.9 |        32473 |           16 |           100.0 |            10.2 |             9.0 |            11.5 |     -8.9 |      39.2 | no            |             69.0 |             53.9 |                21.9 |                 52.0 |              79.3 |             0 |
| Zephyr   |              7572.2 | 1870.3 |               75.3 |       664319 |           25 |           100.0 |           187.8 |           107.3 |            42.5 |     33.9 |      49.0 | yes           |             85.4 |             68.4 |                19.9 |                 57.8 |              80.0 |             0 |

### STRATA against every baseline (range over the traces of this section)

| baseline                        |   traces |   faster (established) |   slower (established) |   peak heap red. % min |   median |   max |   replay time red. % min |   median  |   max  |
|:--------------------------------|---------:|-----------------------:|-----------------------:|-----------------------:|---------:|------:|-------------------------:|----------:|-------:|
| arena + chains (allocator-free) |        2 |                      0 |                      0 |                   -0.0 |     -0.0 |  -0.0 |                    -11.8 |      -9.4 |   -6.9 |
| METIS-X (previous)              |        4 |                      1 |                      0 |                   51.3 |     67.8 |  75.3 |                     11.5 |      26.3 |   42.5 |
| old arena table                 |        2 |                      2 |                      0 |                   62.4 |     68.6 |  74.8 |                     93.1 |      93.3 |   93.6 |
| old scope maps                  |        4 |                      4 |                      0 |                   61.3 |     61.9 |  67.7 |                     36.5 |      42.4 |   65.6 |
| map per scope                   |        4 |                      3 |                      0 |                   44.5 |     46.0 |  55.0 |                     28.1 |      46.0 |   60.7 |
| std map + undo log              |        4 |                      2 |                      0 |                   55.2 |     57.2 |  64.1 |                     17.5 |      37.1 |   53.4 |
| Swiss node map + undo log       |        4 |                      2 |                      0 |                   46.9 |     52.6 |  58.7 |                     -3.4 |      26.5 |   38.0 |
| Swiss flat map, interned        |        4 |                      1 |                      1 |                   75.3 |     79.1 |  90.2 |                    -30.8 |       1.8 |   29.3 |

