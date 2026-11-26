# Item routes grouped by unit (SPS, last 12 months)

Prepared by Abdul Hadhee | IT Executive

Source: `routes.csv`. It covers 1,450 items sold in the last 12 months. An item's route is the units of its nested BOM sub-assemblies, then the item's own unit.
An item is listed under every unit its route passes through. "Only here" means the whole job stays in that unit. "Comes from" and "goes to" are the cross-unit hand-offs that Send next will suggest.
The full item list is in `routes-by-unit.csv`, which can be opened in Excel.

| Unit | Items | Order lines | Only here | Starts here | Middle | Ends here | Comes from (items) | Goes to (items) |
|---|---|---|---|---|---|---|---|---|
| **PackPro** | 577 | 1,855 | 530 | 38 | 0 | 9 | SHPS (9) | CPU (32), RWU (3), SHPS (3) |
| **SHPS** | 471 | 1,118 | 453 | 10 | 2 | 6 | PackPro (3), OPD-Offset (3), MOBA-Cup (2) | PackPro (9), OPD-Offset (3) |
| **MOBA-Cup** | 168 | 523 | 148 | 19 | 0 | 1 | OPD-Offset (1) | MOBA (12), PCU(cup) (5), SHPS (2) |
| **PSU** | 7 | 305 | 7 | 0 | 0 | 0 | — | — |
| **RWU** | 11 | 224 | 8 | 0 | 0 | 3 | PackPro (3) | — |
| **MOBA-Punch** | 59 | 218 | 59 | 0 | 0 | 0 | — | — |
| **OPD-Offset** | 135 | 209 | 112 | 20 | 0 | 3 | SHPS (3) | CPU (16), SHPS (3), MOBA-Cup (1) |
| **CPU** | 69 | 163 | 21 | 0 | 0 | 48 | PackPro (32), OPD-Offset (16) | — |
| **PCU(cup)** | 10 | 88 | 5 | 0 | 0 | 5 | MOBA-Cup (5) | — |
| **FPP** | 11 | 32 | 11 | 0 | 0 | 0 | — | — |
| **MOBA** | 15 | 28 | 3 | 0 | 0 | 12 | MOBA-Cup (12) | — |
| **MOBA-Plate** | 2 | 10 | 2 | 0 | 0 | 0 | — | — |
| **MOBA-Cake** | 4 | 6 | 4 | 0 | 0 | 0 | — | — |

**Notes**

- "PCU(cup)" is the paper cup unit; "MOBA-Cup", "MOBA-Punch", "MOBA-Plate" and "MOBA-Cake" are MOBA lines; "OPD-Offset" is the OPD offset unit.
- PackPro and MacPro cannot be told apart from the item: the same items go either way, chosen per order. So PackPro here includes MacPro work.
- The data comes from the 19 Sep BOM export and the 12-month sales pull (8 Oct). It shows what the BOMs say, not who actually did the work on the floor.
