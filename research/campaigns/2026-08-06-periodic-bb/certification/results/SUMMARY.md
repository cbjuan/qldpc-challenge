# Periodic BB exact-certification summary

Targets: 128; exact: 6; refuted: 5; sharded closed pending serial: 0; timeout: 117; pending: 0.

Non-overlapping batch wall time: 973.7 s; summed new-task wall time: 56317.7 s; summed new-task CPU time: 55663.4 s.

A side marked `sharded_closed_pending_serial` has all logical-row cutoff MILPs proven infeasible, but the candidate is `exact` only after a hash-matched, persisted stock `verify/certify.py` result has `d_exact: true`.

## Completed batches

| stage | budget (s) | workers | candidates | new tasks | inherited | wall (s) | new-task CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| priority-t5-w32 | 5 | 32 | 10 | 288 | 0 | 144.5 | 4419.3 |
| all-t5-w64 | 5 | 64 | 128 | 10520 | 20 | 829.2 | 51244.1 |

## Targets

| target | parameters | X | Z | overall | budgets (s) | new-task wall (s) | CPU (s) |
|---|---:|---|---|---|---:|---:|---:|
| c0000142 | [[208,52,2]] | exact | exact | exact | 5 | 8.9 | 8.5 |
| c0002359 | [[108,36,3]] | exact | exact | exact | 5 | 16.4 | 15.8 |
| c0004417 | [[452,228,2]] | exact | exact | exact | 5 | 154.4 | 151.4 |
| c0004584 | [[198,26,3]] | sharded_closed_pending_serial | timeout | timeout | 5 | 43.7 | 42.9 |
| c0006423 | [[234,78,3]] | exact | exact | exact | 5 | 59.6 | 58.6 |
| c0006625 | [[266,38,4]] | sharded_closed_pending_serial | timeout | timeout | 5 | 111.7 | 109.9 |
| c0010524 | [[270,18,9]] | timeout | timeout | timeout | 5 | 186.3 | 183.9 |
| c0011462 | [[270,90,3]] | timeout | timeout | timeout | 5 | 306.2 | 301.7 |
| c0012783 | [[224,112,2]] | exact | exact | exact | 5 | 3.7 | 3.4 |
| c0014474 | [[396,136,3]] | timeout | timeout | timeout | 5 | 1130.5 | 1121.5 |
| c0016039 | [[288,96,3]] | timeout | timeout | timeout | 5 | 390.9 | 386.0 |
| c0016229 | [[208,26,6]] | sharded_closed_pending_serial | timeout | timeout | 5 | 114.9 | 113.4 |
| c0016394 | [[288,100,3]] | timeout | timeout | timeout | 5 | 300.5 | 295.7 |
| c0018628 | [[280,20,7]] | timeout | timeout | timeout | 5 | 150.1 | 147.6 |
| c0019513 | [[384,96,4]] | sharded_closed_pending_serial | timeout | timeout | 5 | 401.4 | 395.0 |
| c0019531 | [[248,62,4]] | exact | exact | exact | 5 | 20.2 | 19.5 |
| c0020058 | [[304,52,7]] | timeout | timeout | timeout | 5 | 527.0 | 521.1 |
| c0020118 | [[272,48,8]] | timeout | timeout | timeout | 5 | 489.5 | 485.5 |
| c0020168 | [[280,20,8]] | timeout | timeout | timeout | 5 | 285.1 | 283.0 |
| c0020198 | [[238,46,6]] | timeout | timeout | timeout | 5 | 463.9 | 459.7 |
| c0020283 | [[330,22,9]] | timeout | timeout | timeout | 5 | 439.8 | 436.6 |
| c0020343 | [[252,48,6]] | timeout | timeout | timeout | 5 | 486.0 | 481.9 |
| c0020418 | [[270,30,7]] | timeout | timeout | timeout | 5 | 282.7 | 280.0 |
| c0020458 | [[240,30,6]] | sharded_closed_pending_serial | timeout | timeout | 5 | 139.7 | 138.4 |
| c0020498 | [[224,44,6]] | timeout | timeout | timeout | 5 | 440.3 | 436.0 |
| c0020623 | [[260,26,6]] | sharded_closed_pending_serial | timeout | timeout | 5 | 87.3 | 86.3 |
| c0020718 | [[256,46,6]] | timeout | timeout | timeout | 5 | 464.9 | 457.7 |
| c0020918 | [[234,26,7]] | timeout | timeout | timeout | 5 | 249.6 | 244.5 |
| c0020978 | [[266,50,6]] | timeout | timeout | timeout | 5 | 498.0 | 489.6 |
| c0040000 | [[696,236,3]] | timeout | timeout | timeout | 5 | 2618.7 | 2584.0 |
| c0040001 | [[696,232,3]] | timeout | timeout | timeout | 5 | 1884.6 | 1851.7 |
| c0040002 | [[696,236,3]] | timeout | timeout | timeout | 5 | 2329.7 | 2287.3 |
| c0040003 | [[690,234,3]] | timeout | timeout | timeout | 5 | 2293.7 | 2240.4 |
| c0040004 | [[672,228,3]] | timeout | timeout | timeout | 5 | 2238.5 | 2204.0 |
| c0040005 | [[696,174,4]] | timeout | timeout | timeout | 5 | 1315.7 | 1300.6 |
| c0040006 | [[688,172,4]] | timeout | timeout | timeout | 5 | 1229.4 | 1217.2 |
| c0040007 | [[680,170,4]] | timeout | timeout | timeout | 5 | 1242.3 | 1225.1 |
| c0045014 | [[690,46,9]] | timeout | timeout | timeout | 5 | 509.3 | 500.4 |
| c0045015 | [[660,44,9]] | timeout | timeout | timeout | 5 | 464.3 | 458.8 |
| c0045016 | [[600,40,9]] | timeout | timeout | timeout | 5 | 426.8 | 421.7 |
| c0045017 | [[570,38,9]] | timeout | timeout | timeout | 5 | 397.0 | 393.4 |
| c0045030 | [[464,72,8]] | timeout | timeout | timeout | 5 | 737.6 | 731.2 |
| c0045031 | [[448,70,8]] | timeout | timeout | timeout | 5 | 849.8 | 840.1 |
| c0045032 | [[432,68,8]] | timeout | timeout | timeout | 5 | 794.3 | 783.2 |
| c0045033 | [[416,66,8]] | timeout | timeout | timeout | 5 | 672.9 | 666.6 |
| c0045035 | [[384,62,8]] | timeout | timeout | timeout | 5 | 635.2 | 629.4 |
| c0045036 | [[368,60,8]] | timeout | timeout | timeout | 5 | 617.9 | 612.6 |
| c0045037 | [[352,58,8]] | timeout | timeout | timeout | 5 | 590.2 | 584.5 |
| c0045041 | [[700,50,8]] | timeout | timeout | timeout | 5 | 479.9 | 472.7 |
| c0045042 | [[672,48,8]] | timeout | timeout | timeout | 5 | 445.8 | 439.3 |
| c0045043 | [[644,46,8]] | timeout | timeout | timeout | 5 | 426.5 | 421.2 |
| c0045044 | [[616,44,8]] | timeout | timeout | timeout | 5 | 391.1 | 387.4 |
| c0045046 | [[560,40,8]] | timeout | timeout | timeout | 5 | 348.4 | 344.3 |
| c0045047 | [[532,38,8]] | timeout | timeout | timeout | 5 | 345.4 | 342.0 |
| c0045048 | [[504,36,8]] | timeout | timeout | timeout | 5 | 775.1 | 767.6 |
| c0045049 | [[476,34,8]] | timeout | timeout | timeout | 5 | 696.6 | 691.1 |
| c0045059 | [[540,36,9]] | timeout | timeout | timeout | 5 | 404.7 | 399.9 |
| c0045060 | [[510,34,9]] | timeout | timeout | timeout | 5 | 500.9 | 494.2 |
| c0045061 | [[480,32,9]] | timeout | timeout | timeout | 5 | 433.7 | 429.1 |
| c0045062 | [[450,30,9]] | timeout | timeout | timeout | 5 | 391.5 | 387.2 |
| c0045064 | [[390,26,9]] | timeout | timeout | timeout | 5 | 302.3 | 299.1 |
| c0045088 | [[648,8,34]] | timeout | timeout | timeout | 5 | 86.3 | 85.6 |
| c0045091 | [[576,12,28]] | timeout | timeout | timeout | 5 | 557.5 | 552.5 |
| c0045094 | [[504,8,28]] | timeout | timeout | timeout | 5 | 788.1 | 782.9 |
| c0045107 | [[576,24,12]] | timeout | timeout | timeout | 5 | 303.3 | 300.7 |
| c0045113 | [[432,24,12]] | timeout | timeout | timeout | 5 | 496.1 | 492.6 |
| c0045118 | [[630,8,30]] | timeout | timeout | timeout | 5 | 93.4 | 92.9 |
| c0045244 | [[648,4,34]] | timeout | timeout | timeout | 5 | 198.1 | 196.7 |
| c0045426 | [[420,8,26]] | timeout | timeout | timeout | 5 | 451.3 | 447.3 |
| c0045508 | [[648,4,36]] | timeout | timeout | timeout | 5 | 44.9 | 44.7 |
| c0045591 | [[448,56,8]] | timeout | timeout | timeout | 5 | 577.5 | 570.3 |
| c0046163 | [[644,46,8]] | timeout | timeout | timeout | 5 | 493.7 | 488.4 |
| c0046164 | [[616,44,8]] | timeout | timeout | timeout | 5 | 457.3 | 448.1 |
| c0046282 | [[540,8,30]] | timeout | timeout | timeout | 5 | 87.3 | 85.7 |
| c0046378 | [[630,4,32]] | timeout | timeout | timeout | 5 | 44.4 | 43.5 |
| c0046587 | [[532,38,8]] | timeout | timeout | timeout | 5 | 399.0 | 393.9 |
| c0046841 | [[660,8,34]] | timeout | timeout | timeout | 5 | 90.5 | 89.6 |
| c0047091 | [[630,14,20]] | timeout | timeout | timeout | 5 | 157.1 | 154.8 |
| c0047122 | [[540,8,28]] | timeout | timeout | timeout | 5 | 351.4 | 348.9 |
| c0048101 | [[660,8,34]] | timeout | timeout | timeout | 5 | 90.1 | 89.1 |
| c0048487 | [[686,6,36]] | timeout | timeout | timeout | 5 | 141.7 | 141.0 |
| c0048911 | [[630,8,28]] | timeout | timeout | timeout | 5 | 87.0 | 86.0 |
| c0049220 | [[648,4,38]] | refuted | timeout | refuted | 5 | 248.5 | 247.0 |
| c0049291 | [[660,8,28]] | timeout | timeout | timeout | 5 | 87.9 | 87.1 |
| c0049482 | [[540,8,26]] | timeout | timeout | timeout | 5 | 366.3 | 361.8 |
| c0049503 | [[648,8,30]] | timeout | timeout | timeout | 5 | 86.5 | 85.0 |
| c0049506 | [[540,8,30]] | timeout | timeout | timeout | 5 | 87.2 | 86.3 |
| c0049780 | [[630,8,30]] | timeout | timeout | timeout | 5 | 91.9 | 90.6 |
| c0049795 | [[600,8,26]] | timeout | timeout | timeout | 5 | 86.0 | 84.9 |
| c0049803 | [[648,8,28]] | timeout | timeout | timeout | 5 | 86.0 | 84.9 |
| c0049926 | [[540,8,28]] | timeout | timeout | timeout | 5 | 392.2 | 388.5 |
| c0050011 | [[660,8,28]] | timeout | timeout | timeout | 5 | 93.5 | 92.2 |
| c0050071 | [[660,8,28]] | timeout | timeout | timeout | 5 | 90.8 | 89.4 |
| c0050292 | [[576,8,30]] | timeout | timeout | timeout | 5 | 93.0 | 91.9 |
| c0050526 | [[540,8,30]] | timeout | timeout | timeout | 5 | 88.0 | 86.6 |
| c0050584 | [[630,8,34]] | timeout | timeout | timeout | 5 | 185.9 | 185.0 |
| c0050641 | [[576,16,20]] | timeout | timeout | timeout | 5 | 680.0 | 674.4 |
| c0050670 | [[540,8,28]] | timeout | timeout | timeout | 5 | 367.5 | 365.3 |
| c0050719 | [[660,8,28]] | timeout | timeout | timeout | 5 | 241.0 | 239.1 |
| c0051753 | [[660,8,32]] | timeout | timeout | timeout | 5 | 89.5 | 88.9 |
| c0051763 | [[540,8,26]] | timeout | timeout | timeout | 5 | 140.4 | 139.1 |
| c0051880 | [[648,4,38]] | timeout | timeout | timeout | 5 | 43.1 | 42.6 |
| c0051899 | [[660,8,32]] | timeout | timeout | timeout | 5 | 92.1 | 90.5 |
| c0052765 | [[648,8,30]] | timeout | timeout | timeout | 5 | 87.7 | 86.7 |
| c0052988 | [[576,16,20]] | timeout | timeout | timeout | 5 | 730.8 | 722.7 |
| c0054814 | [[686,6,28]] | timeout | refuted | refuted | 5 | 195.3 | 192.8 |
| c0054828 | [[660,8,32]] | timeout | timeout | timeout | 5 | 87.8 | 87.3 |
| c0054859 | [[686,6,36]] | timeout | timeout | timeout | 5 | 76.6 | 75.9 |
| c0054911 | [[630,8,28]] | timeout | timeout | timeout | 5 | 89.7 | 88.6 |
| c0055020 | [[648,8,28]] | timeout | timeout | timeout | 5 | 498.4 | 493.0 |
| c0055406 | [[630,4,36]] | timeout | timeout | timeout | 5 | 44.7 | 44.2 |
| c0056213 | [[576,12,30]] | timeout | timeout | timeout | 5 | 1506.8 | 1498.5 |
| c0056263 | [[540,8,28]] | timeout | timeout | timeout | 5 | 368.9 | 366.0 |
| c0056884 | [[686,12,28]] | timeout | refuted | refuted | 5 | 427.3 | 424.5 |
| c0057634 | [[686,12,30]] | refuted | timeout | refuted | 5 | 482.8 | 479.0 |
| c0057792 | [[540,8,28]] | timeout | timeout | timeout | 5 | 89.1 | 87.9 |
| c0058472 | [[648,8,30]] | timeout | timeout | timeout | 5 | 90.4 | 89.5 |
| c0058579 | [[686,18,24]] | timeout | timeout | timeout | 5 | 1843.4 | 1834.5 |
| c0058638 | [[648,8,32]] | timeout | timeout | timeout | 5 | 89.2 | 88.7 |
| c0059571 | [[576,16,20]] | timeout | timeout | timeout | 5 | 1125.7 | 1117.8 |
| c0060611 | [[630,10,28]] | timeout | refuted | refuted | 5 | 419.6 | 416.7 |
| c0060702 | [[630,14,28]] | timeout | timeout | timeout | 5 | 316.2 | 314.2 |
| c0060754 | [[576,16,20]] | timeout | timeout | timeout | 5 | 1448.2 | 1439.4 |
| c0060824 | [[660,8,32]] | timeout | timeout | timeout | 5 | 92.0 | 90.8 |
| c0060866 | [[648,8,32]] | timeout | timeout | timeout | 5 | 91.5 | 90.4 |
| c0061526 | [[648,8,32]] | timeout | timeout | timeout | 5 | 93.5 | 92.5 |
| c0062627 | [[630,14,28]] | timeout | timeout | timeout | 5 | 157.2 | 155.4 |
| c0063118 | [[648,8,34]] | timeout | timeout | timeout | 5 | 88.5 | 87.8 |
