# Factory variant 36: draw overwrite and known fallthrough

Raw CODE 9 factory variant 36 now joins the supported set, bringing it to 69
variants below 89. It draws one-based bound 20, **overwrites** byte +11 with the
result, then falls through to the existing variant-31 path: set byte +26 bit 0,
add ten times the signed caller word to word +14 with word wrap, and set byte
+21 bit 7. The shared RNG tail and actual follow-up execute afterward. Variant
numbers here belong to CODE 9's factory dispatch; no gameplay meanings are
assigned to the fields.

The initial draw remains in `variant_draws`, separately from `tail.draws`.
The oracle declares bound 20 explicitly and observes the original return at
0x0cbc, preserving the strict default no-prefix boundary for standalone tail
checks. The caller's RNG/record publication remains staged. The tail can later
add to byte +11 on its zero-result path; it does not change the initial overwrite
into an addition to the old template byte.

## Evidence

Original CODE 1/5/7/9/12 instructions match **210 variant-36/control-31 cases**,
**105 initial draws**, **805 total draws** and **140 actual follow-ups**. Cases
cross seven signed caller words, five initial word values and three RNG/template
profiles. The old byte +11 is 255, making overwrite-versus-addition observable.
Every output byte, full RNG state, selected source and ordered trace match;
existing source, context, child, metadata, stack and guard checks stay enabled.

```sh
python tests/research/verify_factory_variant36.py local-generated/original-resources/manifest.json \
  --native-driver dist/factory_variant_draws_driver \
  --output local-generated/analysis/factory-variant36-crosscheck.json
```

Build that driver with the command in FACTORY_VARIANT_DRAWS.md, using current
source. Use Unicorn 2.1.4 and a fresh private path. Inputs are authored; original
bytes/disassembly/detailed evidence stay ignored. Expanded public regressions
freeze the bound/result, overwrite and signed caller-word wrap.

All prior comparisons passed again. Standalone tail (2,002 cases), mode variant
(648 cases) and variants 60/67 (1,800 cases) retain identical result digests.
Expanded copy/factory checks match 32,768 copy probes and 2,072 factory cases;
finalized factory and placement each match 1,065 cases/710 callbacks/3,595 draws.
Local suites passed 56 Python tests plus native regressions, 25/25 ASan/UBSan
and 26/26 SDL with both optional picture decoders. The existing variant-draw test
was expanded; no new CTest executable was added. No failures/skips occurred.
Production Python tools are unchanged (last coverage 82%). No Android build/runtime,
original game boot, Actions run/upload, merge or release was performed.

This branch follows #47 and targets `develop` directly. Original allocation and
resources, child creation, 20 unsupported variants below 89, full glyph/progression
integration and gameplay validation remain unfinished. The active demo is unchanged
and all five Actions workflows remain disabled.
