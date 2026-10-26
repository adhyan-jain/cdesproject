
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
