# Local findings ledger

All entries remain local and unsubmitted. `passed` means the trusted local
validator accepted the candidate and did not refute its witness-backed upper
bound. Literature novelty is unverified.

| Candidate | Check weight | Gate | Board status | Artifact |
|---|---:|---|---|---|
| `[[270,18,9]]` | 6 | passed after flat 2k→8k→60k ladder | advances weight-6 × unrestricted; FOM 5.40 | `artifacts/candidates/c0010524-88d55b4bd0-60k-python8000-s852276647-fast60000.json` |
| `[[280,20,7]]` | 6 | passed after flat 2k→8k→60k ladder | advances weight-6 × unrestricted; FOM 3.50 | `artifacts/candidates/c0018628-a16cd470e9-60k-python8000-s1424024388-fast60000.json` |
| `[[208,26,6]]` | 6 | passed after flat 2k→8k→60k ladder | advances weight-6 × unrestricted | `artifacts/candidates/c0016229-34ddd89e34-60k-python8000-s730123194-fast60000.json` |
| `[[248,62,4]]` | 6 | passed after flat 2k→8k→60k ladder | advances weight-6 × unrestricted | `artifacts/candidates/c0019531-4fba9c6576-60k-python8000-s172055528-fast60000.json` |
| `[[266,38,4]]` | 6 | passed after flat 2k→8k→60k ladder | advances weight-6 × unrestricted | `artifacts/candidates/c0006625-3fadd04521-60k-python8000-s572072710-fast60000.json` |
| `[[198,26,3]]` | 6 | passed at 2k | advances weight-6 × unrestricted | `artifacts/candidates/c0004584-ff039c096b-python2000-s1431612151.json` |
| `[[208,52,2]]` | 6 | passed at 2k | advances weight-6 × unrestricted | `artifacts/candidates/c0000142-fac92a1832-python2000-s1512128256.json` |
| `[[108,36,3]]` | 16 | passed | advances weight-9plus × unrestricted | `artifacts/candidates/c0002359-0daec5be0e-python2000-s1571305854.json` |
| `[[224,112,2]]` | 6 | passed | advances weight-6 × unrestricted | `artifacts/candidates/c0012783-4b63b4ed57-python2000-s1744585393.json` |
| `[[452,228,2]]` | 8 | passed | advances weight-8 × unrestricted | `artifacts/candidates/c0004417-e3a2cafb05-python2000-s1815568102.json` |
| `[[40,2,4]]` | 4 | passed | dominated; retained as calibration | `artifacts/candidates/c0008081-a7602f8560-python2000-s1872254395.json` |

The adjacent `*.verdict.json` files contain the full validator evidence. The
continuous search does not stop at any entry in this table.

The shallow `[[288,50,8]]` candidate with FOM 11.11 was rejected as an exact
duplicate of the existing board entry and is retained only as a regression
artifact.
