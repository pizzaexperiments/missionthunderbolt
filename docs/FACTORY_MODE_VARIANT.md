# Factory variant 7 and its signed mode gate

`RecordTemplateFactoryModel` now supports raw variant 7, bringing the supported
set below 89 from 65 to 66. `Context::mode` is the signed word read at A5−0x9fa;
existing callers default it to zero. It must fit −32768…32767. No gameplay meaning
is assigned to that global or the modified fields; the active demo is unchanged.

Variant 7 always sets parent byte +21 bit 3. When the signed mode word exceeds 2,
it first adds 33 to byte +2, multiplies word +14 by 80, subtracts 67 from byte +8
and multiplies long +4 by 1250. Stores wrap at their field width. Negative modes
and 0/1/2 skip those arithmetic edits. The existing common RNG tail and optional
actual follow-up then execute unchanged. Control variants 65/79 ignore the new
mode word.

## Original comparison and hook-cache correction

The original CODE 9 path calls the real CODE 1 multiply helper at A5+0x42.
The observer validates the caller return address and both operands; it never
supplies a result. Original CODE 1/5/7/9/12 instructions execute through the
supported factory stage and actual final follow-up, on a supplied allocation and
authored templates/children/metadata.

An initial call-count assertion failed: mode 3 reached the arithmetic call but
its helper entry was not observed. Tracing showed that Unicorn reused helper
translation blocks compiled during RNG initialization/warm-up before hooks were
installed. The helper still executed and returned its result. The harness now
flushes translated blocks after registering hooks and before the measured stage.
No source instructions, results or assertions were replaced/disabled. This makes
service guards observe the warmed helpers as well as newly translated code.
The generic harness still rejects arithmetic outside observed draws unless an
explicit observer validates the particular variant call.

The final comparison matched **648 cases**, **225 actual variant multiplies**,
**432 actual follow-ups** and **2,160 RNG draws**. Cases cover signed mode edges,
variant 7 plus unchanged controls 65/79, five word values, five long values,
byte wrap, three RNG/table profiles and type-72 child selection. Every record
byte, complete RNG state, source selection, trace and guard/context check matches.
The mode word stays unchanged. Native regressions isolate the arithmetic edits
with an authored nonzero RNG branch and reject invalid mode inputs atomically.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/factory_mode_variant_driver.cpp -o dist/factory_mode_variant_driver
python tests/research/verify_factory_mode_variant.py local-generated/original-resources/manifest.json \
  --native-driver dist/factory_mode_variant_driver \
  --output local-generated/analysis/factory-mode-variant-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private output path. Source hashes match the
finalized-factory oracle. Original bytes, disassembly and detailed reports remain
ignored; public fixtures are authored. Rebuilt research drivers and reran the
older oracles with the corrected observation boundary:

- 2,002 standalone tail cases / 7,091 draws: the complete result digest is
  unchanged from the earlier report.
- 32,768 copy probes plus 1,988 template cases / 6,629 draws.
- 1,020 finalized cases / 680 actual follow-ups / 3,400 draws.
- 1,020 placements / 680 actual follow-ups / 3,400 draws.

The latter suites include the newly supported variant with default mode zero;
older report counts remain historical checkpoints. Local suites passed
56 Python tests plus native regressions, 24/24 ASan/UBSan and 25/25 SDL checks,
with both optional graphics decoders. The failed initial hook assertion is
retained in local logs. Production Python tools are unchanged (last coverage 82%).
No Android build/runtime, original game boot, Actions run/upload or release was
performed. All five Actions workflows remain disabled. Original allocation and
child creation, 23 unsupported variants below 89, glyph/progression integration
and original gameplay validation remain unfinished.

This branch starts from the integration repair #45 but targets `develop` directly.
Its prerequisite commits disappear from the diff when #45 reaches `develop`;
there is no need to wait for that merge before doing new work.
