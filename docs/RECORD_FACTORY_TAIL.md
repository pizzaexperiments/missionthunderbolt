# Common factory RNG tail — issues #7, #8 and #11

`RecordFactoryTailModel` models CODE 9 resource offsets **0x1298–0x1324**.
This bounded stage takes an explicit authored 112-byte record and RNG state.
It starts after unresolved type-specific effects and stops before template lookup
and an optional follow-up callback. It is not the whole factory or recovered
item/spawn semantics; the active synthetic demo is unchanged.

The original begins with a zero-based bound-100 draw. A nonzero result skips the
conditional edits. A zero result performs seven one-based draws in exact order:

| Bound | Raw field operation |
| --- | --- |
| arithmetic-half(signed global byte at A5−0x7f1) + 1 | add draw to record byte +2 |
| signed record word +14 | add draw to word +14 |
| same global-byte bound | subtract draw from byte +8 |
| 10 | add draw to byte +13 |
| 10 | add draw to byte +10 |
| 10 | add draw to byte +11 |
| arithmetic-half(signed record byte +9) + 1 | add draw to byte +9 |

The zero-result path then adds the arithmetic half of signed long +4 to itself,
with 32-bit wrap. Arithmetic shift rounds negative odd values downward: −1 becomes
−2 after the addition, and −3 becomes −5. Using C++ truncating division or an
unsigned shift would change behavior. Byte/word stores wrap at their field width.
Nonpositive one-based bounds still call the original wrapper, which returns 1
without advancing seeds/table; the last-result field is updated.

**Both paths copy final word +14 into word +16.** Other fields remain unchanged.
The model returns the selected path and bound/mode/result trace. It reserves trace
storage before consuming RNG or mutating records. No statistics or type names are
assigned to these raw offsets.

## Connected local evidence

The comparison executes original CODE 9 tail instructions and original CODE 5
RNG wrappers, CODE 12 shuffled RNG and CODE 1 arithmetic helpers. For initialized
cases it also runs the original CODE 5 initializer. Loaded-jump stubs route to
those original routines; observation hooks read arguments/results and never
supply them. Unmodeled services fail, and internal RNG helpers must execute
inside an observed draw. No service-result or RNG shim is used.

**2,002 probes** matched every record byte, complete RNG state (last result, both
seeds and 100 shuffle entries), and the ordered raw-bound/mode/result trace:

- 1,024 seeds with original initialization and deterministic 0/32/64/96/128
  zero-based bound-1 warm-up draws. These are authored histories, not identified
  original game startup behavior. The 65,472 warm-up draws precede the measured
  factory tail and are reported separately.
- All 256 global-byte values under two explicit authored shuffle-table profiles,
  forcing the zero and nonzero paths for field-boundary checks.
- All 256 byte +9 values on the zero-result path.
- Six signed word +14 boundaries, seven long +4 boundaries and five global-byte
  boundaries in a cross-product of authored records.

There were **727 zero-result paths** and **7,091 tail RNG draws**. Five zero paths
came from original initialization plus warm-up histories; the remaining 722 used
explicit authored table states. The earlier cold-initialization sweep exercised
no zero paths from its 1,024 initialized seeds; warming the table added that
coverage without removing the forced boundary cases or weakening assertions.

Record, RNG-state and stack guards, global context, caller frame, endpoint,
registers and stack balance are checked. Source fingerprints for CODE 1/5/12
come from verify_rng_cpu.py; CODE 9 must match SHA-256
`6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717`.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/record_factory_tail_driver.cpp -o dist/record_factory_tail_driver
python tests/research/verify_record_factory_tail.py local-generated/original-resources/manifest.json \
  --native-driver dist/record_factory_tail_driver \
  --output local-generated/analysis/record-factory-tail-warmed-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private report path. Original code, disassembly and
detailed results remain ignored. Public regressions use authored records/states
and cover both paths, draw count/order, nonpositive bounds, byte/word wrap,
arithmetic signed-long boundaries and untouched fields. Local suites passed
**56 Python tests** plus native regressions, **19/19 ASan/UBSan** and **20/20 SDL**
checks, with both optional external picture decoders. No failures or skips
occurred. Production Python tools are unchanged (last measured coverage 82%).

Allocator behavior, template copy/lookup, type-specific factory effects, the
optional final callback, whole-factory/creation-glyph integration, progression
and original gameplay references remain unverified. No Android build/runtime,
original game boot, Actions run/upload or release was performed. All five Actions
workflows remain disabled; test evidence belongs in the PR.
