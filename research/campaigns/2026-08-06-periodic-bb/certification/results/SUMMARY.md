# Periodic BB exact-certification summary

Targets: 128; exact: 26; refuted: 6; sharded closed pending serial: 10; timeout: 86; pending: 0.

Non-overlapping batch wall time: 60266.1 s; summed new-task wall time: 2695213.5 s; summed new-task CPU time: 2663245.6 s.

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

Incomplete batch starts (not counted as timeouts):
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r29b-c0010524-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w1-r40a-c0046378-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t14400-w8-r7-c0020168-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t28800-w1-r41a-c0020283-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w18-r33b-c0045037-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w20-r31-c0020283-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w4-r39b-c0045049-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w6-r34a-c0045035-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w7-r39d-c0045047-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w7-r39f-c0045061-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w8-r39c-c0045064-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t3600-w8-r39e-c0046587-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w1-r22-c0045016-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w1-r25-c0045044-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w1-r26-c0046164-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w10-r20-c0045047-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w10-r23-c0045046-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w10-r41c-c0056213-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w11-r32a-c0045036-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w11-r37a-c0045043-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w4-r18-c0045059-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w5-r21-c0046587-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w7-r33a-c0045033-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w8-r19-c0045017-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w8-r24-c0045015-start.json`
- `research/campaigns/2026-08-06-periodic-bb/certification/results/batches/selective-t600-w8-r41b-c0060702-start.json`

Persisted tasks outside completed batches: 379 (379368.5 CPU s); retained as evidence but not counted as completed-batch timeouts.

## Targets

| target | parameters | X | Z | overall | budgets (s) | new-task wall (s) | CPU (s) |
|---|---:|---|---|---|---:|---:|---:|
| c0000142 | [[208,52,2]] | exact | exact | exact | 5 | 8.9 | 8.5 |
| c0002359 | [[108,36,3]] | exact | exact | exact | 5 | 16.4 | 15.8 |
| c0004417 | [[452,228,2]] | exact | exact | exact | 5 | 154.4 | 151.4 |
| c0004584 | [[198,26,3]] | exact | exact | exact | 5,30 | 49.3 | 48.5 |
| c0006423 | [[234,78,3]] | exact | exact | exact | 5 | 59.6 | 58.6 |
| c0006625 | [[266,38,4]] | exact | exact | exact | 5,30 | 150.1 | 148.1 |
| c0010524 | [[270,18,9]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600,14400 | 34662.8 | 34240.1 |
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
| c0020118 | [[272,48,8]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600 | 39968.1 | 39462.8 |
| c0020168 | [[280,20,8]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600,14400 | 104233.2 | 102939.0 |
| c0020198 | [[238,46,6]] | exact | exact | exact | 5,30,120 | 3207.7 | 3168.2 |
| c0020283 | [[330,22,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600,14400 | 158160.8 | 156077.9 |
| c0020343 | [[252,48,6]] | exact | exact | exact | 5,30,120 | 3179.1 | 3136.9 |
| c0020418 | [[270,30,7]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600,14400 | 53967.7 | 53229.3 |
| c0020458 | [[240,30,6]] | exact | exact | exact | 5,30,120 | 1306.7 | 1289.3 |
| c0020498 | [[224,44,6]] | exact | exact | exact | 5,30,120 | 1911.4 | 1887.7 |
| c0020623 | [[260,26,6]] | exact | exact | exact | 5,30 | 178.0 | 175.8 |
| c0020718 | [[256,46,6]] | exact | exact | exact | 5,30,120 | 4119.5 | 4060.3 |
| c0020918 | [[234,26,7]] | exact | exact | exact | 5,30,120,600,3600 | 25452.4 | 25184.2 |
| c0020978 | [[266,50,6]] | exact | exact | exact | 5,30,120 | 3190.0 | 3148.6 |
| c0040000 | [[696,236,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,14400 | 82565.7 | 81915.1 |
| c0040001 | [[696,232,3]] | exact | exact | exact | 5,30,120 | 4767.6 | 4708.7 |
| c0040002 | [[696,236,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600 | 57561.9 | 56917.1 |
| c0040003 | [[690,234,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600 | 40542.9 | 40088.1 |
| c0040004 | [[672,228,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600 | 40950.3 | 40544.9 |
| c0040005 | [[696,174,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120 | 28911.2 | 28671.4 |
| c0040006 | [[688,172,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120 | 28405.8 | 28160.6 |
| c0040007 | [[680,170,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120 | 28448.2 | 28203.9 |
| c0045014 | [[690,46,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 38523.5 | 38222.3 |
| c0045015 | [[660,44,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 45855.6 | 45372.9 |
| c0045016 | [[600,40,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 34512.6 | 34002.1 |
| c0045017 | [[570,38,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 45681.2 | 45095.5 |
| c0045030 | [[464,72,8]] | timeout | timeout | timeout | 5,30,120,600 | 80646.5 | 79488.9 |
| c0045031 | [[448,70,8]] | timeout | timeout | timeout | 5,30,120,600 | 80752.8 | 79534.1 |
| c0045032 | [[432,68,8]] | timeout | timeout | timeout | 5,30,120,600 | 78527.1 | 77206.3 |
| c0045033 | [[416,66,8]] | timeout | timeout | timeout | 5,30,120,600 | 66517.3 | 65556.1 |
| c0045035 | [[384,62,8]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600 | 87904.2 | 86755.2 |
| c0045036 | [[368,60,8]] | timeout | timeout | timeout | 5,30,120,600 | 86557.1 | 85448.2 |
| c0045037 | [[352,58,8]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30,120,600,3600 | 72114.9 | 71180.9 |
| c0045041 | [[700,50,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 40210.2 | 39414.0 |
| c0045042 | [[672,48,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 38025.1 | 37698.0 |
| c0045043 | [[644,46,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 36749.8 | 36230.2 |
| c0045044 | [[616,44,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 34887.1 | 34376.4 |
| c0045046 | [[560,40,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 42996.9 | 42419.4 |
| c0045047 | [[532,38,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 99952.0 | 98935.5 |
| c0045048 | [[504,36,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 116967.9 | 115863.8 |
| c0045049 | [[476,34,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 58278.8 | 57673.5 |
| c0045059 | [[540,36,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 39224.3 | 38703.3 |
| c0045060 | [[510,34,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 27957.0 | 27603.8 |
| c0045061 | [[480,32,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 51367.0 | 50773.6 |
| c0045062 | [[450,30,9]] | exact | exact | exact | 5,30,120,600,3600 | 24273.1 | 23993.8 |
| c0045064 | [[390,26,9]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 88315.2 | 87531.1 |
| c0045088 | [[648,8,34]] | timeout | timeout | timeout | 5,30,120,600,3600 | 71355.0 | 70566.7 |
| c0045091 | [[576,12,28]] | timeout | timeout | timeout | 5,30,120 | 4731.8 | 4681.0 |
| c0045094 | [[504,8,28]] | timeout | timeout | timeout | 5,30,120 | 3580.4 | 3543.2 |
| c0045107 | [[576,24,12]] | timeout | timeout | timeout | 5,30,120 | 7433.5 | 7326.0 |
| c0045113 | [[432,24,12]] | timeout | timeout | timeout | 5,30,120 | 7704.3 | 7618.5 |
| c0045118 | [[630,8,30]] | timeout | timeout | timeout | 5,30,120 | 3734.6 | 3687.4 |
| c0045244 | [[648,4,34]] | timeout | timeout | timeout | 5,30,120,600,3600 | 35419.0 | 35125.1 |
| c0045426 | [[420,8,26]] | timeout | timeout | timeout | 5,30,120 | 2888.6 | 2853.2 |
| c0045508 | [[648,4,36]] | timeout | refuted | refuted | 5,30,120,600,3600 | 35517.3 | 35233.6 |
| c0045591 | [[448,56,8]] | timeout | timeout | timeout | 5,30,120,600 | 50921.8 | 50244.4 |
| c0046163 | [[644,46,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 36610.3 | 36282.8 |
| c0046164 | [[616,44,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600 | 34256.9 | 33759.1 |
| c0046282 | [[540,8,30]] | timeout | timeout | timeout | 5,30,120 | 3235.8 | 3205.7 |
| c0046378 | [[630,4,32]] | timeout | timeout | timeout | 5,30,120,600,3600 | 35425.7 | 35140.5 |
| c0046587 | [[532,38,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30,120,600,3600 | 96959.8 | 96015.0 |
| c0046841 | [[660,8,34]] | timeout | timeout | timeout | 5,30,120 | 3943.3 | 3912.1 |
| c0047091 | [[630,14,20]] | timeout | timeout | timeout | 5,30,120 | 5955.7 | 5908.5 |
| c0047122 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3182.0 | 3156.9 |
| c0048101 | [[660,8,34]] | timeout | timeout | timeout | 5,30,120 | 3829.5 | 3801.1 |
| c0048487 | [[686,6,36]] | timeout | timeout | timeout | 5,30,120,600,3600 | 54048.6 | 53428.7 |
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
| c0050584 | [[630,8,34]] | timeout | timeout | timeout | 5,30,120,600,3600 | 71372.2 | 70560.5 |
| c0050641 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120 | 6222.8 | 6165.5 |
| c0050670 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3241.4 | 3213.0 |
| c0050719 | [[660,8,28]] | timeout | timeout | timeout | 5,30,120 | 3271.5 | 3244.5 |
| c0051753 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3783.5 | 3754.4 |
| c0051763 | [[540,8,26]] | timeout | timeout | timeout | 5,30,120 | 3071.9 | 3046.9 |
| c0051880 | [[648,4,38]] | timeout | timeout | timeout | 5,30,120,600,3600 | 35580.5 | 35294.4 |
| c0051899 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3692.9 | 3662.5 |
| c0052765 | [[648,8,30]] | timeout | timeout | timeout | 5,30,120 | 3673.9 | 3641.6 |
| c0052988 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120 | 6144.1 | 6079.9 |
| c0054814 | [[686,6,28]] | timeout | refuted | refuted | 5,30,120 | 2046.8 | 2023.9 |
| c0054828 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3827.5 | 3794.6 |
| c0054859 | [[686,6,36]] | timeout | timeout | timeout | 5,30,120,600,3600 | 53977.9 | 53343.5 |
| c0054911 | [[630,8,28]] | timeout | timeout | timeout | 5,30,120 | 3907.0 | 3871.0 |
| c0055020 | [[648,8,28]] | timeout | timeout | timeout | 5,30,120 | 3866.8 | 3830.1 |
| c0055406 | [[630,4,36]] | timeout | timeout | timeout | 5,30,120,600,3600 | 35554.3 | 35283.8 |
| c0056213 | [[576,12,30]] | timeout | timeout | timeout | 5,30,120 | 5913.1 | 5864.7 |
| c0056263 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3218.0 | 3191.1 |
| c0056884 | [[686,12,28]] | timeout | refuted | refuted | 5,30,120 | 4462.2 | 4428.4 |
| c0057634 | [[686,12,30]] | refuted | timeout | refuted | 5,30,120 | 4876.1 | 4839.9 |
| c0057792 | [[540,8,28]] | timeout | timeout | timeout | 5,30,120 | 3084.8 | 3058.0 |
| c0058472 | [[648,8,30]] | timeout | timeout | timeout | 5,30,120 | 3734.6 | 3702.8 |
| c0058579 | [[686,18,24]] | timeout | timeout | timeout | 5,30,120 | 8892.8 | 8821.7 |
| c0058638 | [[648,8,32]] | timeout | timeout | timeout | 5,30,120 | 3842.1 | 3811.8 |
| c0059571 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120 | 6096.9 | 6042.5 |
| c0060611 | [[630,10,28]] | timeout | refuted | refuted | 5,30,120 | 3615.9 | 3586.0 |
| c0060702 | [[630,14,28]] | timeout | timeout | timeout | 5,30,120,600 | 16546.2 | 16425.2 |
| c0060754 | [[576,16,20]] | timeout | timeout | timeout | 5,30,120 | 6792.7 | 6738.5 |
| c0060824 | [[660,8,32]] | timeout | timeout | timeout | 5,30,120 | 3781.4 | 3752.1 |
| c0060866 | [[648,8,32]] | timeout | timeout | timeout | 5,30,120 | 3847.1 | 3819.0 |
| c0061526 | [[648,8,32]] | timeout | timeout | timeout | 5,30,120 | 3869.6 | 3842.0 |
| c0062627 | [[630,14,28]] | timeout | timeout | timeout | 5,30,120 | 5908.8 | 5873.2 |
| c0063118 | [[648,8,34]] | timeout | timeout | timeout | 5,30,120 | 3455.9 | 3440.2 |
