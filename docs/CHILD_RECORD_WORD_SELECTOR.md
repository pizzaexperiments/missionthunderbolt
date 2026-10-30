# Read-only child-record word selector — issues #7/#11

`ChildRecordWordSelectorModel` models CODE 9 entry `0x71b2` through the return at
`0x722c`. It returns a raw low word from a supplied 56-byte record and authored
56-byte/12-byte tables. It has no allocation, services, RNG or mutations. The
active demo does not use it; the word is not assigned an inventory value, weight
or other unverified gameplay meaning.

| Branch | Raw return |
| --- | --- |
| Signed type word +0 equals 107 | Descriptor indexed by signed word +8, word +10; this takes precedence over flags |
| Type 68 or 119, word +8 nonzero | Template indexed by signed type, word +14 plus one with word wrapping |
| Otherwise byte +24 bit 1 or byte +25 bit 1 set | Template indexed by signed type, word +14 |
| Otherwise | Supplied record word +14, without touching either table |

Only an accessed table needs entries. A negative/out-of-range descriptor or
template index is rejected by the native model. This is an explicit safe model
domain, not claimed original error handling. Negative raw types can use the
plain return path without requiring a template. Tables use caller-provided
sizes; this does not establish historical table lengths or contents.

## Local instruction comparison — 2026-10-30

Unicorn 2.1.4 matched **1,862 authored cases** across all four return branches:
262 descriptor, 36 incremented-template, 1,012 template and 552 own-word returns.
Cases cover all 256 descriptor indexes, raw-type boundaries, flags and precedence,
negative/nonzero selector words, word overflow and absent unused tables.

The oracle executes the original function through its real return, compares D0's
low word, and enforces saved registers, stack balance/arguments, immutable record,
tables, global window (including RNG state), source code and redzones. It refuses
unexpected service calls. Upper D0 bits and caller semantics are outside the
contract. No code or result is patched to supply an expected value.

Source CODE 9 SHA256:
`6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717`.
Complete-output digest:
`219ddc7e109f187e804aa872be1e3f8456c68ad4024d77e57fdfdc09e4ce810c`.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/child_record_word_selector_probe.cpp -o dist/child_record_word_selector_probe
python tests/research/verify_child_record_word_selector.py \
  local-generated/original-resources/manifest.json \
  --native-driver dist/child_record_word_selector_probe \
  --output local-generated/analysis/child-record-word-selector-crosscheck.json
```

Original bytes, instruction listings and detailed reports remain ignored. Native
regressions use authored tables and cover table bounds without mutation, branch
precedence, wrap and every non-descriptor raw type on the plain path. Per-PR local
smoke results are recorded with the PR. Full local ASan/UBSan **28/28** and
SDL **29/29** suites passed. No Android host behavior or
historical asset distribution changes. Inventory definitions/transitions,
parent integration and original gameplay comparisons remain open; no original
boot, Actions execution, signing, merge or publication is claimed.
