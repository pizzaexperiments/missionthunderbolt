# Supported child-record factory body — issues #7/#11

`ChildRecordFactoryModel` composes the [56-byte prefix](CHILD_RECORD_PREFIX.md)
with supported type dispatch in CODE 9, from resource offset `0x484e` through
`0x4cd8`. Allocation is supplied and execution stops before the return epilogue.
The active demo does not use this research model. Source tables remain authored;
raw fields are not assigned item, enemy or inventory meanings.

The copied type word selects a 143-entry dispatcher for types 25–167. Types
outside that interval use the unchanged default. Seven types reject before
publishing any output/RNG change: **36, 37, 70, 77, 137, 138, 166**. Their paths
need recursive construction, an external helper/table or additional globals.
Supporting a default type is not evidence that it exists in historical data.

Supported non-default operations are:

| Raw type | Bounded effect after prefix |
| --- | --- |
| 25 | Signed caller word divided by five, truncating toward zero, selects raw byte +6 subtraction and word +8 replacement |
| 39 / 63 / 100 | Replace word +22 with one-based-200 / word +8 with one-based-5 / word +8 with zero-based-50 |
| 62 | Add caller word to zero-based-11, subtract five with word wrapping; reroll negative signed results with zero-based-5, clear results at least 15 |
| 81, 141 / 109 / 108 | Add one-based-20 / one-based-10 / one-based-5 to word +14 |
| 114, 116 | Replace word +22 with a one-based draw bounded by its signed value; nonpositive bounds return one without advancing seeds/table |
| 93–98, 101, 143 | Set byte +25 bit 2 |
| 127 | Replace word +22 with zero-based-5; add its product with source slot 42 word +14 to output word +14 |
| 129 | Set byte +2 to two if zero-based-4 is zero, otherwise one |
| 140, 164, 165, 167 | Set byte +24 bit 3 |
| 144 | Replace byte +13 with three |

Copy-source index, copied type and slot-42 factor are distinct inputs. All word/
byte mutations wrap at the original width. The signed caller word must fit
−32768..32767; variants retain the prefix's nonnegative-word requirement. Prefix
and dispatch publish together only after success. At most ten ordered RNG draws
occur; trace bounds retain their raw word encoding for negative signed bounds.

## Local evidence — 2026-10-30

The original-instruction/native oracle matched **2,096 cases / 5,302 draws**,
including the maximum ten-draw path, every supported table entry, unsigned
range boundaries and all **30** required arithmetic/type branch blocks. It
compares every output byte, source selection, ordered bound/mode/result and all
103 RNG state words, while enforcing source/frame/pointer/record/RNG/stack guards
and the exact endpoint. No helper return values are shimmed. Input tables,
records, caller words and RNG histories are authored.

Complete-output digest:
`fb1869bf6127e274691fc48d2304ab73e0849a629f30c177057bebe3898bb5e2`.
CODE 1/5/9/12 fingerprints match [the factory-tail oracle](RECORD_FACTORY_TAIL.md)
and are written into the private report. Use Unicorn 2.1.4:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/child_record_factory_probe.cpp -o dist/child_record_factory_probe
python tests/research/verify_child_record_factory.py \
  local-generated/original-resources/manifest.json \
  --native-driver dist/child_record_factory_probe \
  --output local-generated/analysis/child-record-factory-crosscheck.json
```

The prefix harness has an explicit factory mode; its default still stops at
`0x4974`. Rerunning that default matched **1,458 cases / 4,368 draws** with the
unchanged digest from the preceding checkpoint. Native tests cover atomic
rejection, raw signed bounds, caller division/wrap, separate factor source,
complete RNG continuation and the composed maximum-draw path. Full local
ASan/UBSan **27/27** and SDL **28/28** suites passed.

Original template contents, actual allocation, seven excluded types, return ABI,
parent child-construction integration, inventory semantics and gameplay reference
comparisons remain unfinished. Source listings and detailed original-derived
reports remain ignored. No Android rebuild/device test, Actions execution,
merge, signing or publication is claimed by this increment.
