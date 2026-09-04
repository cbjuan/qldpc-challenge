# Periodic BB exact-certification summary

Targets: 128; exact: 41; refuted: 6; sharded closed pending serial: 1; timeout: 80; pending: 0.

Non-overlapping batch wall time: 413148.4 s; summed new-task wall time: 8699331.1 s; summed new-task CPU time: 8616009.4 s.

A side marked `sharded_closed_pending_serial` has all logical-row cutoff MILPs proven infeasible, but the candidate is `exact` only after a hash-matched, persisted stock `verify/certify.py` result has `d_exact: true`.

## Completed batches

| stage | budget (s) | workers | candidates | new tasks | inherited | wall (s) | new-task CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| priority-t5-w32 | 5 | 32 | 10 | 288 | 0 | 144.5 | 4419.3 |
| all-t5-w64 | 5 | 64 | 128 | 10520 | 20 | 829.2 | 51244.1 |
| all-t30-w64 | 30 | 64 | 128 | 7218 | 3322 | 3868.1 | 238522.7 |
| all-t120-w64 | 120 | 64 | 128 | 5192 | 5348 | 8991.6 | 560822.1 |
| selective-t600-w63-r1 | 600 | 63 | 13 | 136 | 384 | 1861.0 | 78082.4 |
| selective-t3600-w62-r1 | 3600 | 62 | 7 | 60 | 72 | 3635.1 | 190534.9 |
| selective-t3600-w62-r2 | 3600 | 62 | 5 | 68 | 48 | 6528.3 | 233004.1 |
| selective-t600-w54-r2 | 600 | 54 | 3 | 156 | 872 | 793.7 | 35271.9 |
| selective-t600-w54-r3 | 600 | 54 | 1 | 101 | 371 | 741.7 | 25024.7 |
| selective-t600-w45-r4 | 600 | 45 | 1 | 139 | 333 | 853.5 | 30872.4 |
| selective-t3600-w2-r5-c0040002 | 3600 | 2 | 1 | 2 | 470 | 790.9 | 1367.8 |
| selective-t14400-w2-r6-c0020418 | 14400 | 2 | 1 | 2 | 58 | 3627.5 | 7074.8 |
| selective-t600-w9-r8-c0010524 | 600 | 9 | 1 | 18 | 18 | 1118.8 | 7482.2 |
| selective-t600-w22-r9-c0020283 | 600 | 22 | 1 | 22 | 22 | 601.6 | 12899.1 |
| selective-t600-w13-r10-c0045064 | 600 | 13 | 1 | 26 | 26 | 1208.8 | 15455.5 |
| selective-t600-w22-r11-c0045062 | 600 | 22 | 1 | 28 | 32 | 728.6 | 9184.0 |
| selective-t600-w12-r12-c0045061 | 600 | 12 | 1 | 32 | 32 | 1812.4 | 18948.5 |
| selective-t600-w11-r13-c0045049 | 600 | 11 | 1 | 34 | 34 | 2404.0 | 20194.3 |
| selective-t14400-w1-r14-c0040000 | 14400 | 1 | 1 | 1 | 471 | 747.5 | 731.0 |
| selective-t600-w9-r15-c0045060 | 600 | 9 | 1 | 34 | 34 | 2417.7 | 20246.8 |
| selective-t3600-w3-r16-c0045062 | 3600 | 3 | 1 | 8 | 52 | 3341.1 | 8697.1 |
| selective-t600-w13-r17-c0045048 | 600 | 13 | 1 | 36 | 36 | 1817.8 | 21394.9 |
| one-sided-t600-w48-r27-restart1 | 600 | 48 | 9 | 362 | 362 | 4867.8 | 215519.6 |
| selective-t14400-w8-r28-c0020168-restart1 | 14400 | 8 | 1 | 8 | 32 | 10297.7 | 61397.2 |
| selective-t3600-w9-r29-c0010524 | 3600 | 9 | 1 | 9 | 27 | 3601.5 | 18822.5 |
| selective-t600-w13-r30a-c0020118 | 600 | 13 | 1 | 67 | 29 | 1890.9 | 20347.5 |
| selective-t600-w26-r30b-c0045591-c0045037 | 600 | 26 | 2 | 163 | 65 | 2923.6 | 68253.5 |
| selective-t3600-w9-r30a2-c0020118 | 3600 | 9 | 1 | 8 | 88 | 907.6 | 5347.9 |
| selective-t600-w21-r32b-c0045035 | 600 | 21 | 1 | 110 | 14 | 2169.9 | 39183.6 |
| selective-t3600-w11-r35d-c0020283-restart1 | 3600 | 11 | 1 | 11 | 33 | 3601.1 | 39096.6 |
| selective-t600-w11-r35e-c0045036-restart1 | 600 | 11 | 1 | 48 | 72 | 3001.8 | 28025.9 |
| selective-t600-w7-r35f-c0045033-restart1 | 600 | 7 | 1 | 86 | 46 | 5095.2 | 32973.8 |
| selective-t3600-w11-r35h-c0045035-restart1 | 3600 | 11 | 1 | 28 | 96 | 3036.8 | 28121.2 |
| selective-t14400-w1-r35c-c0010524-restart1 | 14400 | 1 | 1 | 1 | 35 | 4607.1 | 4522.4 |
| selective-t3600-w14-r35g-c0045037-restart1 | 3600 | 14 | 1 | 14 | 102 | 1902.8 | 16836.7 |
| selective-t600-w11-r36a-c0045032 | 600 | 11 | 1 | 129 | 7 | 5438.4 | 56267.6 |
| selective-t600-w7-r36b-c0045030 | 600 | 7 | 1 | 143 | 1 | 8521.9 | 57398.9 |
| selective-t600-w8-r36c-c0045031 | 600 | 8 | 1 | 137 | 3 | 7540.6 | 57925.8 |
| selective-t600-w8-r36d-c0045041 | 600 | 8 | 1 | 50 | 50 | 4271.9 | 29809.9 |
| selective-t14400-w11-r37a-c0020283 | 14400 | 11 | 1 | 11 | 33 | 14401.6 | 91945.3 |
| selective-t600-w7-r38a-c0045043-restart1 | 600 | 7 | 1 | 46 | 46 | 4311.0 | 27819.9 |
| selective-t600-w11-r38b-c0045042 | 600 | 11 | 1 | 48 | 48 | 3021.5 | 28942.9 |
| selective-t600-w8-r38c-c0046163 | 600 | 8 | 1 | 46 | 46 | 3625.0 | 27518.2 |
| selective-t600-w7-r38d-c0045014 | 600 | 7 | 1 | 46 | 46 | 4247.7 | 27737.7 |
| selective-t3600-w10-r39a-c0045048 | 3600 | 10 | 1 | 35 | 37 | 9819.1 | 87956.7 |
| selective-t3600-w4-r39b-c0045049 | 3600 | 4 | 1 | 34 | 34 | 24422.4 | 88517.0 |
| selective-t3600-w8-r39c-c0045064 | 3600 | 8 | 1 | 26 | 26 | 10999.7 | 74006.7 |
| selective-t3600-w7-r39d-c0045047 | 3600 | 7 | 1 | 38 | 38 | 19519.9 | 126784.6 |
| selective-t3600-w8-r39e-c0046587 | 3600 | 8 | 1 | 38 | 38 | 18003.9 | 135650.0 |
| selective-t3600-w7-r39f-c0045061 | 3600 | 7 | 1 | 32 | 32 | 18002.3 | 114185.1 |
| selective-t28800-w1-r41a-c0020283 | 28800 | 1 | 1 | 1 | 43 | 15298.1 | 15142.6 |
| selective-t600-w8-r41b-c0060702 | 600 | 8 | 1 | 28 | 0 | 2485.4 | 17050.6 |
| selective-t600-w10-r41c-c0056213 | 600 | 10 | 1 | 24 | 0 | 1808.9 | 14433.4 |
| selective-t600-w8-r41d-c0058579 | 600 | 8 | 1 | 36 | 0 | 3029.8 | 21660.8 |
| selective-t600-w8-r41e-c0060754 | 600 | 8 | 1 | 32 | 0 | 2478.8 | 19158.3 |
| selective-t600-w10-r41f-c0045113 | 600 | 10 | 1 | 48 | 0 | 3001.7 | 28449.3 |
| selective-t600-w10-r41g-c0045107 | 600 | 10 | 1 | 41 | 7 | 2503.9 | 21951.7 |
| selective-t600-w9-r41h-c0050641 | 600 | 9 | 1 | 32 | 0 | 2456.2 | 19182.5 |
| selective-t14400-w16-r41i-c0050584 | 14400 | 16 | 1 | 16 | 0 | 14402.5 | 227868.9 |
| selective-t14400-w3-r41j-c0048487 | 14400 | 3 | 1 | 12 | 0 | 57608.8 | 171145.7 |
| selective-t600-w12-r42a-c0062627 | 600 | 12 | 1 | 28 | 0 | 1824.3 | 17241.2 |
| selective-t600-w8-r42b-c0052988 | 600 | 8 | 1 | 32 | 0 | 2472.6 | 19248.8 |
| selective-t600-w6-r42c-c0059571 | 600 | 6 | 1 | 32 | 0 | 3612.1 | 19163.5 |
| selective-t600-w11-r42d-c0045091 | 600 | 11 | 1 | 24 | 0 | 1803.0 | 14427.7 |
| selective-t14400-w7-r42f-c0045048 | 14400 | 7 | 1 | 18 | 54 | 43202.9 | 256261.9 |
| selective-t3600-w16-r42g-c0045033 | 3600 | 16 | 1 | 33 | 99 | 2830.6 | 35036.1 |
| selective-t600-w7-r42h-c0048101 | 600 | 7 | 1 | 16 | 0 | 1878.6 | 9719.1 |
| selective-t3600-w16-r42j-c0045036 | 3600 | 16 | 1 | 45 | 75 | 3500.1 | 46289.2 |
| selective-t14400-w9-r42i-c0045049 | 14400 | 9 | 1 | 17 | 51 | 28802.6 | 241765.4 |
| selective-t14400-w14-r42m-c0045047 | 14400 | 14 | 1 | 28 | 48 | 28803.1 | 316787.5 |
| selective-t3600-w16-r42o-c0045031 | 3600 | 16 | 1 | 60 | 80 | 6134.3 | 85015.0 |
| selective-t3600-w13-r42q-c0045032 | 3600 | 13 | 1 | 66 | 70 | 7335.4 | 87378.8 |
| selective-t14400-w3-r42p-c0045031 | 14400 | 3 | 1 | 3 | 137 | 5357.1 | 13404.1 |
| selective-t14400-w1-r42v-c0045032 | 14400 | 1 | 1 | 1 | 135 | 3986.9 | 3943.5 |
| selective-t3600-w12-r42w-c0060754 | 3600 | 12 | 1 | 32 | 0 | 10803.0 | 114292.7 |
| selective-t28800-w3-r44b-c0048487 | 28800 | 3 | 1 | 12 | 0 | 115203.5 | 343329.3 |
| selective-t28800-w7-r44d-c0045048 | 28800 | 7 | 1 | 18 | 54 | 86403.4 | 514255.9 |
| selective-t28800-w14-r44h-c0045047 | 28800 | 14 | 1 | 19 | 57 | 57602.9 | 541999.5 |
| selective-t28800-w3-r44c-c0045064 | 28800 | 3 | 1 | 6 | 46 | 57601.5 | 150028.7 |
| selective-t14400-w2-r44l-c0058579 | 14400 | 2 | 1 | 36 | 0 | 259209.0 | 515489.0 |
| selective-t28800-w9-r44n-c0045049 | 28800 | 9 | 1 | 17 | 51 | 57603.3 | 485271.8 |
| selective-t600-w8-r47e-c0045426 | 600 | 8 | 1 | 16 | 0 | 1222.1 | 9574.9 |
| selective-t600-w8-r47f-c0051763 | 600 | 8 | 1 | 16 | 0 | 1244.6 | 9594.8 |
| selective-t600-w8-r47g-c0057792 | 600 | 8 | 1 | 16 | 0 | 1228.3 | 9572.0 |
| selective-t57600-w4-r48a-c0045064 | 57600 | 4 | 1 | 4 | 48 | 22325.8 | 81313.3 |
| selective-t28800-w1-r48b-c0046378 | 28800 | 1 | 1 | 8 | 0 | 230405.3 | 229244.6 |
| selective-t28800-w1-r48d-c0051880 | 28800 | 1 | 1 | 8 | 0 | 230405.1 | 229329.4 |
| selective-t28800-w1-r48c-c0055406 | 28800 | 1 | 1 | 8 | 0 | 230405.5 | 229341.9 |
| selective-t28800-w2-r48e-c0045244 | 28800 | 2 | 1 | 8 | 0 | 115203.8 | 229257.0 |

Incomplete batch starts (not counted as timeouts):
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r29b-c0010524-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r40a-c0046378-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r42l-c0055406-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r42n-c0051880-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r44i-c0045107-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r44j-c0060702-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r44k-c0056213-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r44o-c0045113-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w12-r43a-c0060754-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w12-r44m-c0060754-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w2-r42k-c0045244-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w3-r42e-c0045064-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w8-r7-c0020168-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r44a-c0046378-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r44f-c0055406-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r44g-c0051880-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r46a-c0060754-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r46b-c0050584-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r47a-c0046378-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r47b-c0055406-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r47c-c0051880-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w14-r43b-c0045047-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w2-r44e-c0045244-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w2-r47d-c0045244-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w4-r45c-c0060754-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w9-r42z-c0045049-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w1-r42r-c0045107-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w1-r42s-c0060702-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w1-r42t-c0056213-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w1-r42x-c0045113-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w18-r33b-c0045037-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w2-r42u-c0058579-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w20-r31-c0020283-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w6-r34a-c0045035-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w1-r22-c0045016-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w1-r25-c0045044-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w1-r26-c0046164-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w10-r20-c0045047-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w10-r23-c0045046-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w11-r32a-c0045036-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w11-r37a-c0045043-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w4-r18-c0045059-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w4-r47h-c0049482-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w5-r21-c0046587-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w7-r33a-c0045033-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w8-r19-c0045017-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w8-r24-c0045015-start.json`

Persisted tasks outside completed batches: 501 (2774595.0 CPU s); retained as evidence but not counted as completed-batch timeouts.

## Targets

| target | parameters | X | Z | overall | budgets (s) | new-task wall (s) | CPU (s) |
|---|---:|---|---|---|---:|---:|---:|
| c0000142 | [[208,52,2]] | exact | exact | exact | 5 | 8.9 | 8.5 |
| c0002359 | [[108,36,3]] | exact | exact | exact | 5 | 16.4 | 15.8 |
| c0004417 | [[452,228,2]] | exact | exact | exact | 5 | 154.4 | 151.4 |
| c0004584 | [[198,26,3]] | exact | exact | exact | 5,30 | 49.3 | 48.5 |
| c0006423 | [[234,78,3]] | exact | exact | exact | 5 | 59.6 | 58.6 |
| c0006625 | [[266,38,4]] | exact | exact | exact | 5,30 | 150.1 | 148.1 |
| c0010524 | [[270,18,9]] | exact | exact | exact | 5,30,120,600,3600,14400 | 34662.8 | 34240.1 |
| c0011462 | [[270,90,3]] | exact | exact | exact | 5,30 | 459.7 | 452.8 |
| c0012783 | [[224,112,2]] | exact | exact | exact | 5 | 3.7 | 3.4 |
| c0014474 | [[396,136,3]] | exact | exact | exact | 5,30,120,600 | 6770.1 | 6705.7 |
| c0016039 | [[288,96,3]] | exact | exact | exact | 5,30 | 527.1 | 520.6 |
| c0016229 | [[208,26,6]] | exact | exact | exact | 5,30,120 | 1017.0 | 1006.5 |
| c0016394 | [[288,100,3]] | exact | exact | exact | 5,30 | 491.0 | 483.8 |
| c0018628 | [[280,20,7]] | exact | exact | exact | 5,30,120 | 2422.4 | 2393.3 |
| c0019513 | [[384,96,4]] | exact | exact | exact | 5,30,120 | 1622.2 | 1598.4 |
| c0019531 | [[248,62,4]] | exact | exact | exact | 5 | 20.2 | 19.5 |
| c0020058 | [[304,52,7]] | exact | exact | exact | 5,30,120,600 | 19177.7 | 18951.0 |
| c0020118 | [[272,48,8]] | exact | exact | exact | 5,30,120,600,3600 | 39968.1 | 39462.8 |
| c0020168 | [[280,20,8]] | exact | exact | exact | 5,30,120,600,3600,14400 | 104233.2 | 102939.0 |
| c0020198 | [[238,46,6]] | exact | exact | exact | 5,30,120 | 3207.7 | 3168.2 |
| c0020283 | [[330,22,9]] | exact | exact | exact | 5,30,120,600,3600,14400,28800 | 173457.5 | 171220.5 |
| c0020343 | [[252,48,6]] | exact | exact | exact | 5,30,120 | 3179.1 | 3136.9 |
| c0020418 | [[270,30,7]] | exact | exact | exact | 5,30,120,600,3600,14400 | 53967.7 | 53229.3 |
| c0020458 | [[240,30,6]] | exact | exact | exact | 5,30,120 | 1306.7 | 1289.3 |
| c0020498 | [[224,44,6]] | exact | exact | exact | 5,30,120 | 1911.4 | 1887.7 |
| c0020623 | [[260,26,6]] | exact | exact | exact | 5,30 | 178.0 | 175.8 |
| c0020718 | [[256,46,6]] | exact | exact | exact | 5,30,120 | 4119.5 | 4060.3 |
| c0020918 | [[234,26,7]] | exact | exact | exact | 5,30,120,600,3600 | 25452.4 | 25184.2 |
| c0020978 | [[266,50,6]] | exact | exact | exact | 5,30,120 | 3190.0 | 3148.6 |
| c0040000 | [[696,236,3]] | exact | exact | exact | 5,30,120,600,14400 | 82565.7 | 81915.1 |
| c0040001 | [[696,232,3]] | exact | exact | exact | 5,30,120 | 4767.6 | 4708.7 |
| c0040002 | [[696,236,3]] | exact | exact | exact | 5,30,120,600,3600 | 57561.9 | 56917.1 |
| c0040003 | [[690,234,3]] | exact | exact | exact | 5,30,120,600 | 40542.9 | 40088.1 |
| c0040004 | [[672,228,3]] | exact | exact | exact | 5,30,120,600 | 40950.3 | 40544.9 |
| c0040005 | [[696,174,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120 | 28911.2 | 28671.4 |
| c0040006 | [[688,172,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120 | 28405.8 | 28160.6 |
| c0040007 | [[680,170,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120 | 28448.2 | 28203.9 |
| c0045014 | [[690,46,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 38523.5 | 38222.3 |
| c0045015 | [[660,44,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 45855.6 | 45372.9 |
| c0045016 | [[600,40,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 34512.6 | 34002.1 |
| c0045017 | [[570,38,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 45681.2 | 45095.5 |
| c0045030 | [[464,72,8]] | timeout | timeout | timeout | 5,30,120,600 | 80646.5 | 79488.9 |
| c0045031 | [[448,70,8]] | exact | exact | exact | 5,30,120,600,3600,14400 | 180857.5 | 177953.2 |
| c0045032 | [[432,68,8]] | exact | exact | exact | 5,30,120,600,3600,14400 | 171036.1 | 168528.6 |
| c0045033 | [[416,66,8]] | exact | exact | exact | 5,30,120,600,3600 | 101917.3 | 100592.2 |
| c0045035 | [[384,62,8]] | exact | exact | exact | 5,30,120,600,3600 | 87904.2 | 86755.2 |
| c0045036 | [[368,60,8]] | exact | exact | exact | 5,30,120,600,3600 | 133570.9 | 131737.4 |
| c0045037 | [[352,58,8]] | exact | exact | exact | 5,30,120,600,3600 | 72114.9 | 71180.9 |
| c0045041 | [[700,50,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 40210.2 | 39414.0 |
| c0045042 | [[672,48,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 38025.1 | 37698.0 |
| c0045043 | [[644,46,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 36749.8 | 36230.2 |
| c0045044 | [[616,44,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 34887.1 | 34376.4 |
| c0045046 | [[560,40,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 42996.9 | 42419.4 |
| c0045047 | [[532,38,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600,14400,28800 | 1043484.8 | 1032598.9 |
| c0045048 | [[504,36,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600,14400,28800 | 894582.4 | 886381.6 |
| c0045049 | [[476,34,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600,14400,28800 | 850293.0 | 841781.7 |
| c0045059 | [[540,36,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 39224.3 | 38703.3 |
| c0045060 | [[510,34,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 27957.0 | 27603.8 |
| c0045061 | [[480,32,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 141370.4 | 139962.4 |
| c0045062 | [[450,30,9]] | exact | exact | exact | 5,30,120,600,3600 | 24273.1 | 23993.8 |
| c0045064 | [[390,26,9]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600,14400,28800,57600 | 471625.6 | 467366.4 |
| c0045088 | [[648,8,34]] | timeout | timeout | timeout | 5,30,120,600,3600 | 71355.0 | 70566.7 |
| c0045091 | [[576,12,28]] | timeout | timeout | timeout | 5,30,120,600 | 19292.8 | 19108.6 |
| c0045094 | [[504,8,28]] | timeout | timeout | timeout | 5,30,120 | 3580.4 | 3543.2 |
| c0045107 | [[576,24,12]] | timeout | timeout | timeout | 5,30,120,600,3600,14400 | 353616.4 | 351107.7 |
| c0045113 | [[432,24,12]] | timeout | timeout | timeout | 5,30,120,600,3600,14400 | 347245.4 | 344711.6 |
| c0045118 | [[630,8,30]] | timeout | timeout | timeout | 5,30,120 | 3734.6 | 3687.4 |
| c0045244 | [[648,4,34]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 409827.8 | 406893.6 |
| c0045426 | [[420,8,26]] | timeout | timeout | timeout | 5,30,120,600 | 12529.7 | 12428.1 |
| c0045508 | [[648,4,36]] | timeout | refuted | refuted | 5,30,120,600,3600 | 35517.3 | 35233.6 |
| c0045591 | [[448,56,8]] | timeout | timeout | timeout | 5,30,120,600 | 50921.8 | 50244.4 |
| c0046163 | [[644,46,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 36610.3 | 36282.8 |
| c0046164 | [[616,44,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 34256.9 | 33759.1 |
| c0046282 | [[540,8,30]] | timeout | timeout | timeout | 5,30,120 | 3235.8 | 3205.7 |
| c0046378 | [[630,4,32]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 352231.3 | 349924.7 |
| c0046587 | [[532,38,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 176170.8 | 174507.0 |
| c0046841 | [[660,8,34]] | timeout | timeout | timeout | 5,30,120 | 3943.3 | 3912.1 |
| c0047091 | [[630,14,20]] | timeout | timeout | timeout | 5,30,120 | 5955.7 | 5908.5 |
| c0047122 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3182.0 | 3156.9 |
| c0048101 | [[660,8,34]] | timeout | timeout | timeout | 5,30,120,600 | 13641.2 | 13520.2 |
| c0048487 | [[686,6,36]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 572462.1 | 567903.7 |
| c0048911 | [[630,8,28]] | timeout | timeout | timeout | 5,30,120 | 3499.5 | 3474.9 |
| c0049220 | [[648,4,38]] | refuted | timeout | refuted | 5,30,120 | 1543.8 | 1530.4 |
| c0049291 | [[660,8,28]] | timeout | timeout | timeout | 5,30,120 | 3799.2 | 3770.2 |
| c0049482 | [[540,8,26]] | timeout | timeout | timeout | 5,30,120 | 3105.7 | 3079.4 |
| c0049503 | [[648,8,30]] | timeout | timeout | timeout | 5,30,120 | 3823.7 | 3791.8 |
| c0049506 | [[540,8,30]] | timeout | timeout | timeout | 5,30,120 | 3136.2 | 3112.0 |
| c0049780 | [[630,8,30]] | timeout | timeout | timeout | 5,30,120 | 3632.0 | 3601.9 |
| c0049795 | [[600,8,26]] | timeout | timeout | timeout | 5,30,120 | 3418.6 | 3392.1 |
| c0049803 | [[648,8,28]] | timeout | timeout | timeout | 5,30,120 | 3714.7 | 3687.1 |
| c0049926 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3154.9 | 3129.9 |
| c0050011 | [[660,8,28]] | timeout | timeout | timeout | 5,30,120 | 3769.1 | 3735.8 |
| c0050071 | [[660,8,28]] | timeout | timeout | timeout | 5,30,120 | 3591.4 | 3562.0 |
| c0050292 | [[576,8,30]] | timeout | timeout | timeout | 5,30,120 | 3323.5 | 3295.1 |
| c0050526 | [[540,8,30]] | timeout | timeout | timeout | 5,30,120 | 3088.5 | 3060.1 |
| c0050584 | [[630,8,34]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 532178.8 | 527685.5 |
| c0050641 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120,600 | 25559.8 | 25348.0 |
| c0050670 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3241.4 | 3213.0 |
| c0050719 | [[660,8,28]] | timeout | timeout | timeout | 5,30,120 | 3271.5 | 3244.5 |
| c0051753 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3783.5 | 3754.4 |
| c0051763 | [[540,8,26]] | timeout | timeout | timeout | 5,30,120,600 | 12726.4 | 12641.7 |
| c0051880 | [[648,4,38]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 337985.8 | 335921.3 |
| c0051899 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3692.9 | 3662.5 |
| c0052765 | [[648,8,30]] | timeout | timeout | timeout | 5,30,120 | 3673.9 | 3641.6 |
| c0052988 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120,600 | 25558.9 | 25328.7 |
| c0054814 | [[686,6,28]] | timeout | refuted | refuted | 5,30,120 | 2046.8 | 2023.9 |
| c0054828 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3827.5 | 3794.6 |
| c0054859 | [[686,6,36]] | timeout | timeout | timeout | 5,30,120,600,3600 | 53977.9 | 53343.5 |
| c0054911 | [[630,8,28]] | timeout | timeout | timeout | 5,30,120 | 3907.0 | 3871.0 |
| c0055020 | [[648,8,28]] | timeout | timeout | timeout | 5,30,120 | 3866.8 | 3830.1 |
| c0055406 | [[630,4,36]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 337959.8 | 335876.6 |
| c0056213 | [[576,12,30]] | timeout | timeout | timeout | 5,30,120,600,3600,14400 | 340847.3 | 338819.9 |
| c0056263 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3218.0 | 3191.1 |
| c0056884 | [[686,12,28]] | timeout | refuted | refuted | 5,30,120 | 4462.2 | 4428.4 |
| c0057634 | [[686,12,30]] | refuted | timeout | refuted | 5,30,120 | 4876.1 | 4839.9 |
| c0057792 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120,600 | 12729.4 | 12630.0 |
| c0058472 | [[648,8,30]] | timeout | timeout | timeout | 5,30,120 | 3734.6 | 3702.8 |
| c0058579 | [[686,18,24]] | timeout | timeout | timeout | 5,30,120,600,3600,14400 | 606832.1 | 603171.9 |
| c0058638 | [[648,8,32]] | timeout | timeout | timeout | 5,30,120 | 3842.1 | 3811.8 |
| c0059571 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120,600 | 25416.5 | 25205.9 |
| c0060611 | [[630,10,28]] | timeout | refuted | refuted | 5,30,120 | 3615.9 | 3586.0 |
| c0060702 | [[630,14,28]] | timeout | timeout | timeout | 5,30,120,600,3600,14400 | 344375.0 | 342475.2 |
| c0060754 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120,600,3600,14400,28800 | 717390.1 | 711386.8 |
| c0060824 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3781.4 | 3752.1 |
| c0060866 | [[648,8,32]] | timeout | timeout | timeout | 5,30,120 | 3847.1 | 3819.0 |
| c0061526 | [[648,8,32]] | timeout | timeout | timeout | 5,30,120 | 3869.6 | 3842.0 |
| c0062627 | [[630,14,28]] | timeout | timeout | timeout | 5,30,120,600 | 23326.5 | 23114.5 |
| c0063118 | [[648,8,34]] | timeout | timeout | timeout | 5,30,120 | 3455.9 | 3440.2 |
