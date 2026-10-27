# Connected direct grid conversion — issue #8

`engine/direct_grid_conversion_model.hpp` models the **19×67 conversion traversal**
for maps containing only the 43 glyphs supported by BasicCellConversionModel.
This is a research model, separate from the active synthetic demo. It does not
complete the generator or assign terrain/item meaning to recovered fields.

The connected original comparison executes CODE 12 offsets **0x1476–0x2b5c**,
including loop initialization, cell addressing, per-cell seed-word assignment,
glyph dispatch and subtype adjustment. It stops before subsequent population
logic. A5 jump displacement **0x742** resolves to jump-table entry 228, CODE 6
resource offset **9816**; an authored loaded-jump stub calls that original routine.
There are no service-result or RNG shims. Any other service entry fails the test.
This does not execute the Macintosh loader or validate CREL runtime addressing.

## Base word and traversal

The CODE 6 helper compares only its first signed word argument. It ignores the
coordinate byte arguments: values below 16 return 0, values 16–29 return 250, and
values 30–32767 return 1000. CODE 12 passes its raw caller word plus one, with
16-bit wrap; raw 32767 therefore passes −32768 and receives 0. These constants
are recovered field values, not identified gameplay statistics.

The outer loop visits rows 0–18, columns 0–66, in that order. It locates each
20-byte record at `104 + row*1340 + column*20`, overwrites word +2 with the helper
result, then performs the supported direct conversion and shared subtype tail.
Other initial bytes are retained except where the verified branch changes them.
The final loop bytes are row 19/column 67. Original allocation/initialization is
outside this comparison; complete initial records and header/tuning inputs are
explicitly authored by the harness.

The native model validates the signed caller-word range and every glyph before
changing records. Unsupported maps reject atomically. This preflight is a model
capability contract, not original error behavior; the original dispatch includes
many branches that are still unimplemented here.

## Local evidence — 2026-10-27

- **131,072 base-word probes**: all 65,536 signed-word values with authored
  coordinate/padding bytes, plus all 65,536 coordinate byte pairs at word 29.
  Return word, saved registers, stack balance, arguments and guards are checked.
- **111 complete grids / 141,303 cells**: 43 uniform-glyph maps, 36 mixed maps
  across caller-word thresholds/wrap and header gates, plus 32 seeded random maps.
  All 25,460 record bytes per map match the native model. Initial records include
  arbitrary bytes, zero and 0xff fills; tuning words include overflow cases.
- Every seed call's row/column/word arguments and order are checked. Header,
  source map, tuning, context registers, caller word, final cell address, frame
  loop counters, stack and record-boundary guards are checked.

Original source SHA-256 fingerprints:

| Segment | SHA-256 |
| --- | --- |
| CODE 6 | `4bf2738077a379758097db694d33a198f88e0f5ef3a165d9638aa02c609ad6bd` |
| CODE 12 | `8eb9990abc838f25c1f498107380341236d65339f4506c3357f5f31820092137` |

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/direct_grid_conversion_driver.cpp -o dist/direct_grid_conversion_driver
python tests/research/verify_direct_grid_conversion.py local-generated/original-resources/manifest.json \
  --native-driver dist/direct_grid_conversion_driver \
  --output local-generated/analysis/direct-grid-conversion-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private output path. Source fingerprints must match;
no original binaries, dispatch bytes, disassembly or detailed outputs are public.
Public frozen native regressions use authored records only and run without the
original archive. They cover threshold/wrap behavior, overwritten seed words,
row-boundary/corner conversion and unchanged records after unsupported input.
An initial driver build failed `-Werror=misleading-indentation`; formatting was
corrected and the driver rebuilt with the same checks enabled.

Local suites passed **56 Python tests** plus native checks, **17/17 ASan/UBSan**
and **18/18 SDL** CTest checks. Both optional external picture decoders were
available. Production Python tools are unchanged (last measured coverage 82%).
No new APK, Android runtime, Actions run, original game boot or release is claimed.

Remaining work includes creation/RNG/default glyph paths, original allocation and
record initialization, connecting earlier loading/selection/preparation stages,
later population/progression and reference gameplay comparisons. The prepared
0x2d/0x2e/0x3b/0x24 creation branches remain unsupported.

The following [level-word glyph increment](LEVEL_GRID_CONVERSION.md) combines
these 43 branches with six additional branches in a separate model, including
two conditional original RNG paths. The direct-only oracle above retains its
strict default service boundary and remains a separate regression check.
