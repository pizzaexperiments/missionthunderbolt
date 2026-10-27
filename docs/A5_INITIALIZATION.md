# Startup A5 data and neighbor tables — issues #7–#9

`engine/a5_initialization_model.hpp` models two bounded blocks of CODE 1 startup:
resource offsets **216–236** (DATA/ZERO expansion) and **260–288** (DREL additions),
stopping before Resource Manager traps. CODE 0 supplies the below/above-A5 sizes.
Resource handles, destination address, A5 and saved alternate base are supplied
by the research harness. No Macintosh OS, application loader or game was booted.

## Recovered resource layout

| Input | Size / meaning | SHA256 |
| --- | --- | --- |
| CODE | CODE 1, startup instructions | `f04c7611a70c37d04b724cd8862838ca1d97052b91ee94a834d65fcccd6c1102` |
| CODE0 | 6,336 bytes above A5; 26,178 below | `a02fd7adac1cd2dfbbbed0fa3249e4a8989e16c7bcda6a65c875adf77beb5f1e` |
| DATA | 6,888 compressed bytes | `c6d01361387c4d5f6c2a7eb5cfc907b09343a30ec2b35477b4471eaeaf52dc7f` |
| ZERO | 864 run-count bytes | `bf8e36f8d85e0c351e7adf87e4c04a97ee81fa09740a77200c28d932d32792f2` |
| DREL | 1,034 relocation bytes | `ea3cf82e2d6d0c06f50594a5271859f37a10dfd5f2399d5be93532ea732b8f4e` |

The expansion loop copies one big-endian DATA word to the destination. A zero
word additionally consumes one big-endian ZERO count and clears that many bytes
after the copied word. A count of zero still consumes its ZERO word. The loop
stops when destination equals A5. In the supplied archive, it consumes all DATA
and ZERO bytes and produces exactly **26,178 bytes**, matching CODE 0's declared
below-A5 size. This establishes the observed initialized window under the
supplied standard A5 layout; OS-provided low-memory setup remains unexecuted.

The relocation block uses each DREL word's low bit as a base selector and its
remaining bits as a signed even displacement from A5. It adds either A5 or the
long saved at CODE 1 offset +4 to the big-endian long at that destination, with
32-bit wraparound. Earlier startup instructions save A4 in that slot; the actual
runtime meaning/value of A4 is not inferred. The harness supplies alternate bases
explicitly. Repeated entries apply repeated additions. The original DREL has
**517 entries** (481 alternate-base and 36 A5-base), spanning displacements
**−21,826 through −556**. This recovers DREL behavior, not CREL code relocation.

Native checks reject truncated resources, odd/alignment-unsupported inputs,
oversized windows and out-of-image relocation targets. These are explicit model
preconditions, not recovered original fault handling. The window cap is 16 MiB;
relocation input is restricted to even lengths up to 32,766 bytes, within the
observed signed-word size loop. Expansion reports consumed source prefixes and
can leave trailing input untouched once the destination is reached.

## Startup neighbor directions

After expansion and relocation, selector table elements **1–8** at A5−2534
(row deltas) and A5−2522 (column deltas) are:

| Index | Row delta | Column delta |
| --- | ---: | ---: |
| 1 | -1 | 0 |
| 2 | -1 | 1 |
| 3 | 0 | 1 |
| 4 | 1 | 1 |
| 5 | 1 | 0 |
| 6 | 1 | -1 |
| 7 | 0 | -1 |
| 8 | -1 | -1 |

No DREL target overlaps either table's consumed bytes. The values are stable
across all five supplied alternate bases. They match the canonical table used
previously as an authored fixture, but that earlier coincidence was not evidence
of original initialization. These checks establish **startup values only**:
later indexed writes, platform/version changes or game-driven modification have
not been excluded. They do not establish keyboard mappings or movement rules.

## Verification and reproduction

Unicorn 2.1.4 executed the hash-checked original blocks. The native model matched
**68 expansion cases** and **133 relocation cases**: authored literal/zero runs,
zero and maximum tested runs, unconsumed tails, repeated relocations, signed
displacements, base-selection flags and arithmetic wraparound, plus the actual
resources across five alternate bases. Output bytes, source consumption and
original memory guards were compared. Capstone 5.0.6 helped inspect startup
instructions after Ghidra's generic decoder stopped at A-line traps; it is a
research-only aid and is not needed to run these checks or bundled with the app.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/a5_initialization_driver.cpp -o dist/a5_initialization_driver
python tests/research/verify_a5_initialization.py local-generated/original-resources/manifest.json \
  --native-driver dist/a5_initialization_driver \
  --output local-generated/analysis/a5-initialization-crosscheck.json
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/selector_lifecycle_driver.cpp -o dist/selector_lifecycle_driver
python tests/research/verify_selector_lifecycle.py local-generated/original-resources/manifest.json \
  --native-driver dist/selector_lifecycle_driver --startup-directions \
  --output local-generated/analysis/selector-startup-directions-crosscheck.json
```

Use fresh private output paths. The second check runs the startup expansion and
relocation blocks in the same original-instruction context as RNG/selector/
lifecycle routines; its native driver expands/relocates the private inputs and
extracts directions through the native model. Neither implementation manually
writes direction values in this mode. Synthetic RNG seed/last-result settings
are then supplied explicitly. Resource loading and the final DisposePtr trap
remain outside the test.

All **162 connected worlds** passed: 18 first-scan, 10 second-scan, 26 random
acceptances, 72 retry-budget stops, 24 direct and 12 neighbor selections. Relevant
grid/record bytes, prefixes, RNG/header state, coordinates and callback order
matched. The existing three-table **486-case** comparison remains available and
was rerun successfully after the extension. The mode does not compare every
unused global or execute the full startup routine. Original resource bytes,
expanded globals, disassembly and reports stay ignored.

The active demo remains synthetic. Full map generation, mission progression,
CREL, allocator reclamation and original gameplay reference comparisons remain
open. See [grid research](GRID_RESEARCH.md) for the connected routine scope.
