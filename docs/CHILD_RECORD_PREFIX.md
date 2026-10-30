# Supplied-allocation child-record prefix — issues #7/#11

`ChildRecordPrefixModel` models CODE 9 resource offsets `0x484e..0x4974`,
after the caller supplies a 56-byte allocation and before the type dispatcher.
It is a research-only header; the active demo does not call it. The 137 source
records are authored inputs, not recovered historical template data.

A nonnegative signed-word variant selects its source slot through 136; larger
variants through 32767 copy slot zero. Negative/out-of-word inputs are rejected
without publishing output or RNG changes. The entire record is copied.

The signed word at +10 draws a replacement in 1..word when greater than one;
word +14 is then multiplied by that replacement with word truncation. Byte +24
bit 5 and nonzero byte +6 gate subsequent perturbations. Bit 1 or raw type word
71 suppresses only the word perturbation. Two ordered zero-based-20 tests select
addition or subtraction of a one-based-10 draw to word +14. Subtraction clamps
the wrapped signed result to at least one; addition does not clamp.

Byte +6 uses its own ordered zero-based-20 tests. A zero-based-10 draw selects
one versus a one-based-3 delta. Addition wraps without clamping; subtraction
clamps a negative signed-byte result to zero after wrapping. These are raw
field operations, not established item quantities, values or gameplay effects.
At most eight draws occur. Output and complete RNG state publish together;
ordered traces record each bound, one-based flag and result.

## Reproduction and limits

Public native regressions cover copy selection, atomic rejection, independent
gates, the eight-draw path and signed/wrapping arithmetic. For a private original
instruction comparison, use lawfully supplied inputs and Unicorn 2.1.4:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/child_record_prefix_probe.cpp -o dist/child_record_prefix_probe
python tests/research/verify_child_record_prefix.py \
  local-generated/original-resources/manifest.json \
  --native-driver dist/child_record_prefix_probe \
  --output local-generated/analysis/child-record-prefix-crosscheck.json
```

The harness hash-checks CODE 1/5/9/12, executes the original RNG helpers, flushes
Unicorn's translated-block cache after registering hooks, and compares every
record byte, complete RNG state and ordered draw. It requires every arithmetic/
clamp block to execute and checks source-table, pointer, frame, record, RNG and
stack guards plus endpoint/register preservation. No service results are shimmed.
Original resources, instruction listings and detailed reports stay private.

The 2026-10-30 local comparison matched **1,458 cases / 4,368 draws**, with
maximum eight draws. All 137 source slots and representative fallback indices
were covered. Original execution reached count replacement 758 times, word
addition/subtraction 28/31 times, word clamp 14 times, byte increment-by-one/
random 54/22 times, byte decrement-by-one/random 43/24 times and byte clamp
35 times. Complete-output digest:
`169fd3ce443602693d8b3d7b4516dfd8eadfe767c543f83a2be53fe14bcfaf56`.
Source SHA256 values match [the factory-tail oracle](RECORD_FACTORY_TAIL.md)
(CODE 1/5/9/12); the private report records each fingerprint explicitly.

Local validation passed the native regressions, **26/26 ASan/UBSan** checks and
**27/27 SDL** checks. The combined workspace Python suite passed 65 tests,
including nine independent NDK-attribution tests; the child-prefix change itself
adds no production Python tooling. Per-PR clean-source results are recorded in
the corresponding PR. No Android host logic changed.

Allocation, type dispatch, recursive child construction, parent integration,
original table contents, inventory semantics and full-game comparisons remain
unfinished. No original game boot, Android build/device run, Actions run or
release publication is implied.

The subsequent [supported child-factory body](CHILD_RECORD_FACTORY.md) now
composes this prefix with pure type dispatch. This prefix oracle retains its
original default endpoint and guards.
