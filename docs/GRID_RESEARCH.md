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

The initial bounded-selector checkpoint stopped before the fallback at CODE 13
offset 15742. Its subsequent control-flow model with explicit service shims is
recorded below; the original linked-record callbacks remain unresolved. This model is not linked into demo map
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

## Fallback control flow with explicit service shims

`GridFallbackSelector` now models CODE 13 entry **15742** using mutable 20-byte
records and explicit linked-record services. These services do not claim the
original implementations, ownership, inventory or entity semantics. The historical
direction table and full generation/progression remain unresolved.

The fallback performs two row-major scans of interior rows **1–17**, columns
**1–65**, then an unbounded random retry loop. Both scans require raw field +12,
kind byte +0 and byte +8 to be zero, byte +1 not to equal 51, and bit 2 of byte +4
to be clear. The first also requires field +16 to be zero. The second can call a
word-valued query for a nonzero field +16; if accepted, it invokes its release
callback, clears that field and selects the cell. Scans consume no RNG draws.

The random stage draws the same interior row/column bounds. It checks kind/base
bytes, linked-record words/flags, and a signed-byte child count before invoking
release/unlink callbacks. Some rejected attempts have **already cleared field
+16 or issued callbacks**. The native model preserves that partial state and exact
callback order; it does not invent transaction rollback or assume an accepted
coordinate. Original callback routines are not executed by this verification.

For accepted random records, the observed direct writes clear bytes +8/+10/+11,
clear bit 0 of +4, mask +5 with 18 and +6 with 240, and conditionally clear +9 and
bit 2 of +4. Kinds 1/2/22/25 can become zero with the big-endian word at +2 set to
1000; kinds 2/22 have additional protection checks. Raw field meanings and kind
names are deliberately unspecified. These are not general pickup/combat/collision
rules and do not complete #11.

The caller must supply a **research retry budget**. On exhaustion, the model
returns `budget_exhausted` with partial state and the last attempted coordinate;
no coordinate is accepted. The original loop has no corresponding cap. The
oracle stops at the next original retry boundary so RNG/mutations can be compared
without hanging on synthetic impossible maps. Zero-budget tests still execute the
two ordered scans and return no attempted coordinate if neither succeeds.

The private oracle passed **1,068** fallback cases: two first-scan, two second-scan,
785 random successes and 279 budget-boundary stops. It compares every record byte,
all RNG state, callback arguments/order, output/suffix sentinels and stack balance
on normal return. Inputs cover all kind bytes, every byte value of the tested
flag fields, linked-record protection branches, signed child-count edges, scan
ordering, border exclusion and partial release before later rejection.

A further **105 end-to-end selector/fallback cases** passed: 22 direct, 23 neighbor,
15 second-scan, 30 random and 15 research-budget stops. Those runs execute the
original RNG initializer, bounded selector and fallback in one instruction
context, with synthetic directions and callback shims, comparing the final grid,
RNG, path and callback log against the composed native models. This extends the
earlier stopped-before-fallback checkpoint; it still does not execute the original
linked-record lifecycle routines or the original game.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/research/grid_fallback_driver.cpp -o dist/grid_fallback_driver
python tests/research/verify_grid_fallback.py local-generated/original-resources/manifest.json \
  --native-driver dist/grid_fallback_driver --output local-generated/analysis/grid-fallback-final-crosscheck.json
python tests/research/verify_grid_fallback.py local-generated/original-resources/manifest.json \
  --native-driver dist/grid_fallback_driver --pipeline --output local-generated/analysis/grid-fallback-final-pipeline.json
```

Reports remain private. Public native tests freeze independently executed synthetic
scan, mutation, callback-order and budget-boundary cases. Active demo gameplay
still does not use these research models.
