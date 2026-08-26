# Periodic BB exact-certification summary

Targets: 128; exact: 6; refuted: 5; sharded closed pending serial: 6; timeout: 111; pending: 0.

Non-overlapping batch wall time: 4841.8 s; summed new-task wall time: 297105.0 s; summed new-task CPU time: 294186.1 s.

A side marked `sharded_closed_pending_serial` has all logical-row cutoff MILPs proven infeasible, but the candidate is `exact` only after a hash-matched, persisted stock `verify/certify.py` result has `d_exact: true`.

## Completed batches

| stage | budget (s) | workers | candidates | new tasks | inherited | wall (s) | new-task CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| priority-t5-w32 | 5 | 32 | 10 | 288 | 0 | 144.5 | 4419.3 |
| all-t5-w64 | 5 | 64 | 128 | 10520 | 20 | 829.2 | 51244.1 |
| all-t30-w64 | 30 | 64 | 128 | 7218 | 3322 | 3868.1 | 238522.7 |

## Targets

| target | parameters | X | Z | overall | budgets (s) | new-task wall (s) | CPU (s) |
|---|---:|---|---|---|---:|---:|---:|
| c0000142 | [[208,52,2]] | exact | exact | exact | 5 | 8.9 | 8.5 |
| c0002359 | [[108,36,3]] | exact | exact | exact | 5 | 16.4 | 15.8 |
| c0004417 | [[452,228,2]] | exact | exact | exact | 5 | 154.4 | 151.4 |
| c0004584 | [[198,26,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30 | 49.3 | 48.5 |
| c0006423 | [[234,78,3]] | exact | exact | exact | 5 | 59.6 | 58.6 |
| c0006625 | [[266,38,4]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30 | 150.1 | 148.1 |
| c0010524 | [[270,18,9]] | timeout | timeout | timeout | 5,30 | 1084.0 | 1070.2 |
| c0011462 | [[270,90,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30 | 459.7 | 452.8 |
| c0012783 | [[224,112,2]] | exact | exact | exact | 5 | 3.7 | 3.4 |
| c0014474 | [[396,136,3]] | timeout | timeout | timeout | 5,30 | 4122.9 | 4086.4 |
| c0016039 | [[288,96,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30 | 527.1 | 520.6 |
| c0016229 | [[208,26,6]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 505.3 | 499.3 |
| c0016394 | [[288,100,3]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30 | 491.0 | 483.8 |
| c0018628 | [[280,20,7]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 775.4 | 764.1 |
| c0019513 | [[384,96,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 1372.9 | 1352.5 |
| c0019531 | [[248,62,4]] | exact | exact | exact | 5 | 20.2 | 19.5 |
| c0020058 | [[304,52,7]] | timeout | timeout | timeout | 5,30 | 3621.5 | 3572.5 |
| c0020118 | [[272,48,8]] | timeout | timeout | timeout | 5,30 | 3372.8 | 3329.5 |
| c0020168 | [[280,20,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 922.1 | 912.7 |
| c0020198 | [[238,46,6]] | timeout | timeout | timeout | 5,30 | 2207.5 | 2181.1 |
| c0020283 | [[330,22,9]] | timeout | timeout | timeout | 5,30 | 1574.9 | 1560.1 |
| c0020343 | [[252,48,6]] | timeout | timeout | timeout | 5,30 | 2217.4 | 2187.3 |
| c0020418 | [[270,30,7]] | timeout | timeout | timeout | 5,30 | 1547.6 | 1526.7 |
| c0020458 | [[240,30,6]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 590.3 | 582.3 |
| c0020498 | [[224,44,6]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 1627.7 | 1607.6 |
| c0020623 | [[260,26,6]] | sharded_closed_pending_serial | sharded_closed_pending_serial | sharded_closed_pending_serial | 5,30 | 178.0 | 175.8 |
| c0020718 | [[256,46,6]] | timeout | timeout | timeout | 5,30 | 2378.5 | 2341.2 |
| c0020918 | [[234,26,7]] | timeout | timeout | timeout | 5,30 | 1331.4 | 1312.7 |
| c0020978 | [[266,50,6]] | timeout | timeout | timeout | 5,30 | 2085.2 | 2057.5 |
| c0040000 | [[696,236,3]] | timeout | timeout | timeout | 5,30 | 16679.0 | 16521.3 |
| c0040001 | [[696,232,3]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 4319.4 | 4263.8 |
| c0040002 | [[696,236,3]] | timeout | timeout | timeout | 5,30 | 10447.5 | 10336.0 |
| c0040003 | [[690,234,3]] | timeout | timeout | timeout | 5,30 | 11295.1 | 11155.4 |
| c0040004 | [[672,228,3]] | timeout | timeout | timeout | 5,30 | 10995.3 | 10879.2 |
| c0040005 | [[696,174,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 7119.2 | 7058.6 |
| c0040006 | [[688,172,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 6875.1 | 6815.5 |
| c0040007 | [[680,170,4]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 7125.3 | 7054.1 |
| c0045014 | [[690,46,9]] | timeout | timeout | timeout | 5,30 | 3248.8 | 3209.9 |
| c0045015 | [[660,44,9]] | timeout | timeout | timeout | 5,30 | 2827.8 | 2797.5 |
| c0045016 | [[600,40,9]] | timeout | timeout | timeout | 5,30 | 3059.7 | 3023.1 |
| c0045017 | [[570,38,9]] | timeout | timeout | timeout | 5,30 | 2493.7 | 2466.7 |
| c0045030 | [[464,72,8]] | timeout | timeout | timeout | 5,30 | 5068.3 | 5017.3 |
| c0045031 | [[448,70,8]] | timeout | timeout | timeout | 5,30 | 5072.8 | 5023.6 |
| c0045032 | [[432,68,8]] | timeout | timeout | timeout | 5,30 | 4895.3 | 4842.7 |
| c0045033 | [[416,66,8]] | timeout | timeout | timeout | 5,30 | 4639.6 | 4590.7 |
| c0045035 | [[384,62,8]] | timeout | timeout | timeout | 5,30 | 4360.8 | 4315.3 |
| c0045036 | [[368,60,8]] | timeout | timeout | timeout | 5,30 | 4224.3 | 4182.7 |
| c0045037 | [[352,58,8]] | timeout | timeout | timeout | 5,30 | 4075.6 | 4031.6 |
| c0045041 | [[700,50,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 3055.3 | 3026.0 |
| c0045042 | [[672,48,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 2583.2 | 2560.3 |
| c0045043 | [[644,46,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 2561.1 | 2536.7 |
| c0045044 | [[616,44,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 2017.4 | 1998.2 |
| c0045046 | [[560,40,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 1790.0 | 1775.4 |
| c0045047 | [[532,38,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 1720.9 | 1703.7 |
| c0045048 | [[504,36,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 2138.5 | 2119.7 |
| c0045049 | [[476,34,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 1942.5 | 1926.4 |
| c0045059 | [[540,36,9]] | timeout | timeout | timeout | 5,30 | 2328.3 | 2302.2 |
| c0045060 | [[510,34,9]] | timeout | timeout | timeout | 5,30 | 2460.9 | 2436.3 |
| c0045061 | [[480,32,9]] | timeout | timeout | timeout | 5,30 | 2212.9 | 2190.6 |
| c0045062 | [[450,30,9]] | timeout | timeout | timeout | 5,30 | 1997.4 | 1978.9 |
| c0045064 | [[390,26,9]] | timeout | timeout | timeout | 5,30 | 1676.0 | 1658.1 |
| c0045088 | [[648,8,34]] | timeout | timeout | timeout | 5,30 | 1882.6 | 1863.3 |
| c0045091 | [[576,12,28]] | timeout | timeout | timeout | 5,30 | 1722.3 | 1706.9 |
| c0045094 | [[504,8,28]] | timeout | timeout | timeout | 5,30 | 1568.3 | 1553.2 |
| c0045107 | [[576,24,12]] | timeout | timeout | timeout | 5,30 | 1778.7 | 1759.5 |
| c0045113 | [[432,24,12]] | timeout | timeout | timeout | 5,30 | 1938.1 | 1915.6 |
| c0045118 | [[630,8,30]] | timeout | timeout | timeout | 5,30 | 1796.9 | 1777.8 |
| c0045244 | [[648,4,34]] | timeout | timeout | timeout | 5,30 | 800.4 | 793.3 |
| c0045426 | [[420,8,26]] | timeout | timeout | timeout | 5,30 | 967.0 | 956.8 |
| c0045508 | [[648,4,36]] | timeout | timeout | timeout | 5,30 | 861.5 | 852.8 |
| c0045591 | [[448,56,8]] | timeout | timeout | timeout | 5,30 | 3967.6 | 3912.1 |
| c0046163 | [[644,46,8]] | timeout | timeout | timeout | 5,30 | 2830.4 | 2800.8 |
| c0046164 | [[616,44,8]] | sharded_closed_pending_serial | timeout | timeout | 5,30 | 2189.1 | 2159.5 |
| c0046282 | [[540,8,30]] | timeout | timeout | timeout | 5,30 | 1158.4 | 1147.5 |
| c0046378 | [[630,4,32]] | timeout | timeout | timeout | 5,30 | 729.4 | 723.3 |
| c0046587 | [[532,38,8]] | timeout | timeout | timeout | 5,30 | 2338.8 | 2313.9 |
| c0046841 | [[660,8,34]] | timeout | timeout | timeout | 5,30 | 1974.9 | 1958.6 |
| c0047091 | [[630,14,20]] | timeout | timeout | timeout | 5,30 | 2202.3 | 2184.6 |
| c0047122 | [[540,8,28]] | timeout | timeout | timeout | 5,30 | 1239.1 | 1229.3 |
| c0048101 | [[660,8,34]] | timeout | timeout | timeout | 5,30 | 1886.1 | 1871.8 |
| c0048487 | [[686,6,36]] | timeout | timeout | timeout | 5,30 | 1835.9 | 1820.3 |
| c0048911 | [[630,8,28]] | timeout | timeout | timeout | 5,30 | 1457.9 | 1448.6 |
| c0049220 | [[648,4,38]] | refuted | timeout | refuted | 5,30 | 801.2 | 793.3 |
| c0049291 | [[660,8,28]] | timeout | timeout | timeout | 5,30 | 1783.6 | 1769.1 |
| c0049482 | [[540,8,26]] | timeout | timeout | timeout | 5,30 | 1139.3 | 1129.5 |
| c0049503 | [[648,8,30]] | timeout | timeout | timeout | 5,30 | 1841.7 | 1825.7 |
| c0049506 | [[540,8,30]] | timeout | timeout | timeout | 5,30 | 1092.1 | 1083.4 |
| c0049780 | [[630,8,30]] | timeout | timeout | timeout | 5,30 | 1581.0 | 1567.9 |
| c0049795 | [[600,8,26]] | timeout | timeout | timeout | 5,30 | 1318.5 | 1307.6 |
| c0049803 | [[648,8,28]] | timeout | timeout | timeout | 5,30 | 1636.3 | 1625.1 |
| c0049926 | [[540,8,28]] | timeout | timeout | timeout | 5,30 | 1212.8 | 1203.3 |
| c0050011 | [[660,8,28]] | timeout | timeout | timeout | 5,30 | 1823.9 | 1805.4 |
| c0050071 | [[660,8,28]] | timeout | timeout | timeout | 5,30 | 1578.5 | 1565.9 |
| c0050292 | [[576,8,30]] | timeout | timeout | timeout | 5,30 | 1265.0 | 1255.4 |
| c0050526 | [[540,8,30]] | timeout | timeout | timeout | 5,30 | 1043.6 | 1035.8 |
| c0050584 | [[630,8,34]] | timeout | timeout | timeout | 5,30 | 1924.1 | 1906.5 |
| c0050641 | [[576,16,20]] | timeout | timeout | timeout | 5,30 | 2205.6 | 2189.5 |
| c0050670 | [[540,8,28]] | timeout | timeout | timeout | 5,30 | 1284.5 | 1275.2 |
| c0050719 | [[660,8,28]] | timeout | timeout | timeout | 5,30 | 1280.0 | 1270.6 |
| c0051753 | [[660,8,32]] | timeout | timeout | timeout | 5,30 | 1767.1 | 1754.8 |
| c0051763 | [[540,8,26]] | timeout | timeout | timeout | 5,30 | 993.5 | 986.5 |
| c0051880 | [[648,4,38]] | timeout | timeout | timeout | 5,30 | 927.1 | 920.2 |
| c0051899 | [[660,8,32]] | timeout | timeout | timeout | 5,30 | 1667.0 | 1652.8 |
| c0052765 | [[648,8,30]] | timeout | timeout | timeout | 5,30 | 1701.5 | 1688.8 |
| c0052988 | [[576,16,20]] | timeout | timeout | timeout | 5,30 | 2226.3 | 2207.2 |
| c0054814 | [[686,6,28]] | timeout | refuted | refuted | 5,30 | 953.2 | 944.2 |
| c0054828 | [[660,8,32]] | timeout | timeout | timeout | 5,30 | 1834.0 | 1821.5 |
| c0054859 | [[686,6,36]] | timeout | timeout | timeout | 5,30 | 1755.6 | 1741.4 |
| c0054911 | [[630,8,28]] | timeout | timeout | timeout | 5,30 | 1612.3 | 1598.7 |
| c0055020 | [[648,8,28]] | timeout | timeout | timeout | 5,30 | 1773.3 | 1758.5 |
| c0055406 | [[630,4,36]] | timeout | timeout | timeout | 5,30 | 840.4 | 834.3 |
| c0056213 | [[576,12,30]] | timeout | timeout | timeout | 5,30 | 2903.5 | 2883.9 |
| c0056263 | [[540,8,28]] | timeout | timeout | timeout | 5,30 | 1210.0 | 1200.3 |
| c0056884 | [[686,12,28]] | timeout | refuted | refuted | 5,30 | 2245.2 | 2228.1 |
| c0057634 | [[686,12,30]] | refuted | timeout | refuted | 5,30 | 2466.0 | 2448.6 |
| c0057792 | [[540,8,28]] | timeout | timeout | timeout | 5,30 | 1015.6 | 1005.8 |
| c0058472 | [[648,8,30]] | timeout | timeout | timeout | 5,30 | 1789.1 | 1774.5 |
| c0058579 | [[686,18,24]] | timeout | timeout | timeout | 5,30 | 4258.0 | 4230.1 |
| c0058638 | [[648,8,32]] | timeout | timeout | timeout | 5,30 | 1890.0 | 1876.8 |
| c0059571 | [[576,16,20]] | timeout | timeout | timeout | 5,30 | 2224.9 | 2205.9 |
| c0060611 | [[630,10,28]] | timeout | refuted | refuted | 5,30 | 1543.5 | 1530.4 |
| c0060702 | [[630,14,28]] | timeout | timeout | timeout | 5,30 | 2762.9 | 2744.6 |
| c0060754 | [[576,16,20]] | timeout | timeout | timeout | 5,30 | 2882.9 | 2862.6 |
| c0060824 | [[660,8,32]] | timeout | timeout | timeout | 5,30 | 1791.7 | 1776.8 |
| c0060866 | [[648,8,32]] | timeout | timeout | timeout | 5,30 | 1793.8 | 1781.9 |
| c0061526 | [[648,8,32]] | timeout | timeout | timeout | 5,30 | 1781.3 | 1767.6 |
| c0062627 | [[630,14,28]] | timeout | timeout | timeout | 5,30 | 2364.0 | 2347.9 |
| c0063118 | [[648,8,34]] | timeout | timeout | timeout | 5,30 | 1431.1 | 1424.2 |
