# Supplied-allocation factory through final follow-up

`FinalizedTemplateFactoryModel` composes the template-factory model with the
recovered CODE 7 follow-up whenever the source-template gate requests it.
The original comparison now executes the actual CODE 7 routine through return,
then CODE 9's call-argument cleanup, stopping at 0x133c. It no longer stops at
0x1334 on these cases. Allocation, descriptor-driven child creation, unsupported
variants and whole-factory ABI return remain excluded.

This change preserves template/type selection, pure variant writes and common
RNG processing. A required follow-up can modify parent bytes +18/+20/+22 by
reading supplied child records and threshold metadata. A skipped follow-up leaves
those bytes as produced by the earlier stages; it does not clear selection fields.
The model stages RNG and destination, so missing callback inputs reject without
changing either. This rollback is a model safety contract, not original behavior.

## Connected evidence

The original comparison passed **1,005 cases**, with **670 executed follow-ups**
and **3,350 RNG draws**. Cases cover the 65 supported variants plus two fallback
variants, five signed caller words and three template/metadata profiles. Profiles
exercise no callback, remapped copied types, and type 72; child counts span 0–13.
Children include eligible/excluded scores, signed values, flag gates and ties.
Every final record byte, selected source, full RNG state and ordered draw trace
match the composed native model. Source tables, descriptors, threshold metadata,
children, context, guards, caller words and stack remain checked.

CODE 1/5/7/9/12 instructions execute directly. The loaded A5+0xb92 jump points to
the original CODE 7 entry 9972. The observation hook counts the call and never
supplies a return value. No callback-result, allocator or RNG shim is used. All
records/tables/histories are authored; disassembly and detailed outputs stay private.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/finalized_template_factory_driver.cpp -o dist/finalized_template_factory_driver
python tests/research/verify_finalized_template_factory.py local-generated/original-resources/manifest.json \
  --native-driver dist/finalized_template_factory_driver \
  --output local-generated/analysis/finalized-template-factory-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private report path. The generic harness retains its
strict default service boundary; only the new explicitly supplied observer allows
the original follow-up service. Earlier copy/template and standalone-tail oracles
passed again separately: 32,768 copy probes / 1,960 boundary cases and
2,002 standalone tail cases retain their prior counts/results.

Local suites passed 56 Python tests plus native regressions, 22/22 ASan/UBSan
and 23/23 SDL checks, with both optional picture decoders. The initial research
driver compile rejected an unused argument under `-Werror`; the argument was
unnamed and the driver rebuilt without relaxing flags. No Android build/runtime,
original game boot, Actions run/upload or release was performed. Production
Python tools are unchanged (last measured coverage 82%).

This change is based on PR #42's `feature/record-followup` branch and can be
reviewed as a dependent PR without merging its predecessor first. Both need
maintainer merge approval. Full glyph creation, original allocation/resources,
child creation, unsupported variants, progression and gameplay validation remain
unfinished. GitHub Actions stays disabled.
