# Variant-specific draws before the shared factory tail

`RecordTemplateFactoryModel` adds raw variants 60 and 67, raising support below
89 from 66 to 68. Both make one one-based draw before the existing bound-100
common-tail draw. The result keeps `variant_draws` separate from `tail.draws`;
research drivers emit both in execution order. Destination and RNG are staged
until the result is complete. No item, timing or gameplay meaning is assigned
to these raw fields; the active synthetic demo is unchanged.

Variant 60 sets parent byte +21 bit 0, draws 1–4 and writes it to byte +23.
Signed mode word A5−0x9fa controls further writes: mode 1 clears byte +18; mode 2
sets it to 16; mode 3 sets it to 117, adds 20 to byte +2, multiplies word +14 by
5 and subtracts 60 from byte +8. Other signed modes preserve those fields.
Stores wrap at their width.

Variant 67 draws 1–10, stores supplied raw long A5−0x7f6 plus the draw at record
long +44, and the same supplied long plus 15 at long +28. It sets bit 0 of byte
+20 and bit 4 of +21. Both long additions wrap modulo 2^32. `Context::base_long`
is that explicit supplied long and defaults to zero; no live clock or inferred
initialization is used.

## Connected evidence

Original CODE 1/5/7/9/12 instructions match **1,800 cases**, including **1,200
variant-specific draws**, **7,200 total draws** and **1,200 actual follow-ups**.
Cases cover variants 60/67 and unchanged control 79, eight signed mode values,
five word values, five raw-long values and three RNG/template profiles. Checks
compare every output byte, full RNG state, copy source, follow-up execution and
ordered bound/mode/result trace. Sources, children, metadata, caller/frame,
registers, stack and guards remain checked. No service/RNG/callback result shim
or allocator is used; records/tables/histories are authored.

The harness permits the additional RNG return sites only when the caller
explicitly declares the expected bound 4 or 10. It verifies that prefix draw's
bound/mode, then the common tail's bound-100 entry and its one-or-eight draw
count separately. Standalone-tail comparisons keep the strict no-prefix default.
The raw long is authored inside the existing global-context guard and checked
unchanged. Translation-cache flushing remains enabled before measured execution.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/factory_variant_draws_driver.cpp -o dist/factory_variant_draws_driver
python tests/research/verify_factory_variant_draws.py local-generated/original-resources/manifest.json \
  --native-driver dist/factory_variant_draws_driver \
  --output local-generated/analysis/factory-variant-draws-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private path. Source hashes match the mode-variant
oracle. Original bytes/disassembly/detailed reports remain ignored. Public tests
freeze the prefix draws, mode cases, width wrap and separate tail trace. Earlier
oracles passed after rebuilding their drivers for the expanded result:

- 2,002 standalone tail cases / 7,091 draws: unchanged result digest.
- 648 variant-7 mode cases / 225 multiplies / 432 callbacks: unchanged digest.
- 32,768 copy probes plus 2,044 template cases / 6,881 draws.
- 1,050 finalized cases / 700 callbacks / 3,530 total draws.
- 1,050 placement cases / 700 callbacks / 3,530 total draws.

Local suites passed 56 Python tests plus native regressions, 25/25 ASan/UBSan
and 26/26 SDL checks, with both optional graphics decoders. No failures/skips
occurred. Production Python tools are unchanged (last coverage 82%). No Android
build/runtime, original game boot, Actions run/upload, merge or release was
performed. All five Actions workflows remain disabled.

PR #45's integration repair and PR #46 were verified merged into `develop` during
this work. The new branch starts from #46's head and also targets `develop`.
Original allocation/resources, child creation, 21 unsupported variants below 89,
complete glyph/progression integration and gameplay validation remain unfinished.
