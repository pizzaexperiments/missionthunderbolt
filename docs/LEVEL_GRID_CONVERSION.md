# Six additional level-word glyphs — issue #8

`LevelCellConversionModel` adds six CODE 12 branches. `LevelGridConversionModel`
combines them with the preceding 43 direct branches in the connected 19×67
traversal, for **49 supported glyphs**. These are raw field transitions, not
identified terrain, stairs, mission progression or item effects. The active
synthetic demo is unchanged.

All six retain the common header-byte addition and shared subtype adjustment.
Their word addition uses the original big-endian tuning slots: kind 31 at
A5−0x1c22, kind 32 at A5−0x1c20 and kind 34 at A5−0x1c1c. No lookup-table meaning
beyond these observed slots is inferred.

| Glyph byte | Additional raw writes | Tuning / RNG |
| --- | --- | --- |
| 215 | kind 34; subtype 89, or 87 with header byte +6 bit 4 | add tuning 34 |
| 175 | kind 34; subtype 88 | add tuning 34 |
| 187 | kind 32; set cell +4 bit 2; byte +9 = caller word +1 modulo 256 | add tuning 32 |
| 171 | kind 31; set cell +4 bit 2; byte +9 = caller word −1 modulo 256 | add tuning 31 |
| 94 | kind 0; with nonzero caller word, set +4 bit 2 and byte +9 = caller word −draw modulo 256 | nonzero: tuning 31 and one-based bound-3 draw; zero: base tuning, no draw |
| 118 | kind 0; with nonzero caller word, set +4 bit 2 and byte +9 = caller word +draw modulo 256 | nonzero: tuning 32 and one-based bound-3 draw; zero: base tuning, no draw |

The draw gate tests the **whole raw word**, not its low byte: 256 and −256 still
consume RNG. The zero-word paths preserve prior byte +9 and bit 2 rather than
clearing them. Other old fields survive except where the common prefix/tail or
selected branch writes them. Subtype adjustment can therefore still depend on
arbitrary initial flag/subtype bytes.

## Connected verification — 2026-10-27

Original CODE 12 offsets 0x1476–0x2b5c execute through the same outer loop and
CODE 6 base-word helper as [the earlier traversal](DIRECT_GRID_CONVERSION.md).
The original CODE 5 initializer and one-based RNG wrapper, CODE 12 shuffled RNG,
and CODE 1 arithmetic helpers also execute directly through authored loaded-jump
stubs. Observation hooks read entry/return values; they do not supply results or
replace instructions. Only those service entries are allowed, and RNG helpers
must run inside an observed draw. There is no RNG or service-result shim.

The comparison passed **188 grids / 239,324 cells / 57,618 RNG draws**:

- 144 uniform maps: six new glyphs, 12 signed caller-word values and two header
  gate profiles. Values include −32768, ±256, ±257, −1, 0, 1, 254, 255 and 32767.
- 32 seeded mixed maps over all 49 supported glyphs.
- 12 sparse maps placing the six branches at corners and row boundaries.

All 25,460 record bytes per map match. The complete RNG state (last result, both
seeds and 100 shuffle-table entries) and every row/column/bound/mode/result draw
match. Header, source map, frame/counters, caller word, context registers, stack,
cell boundaries, final address, all six tuning words and fallback word are checked.
Seeds include zero/fallback, 1, 42, 65536 and 0xffffffff; authored initial records
and tuning words cover preserved fields, signed-byte additions and word wrap.
Source SHA-256 fingerprints for CODE 1/5 come from verify_rng_cpu.py and CODE 6/12
from verify_direct_grid_conversion.py; mismatched inputs are rejected.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/level_grid_conversion_driver.cpp -o dist/level_grid_conversion_driver
python tests/research/verify_level_grid_conversion.py local-generated/original-resources/manifest.json \
  --native-driver dist/level_grid_conversion_driver \
  --output local-generated/analysis/level-grid-conversion-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private report path. Original bytes, disassembly and
detailed reports remain ignored. Public regressions use authored records only;
the seed-42 two-draw case freezes results 1/2 and the resulting RNG seed words.
They also check no draw at word zero, byte wrap, branch writes and unchanged
records/RNG after unsupported glyphs or invalid caller words. The grid preflight
is an atomic model capability check, not original error handling.

The original direct-only oracle was rerun after adding an optional service
observer: **131,072 helper probes and 111 grids / 141,303 cells** still match.
Without an observer, its original service rejection remains in force. Local
suites passed **56 Python tests** plus native regressions, **18/18 ASan/UBSan**
and **19/19 SDL** checks. Both optional external picture decoders were present.
No failures or skipped checks occurred in this increment; Android/runtime/device
checks were not rerun. Production Python tools are unchanged (last coverage 82%).

Remaining work includes creation/default glyph branches, original allocation and
initialization, earlier-stage integration, population/progression and gameplay
reference comparisons. The prepared 0x2d/0x2e/0x3b/0x24 creation branches remain
unsupported. No full generator, original game boot, new APK, Actions run/upload
or release is claimed; all five Actions workflows remain disabled.
