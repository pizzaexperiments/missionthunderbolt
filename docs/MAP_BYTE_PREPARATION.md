# Generator map-byte preparation — issue #8

`engine/glyph_preparation_model.hpp` models a bounded stage inside the original
CODE 12 generator caller: **resource offsets 4866 (0x1302) through 5238 (0x1476)**.
The enclosing function starts at 3408 / jump 629 and calls the recovered selector
later. Its cache/loading, preceding setup and subsequent byte-to-record conversion
are not executed by this stage test. No original game was booted.

The stage uses a **19×67 byte map**, reached through 19 row pointers at header
offset +28. These bytes are distinct from the contiguous 20-byte cell records
whose layout was recovered earlier. Inputs include header byte +6, the caller's
raw signed-word argument, and byte +2 of a separately supplied metadata record.
No terrain, item, difficulty or mission names are assigned to those fields.

## Three observed passes

| Pass | Gate and attempts | Effect on a sampled 0x20 byte |
| --- | --- | --- |
| A | Header byte +6 bit 2 clear; 32 attempts | Additional zero-based draw with bound 32: zero writes 0x3b, nonzero writes 0x2e |
| B | Raw word argument differs from 46 and 69; 16 attempts if bit 2 set and metadata byte is signed-nonnegative, otherwise 32 | Write 0x2d |
| C | Same raw-word gate as B; freshly drawn one-based bound 3 at each loop condition | Write 0x24 |

Every attempted sample draws a zero-based row with bound **19** and column with
bound **67** using the recovered shuffled RNG. Non-space bytes remain unchanged,
but their coordinate draws still occur. Repeated coordinates matter: an earlier
write can remove a space, changing both later writes and conditional RNG draws.

Pass C starts its counter at one. It draws a **new** 1–3 comparison value at each
condition, including the final failed condition, rather than selecting a fixed
number of attempts once. It consequently makes 1–3 attempts with a variable RNG
call sequence. Raw arguments 46/69 skip B and C after A; with bit 2 also set the
whole stage consumes no RNG draws or map writes. These constants are observed
branch values, not identified mission or victory conditions.

## Original/native verification

The oracle loads hash-checked original CODE **1, 5 and 12**, executes the original
RNG initializer, and patches analytical A5 jump stubs to the original RNG helpers.
It then enters the bounded generator stage with authored header/row pointers,
metadata, frame and byte map. It stops before the subsequent conversion loop.
There are no service or RNG-result shims in this run.

**1,600 cases** matched every final map byte, all RNG state/table words, pass
attempt counts, and the full sequence of RNG bounds/modes/results and byte writes
(pass, row, column, old value, new value). Total observed work was **151,788 RNG
calls and 33,766 byte writes**. Original header/metadata bytes, map/frame guards,
context registers and stack balance are checked. Fixtures cover:

- Every uniform byte value and every flag byte.
- Every metadata byte, including the signed threshold at 128.
- Gate arguments and signed-word extremes, with supplied valid metadata pointers.
- Seed/fallback variations, spaces, mixed bytes, repeated hits and seeded maps.

Unusual raw arguments test this stage's arithmetic/branches; they do not establish
legal original level identifiers or real runtime metadata. Stable supplied header
and metadata are preconditions. The native model rejects out-of-word arguments
before changing state; that diagnostic is not original error behavior.

The source fingerprints are the existing CODE 1/5/12 profiles in RNG_RESEARCH.md
and the private report. Unicorn **2.1.4** ran the instructions; Capstone **5.0.6**
aided bounded static inspection. Original bytes/disassembly and detailed reports
remain private. Public tests contain authored byte maps and frozen results only.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/glyph_preparation_driver.cpp -o dist/glyph_preparation_driver
python tests/research/verify_glyph_preparation.py local-generated/original-resources/manifest.json \
  --native-driver dist/glyph_preparation_driver \
  --output local-generated/analysis/glyph-preparation-crosscheck.json
```

Use a fresh private output path. The report identifies every fixture, attempt/
draw/write counts and result SHA256. Native regressions freeze all-space seeded
traces, final map fingerprints, conditional draw order, skip behavior, unchanged
non-space bytes and the native argument precondition.

The next boundary is the original **byte-to-20-byte-record classification** stage
starting at 0x1476. Until that conversion, preceding construction/cache/loading
and later population/progression are corroborated, these passes must remain a
research model. They do not replace the active synthetic demo's map generation,
prove original walkability/collision, or complete #8.
