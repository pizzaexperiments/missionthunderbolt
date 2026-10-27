# Grid layout and candidate-selection research — issues #7–#9

These models were written from bounded static analysis and isolated instruction
checks against the supplied executable's hash-checked CODE resources. The
executable identifies 2.0.g. No Mac OS/ROM or original game was booted. Original
bytes, disassembly, decompiler hypotheses and reports stay private. Synthetic
inputs and newly written models/tests are public; active demo gameplay is unchanged.

## Corroborated pieces

| Piece | Source | Native/original-instruction evidence |
| --- | --- | --- |
| Grid pointer builder | CODE 12 entry 19476, jump 630; multiply helper in CODE 1 | 120 cases, 152,760 cell addresses; synthetic allocation/reuse paths |
| Signed-byte coordinate clamp | CODE 13 entry 26098, jump 692 | All 65,536 distinct row/column byte pairs; adjacent bytes preserved |
| Candidate gate | Two decision blocks inside CODE 13 entry 12328, jump 671 | 2,048 probes across all kind bytes and four values of field +16; 1,024 native gate comparisons |
| Selector before fallback | CODE 13 entry 12328 plus original CODE 5/12 RNG and initializer | 105 synthetic-map cases; path, attempt count, coordinates and complete RNG state match |

Unicorn **2.1.4**, explicitly configured as a **68000**, ran the instructions.
Analytical segment/stub/memory addresses are test scaffolding, not recovered
runtime addresses. The optional research harnesses reject unsupported resource
hashes, ambiguous segment IDs and existing report files. Existing RNG research
fingerprints and arithmetic are documented in [RNG_RESEARCH.md](RNG_RESEARCH.md).

## Grid record addressing

The pointer builder constructs **19 row tables of 67 pointers**, with each pointer
addressing a **20-byte record**. A record at zero-based `(column,row)` has address
bits `base + 104 + row*1340 + column*20`, modulo 32 bits. The final record starts
at offset 25,544; its end is 25,564. These are layout facts for this routine,
not identified terrain fields or a recovered mission generator.

Missing row tables invoke a synthetic allocation shim with observed arguments
`(1,268)`; existing row tables are reused. The harness tests empty, reused, mixed
and one-missing table sets; it verifies every pointer, allocation request/count,
stack balance and sentinel bytes after each row table. The original allocator,
allocation failure behavior and wider memory ownership are not modeled.

Five synthetic base values include wraparound, and six signed table-index inputs
include signed-word extremes. This checks arithmetic and indexing; it does not
make those indices legal historical game levels. `GridRecordLayout` returns
integer address bits only, never a native pointer to dereference. Its coordinate
bounds checks are a new research API safety contract.

## Coordinate and candidate rules

The original clamp receives two distinct writable byte pointers, row then column.
It interprets both values as signed bytes and clamps row to **0–18**, column to
**0–66**. The native model uses the explicit `(column,row)` argument order and
rejects inputs outside signed-byte range. It is a clipping helper, not evidence
that a player move into a wall or beyond the boundary succeeds.

The selector's two gates reject kind bytes **1, 2, 22, 25, 28, 29, 30 and 34**.
Other byte values pass only when the raw 32-bit field at record offset **+16** is
zero. The meaning/ownership of that field and the historical names of kind values
remain unresolved; this gate must not be used as a general collision predicate.

## Bounded selector and RNG consumption

`GridCandidateSelector` takes explicit records, an eight-entry signed-byte
**direction table supplied by the caller**, and a separate `ShuffledLcgModel`.
It draws an interior row 1–17 and column 1–65. For up to 200 attempts it checks the
current record, then up to eight clipped neighbors starting at a random direction.
If none qualifies, it draws independent -1/0/+1 row/column changes and clips again.
After 200 attempts it returns `needs_fallback`, with the coordinates and RNG state
at the original fallback call. It does not pretend those coordinates were accepted.

The private oracle runs the original initializer and RNG instructions as well as
the selector. It compares the selected path, original attempt counter, coordinates,
last RNG result, both seeds and all 100 shuffle slots, and checks that grid records
and adjacent output bytes were untouched before fallback. The 105 cases cover
five seed arguments, seven synthetic map patterns and three supplied direction
tables (canonical test ordering, rotation and signed-byte wraparound extremes).
Outcomes: **29 direct, 36 neighbor, 40 needs-fallback**. The historical direction
values/order have not been recovered; the fixtures explicitly do not claim them.
The original D0 return bits are not modeled as a typed result contract.

The fallback at CODE 13 offset 15742 performs additional passes and can modify
records or invoke object-related routines. It is deliberately stopped before
execution; its semantics remain open. This model is not linked into demo map
generation, movement, spawning or rendering. Full topology, mission progression,
collision/FOV, scheduler behavior and original game comparisons remain outstanding.

## Reproduce with private inputs

From the repository root, with Unicorn 2.1.4 in the selected Python environment:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/research/grid_layout_driver.cpp -o dist/grid_layout_driver
python tests/research/verify_grid_layout.py local-generated/original-resources/manifest.json \
  --native-driver dist/grid_layout_driver --output local-generated/analysis/grid-layout-final-crosscheck.json
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/research/grid_rules_driver.cpp -o dist/grid_rules_driver
python tests/research/verify_grid_rules.py local-generated/original-resources/manifest.json \
  --native-driver dist/grid_rules_driver --output local-generated/analysis/grid-rules-final-crosscheck.json
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/research/grid_selector_driver.cpp -o dist/grid_selector_driver
python tests/research/verify_grid_selector.py local-generated/original-resources/manifest.json \
  --native-driver dist/grid_selector_driver --output local-generated/analysis/grid-selector-final-crosscheck.json
```

Use fresh report paths for another run. Public C++ tests freeze corner offsets,
kind rejection bitmap and independently executed synthetic direct/neighbor/
fallback-entry traces, including RNG table hashes. They also reject unsupported
native inputs without advancing RNG state. `sh scripts/test_local.sh` and root
CTest run these without original inputs or an emulator dependency.
