# V30.1 Candidate Acceptance Matrix

| Area | Candidate behavior | Evidence | State |
|---|---|---|---|
| Compact prefixes | Longest configured prefix without mandatory hyphen | Unit test | Implemented candidate |
| Armor suffix | Preserve 22/23; no implicit rewrite | Unit test | Implemented candidate |
| Power voltage | Missing rating HOLD; explicit MV preserved | Unit tests | Implemented candidate |
| Production loss | Remark-only | Unit test | Implemented candidate |
| Package conversion | Requires explicit length | Unit tests | Implemented candidate |
| Fractional metres | HOLD, no silent rounding | Unit test | Implemented candidate |
| Patch | Full row reparse/revalidation | Unit test | Implemented candidate |
| Source quantity conservation | Recompute from raw input independently | Tamper + aggregation tests | Implemented candidate |
| N/PE/PEN role | No inference; compound-section power cables HOLD if role missing | Unit tests | Candidate |
| N/PE/PEN numeric standards | No numeric profiles without reviewed evidence | Empty profile registry | Blocked pending review |
| September historical replay | Not run in this build | None | Pending mandatory acceptance |
| Full V28.5/V29.1 mapping parity | Not complete | None | Pending |
