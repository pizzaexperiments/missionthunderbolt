# Direct-write cell conversion — issue #8

`engine/basic_cell_conversion_model.hpp` implements **43 supported glyph branches**
and the shared subtype adjustment inside CODE 12's generator. It does not
implement the entire glyph dispatch table. Unmodeled glyphs reject before native
state changes; some need creation/RNG services, while others are unmodeled
default paths. A rejection is a model capability contract, not original behavior.

The original comparison enters at **0x14b8**, after an unresolved coordinate
helper has stored the seed word at cell +2, and stops at **0x2b40**, before the
next-column increment. The six-byte argument cleanup still executes and is
checked. Cell pointer, source glyph/row pointers, header bytes, raw caller word
and three tuning words are supplied by the harness. Full cell allocation, the
coordinate helper and the outer map loop are not executed.

## Recovered writes

A header byte +6 bit-4 gate controls a common prefix addition: when clear, the
header's signed byte +8 multiplied by ten is added to cell word +2. Branches then
apply raw kind/subtype/flag writes and add one of the three big-endian tuning
words at A5−0x1c60, A5−0x1c5e and A5−0x1c5c, with 16-bit wraparound.

The supported byte codes are:

```text
32 35 37 38 39 40 41 47 80 92 96 112 119 120 123 125
140 161 162 163 164 166 172 173 176 177 180 185 188 190 191
195 196 197 198 199 200 201 210 211 212 213 217
```

They include space, several direct kind-1 branches and direct kind-2/subtype
variants. The P/p branches both set raw kind 1 and subtype 45; P additionally sets
bit 4 of cell byte +4. Several extended-byte variants set bit 6 of +4 or bit 7
of +5. Header bit 4 selects subtype values in the 82–86 range for certain
branches. One branch adds three times a tuning word and sets byte +5 bit 7 when
the raw caller word is nonzero. These are field-write facts, not identified
terrain, wall, item, combat or rendering semantics.

The shared tail at **0x2af8–0x2b40** activates if cell byte +5 has bit 7, byte +4
has bit 6, or byte +6 has a nonzero low nibble. It adds 50 to subtype values
2–27. If subtype is zero, it instead copies kind+50 when kind is 2–27. Other
bytes remain unchanged. Signed byte comparisons exclude negative raw kinds and
subtypes. The original table includes many more branches, including object
creation for prepared 0x2d/0x2e/0x3b/0x24 bytes; those are not guessed here.

## Verification

Original CODE 12 SHA256:
`8eb9990abc838f25c1f498107380341236d65339f4506c3357f5f31820092137`.
Unicorn 2.1.4 executes the original dispatch table and instructions. There are
**no service-result or RNG shims** in these selected paths; entering an unmodeled
service address fails the oracle. Input source/header/tuning/frame bytes, cell
guards and stack balance are checked. Every output cell byte is compared.

- **268,288 shared-tail probes**: all kind/subtype pairs under four gate profiles,
  plus individual flag-byte sweeps at boundary kind/subtype pairs.
- **23,822 conversion probes** across the 43 glyphs, all header flag/byte values,
  signed caller-word edges, arbitrary initial records and tuning/wraparound cases.

The first run caught two misread branch-entry details in the draft native model:
P sets an extra flag and p sets kind 1. Correcting the model to the original
instructions made the full comparison pass; no assertions were removed. Public
regressions freeze those transitions, preserved fields, word wrap, subtype
boundaries and unsupported-input behavior using authored records only.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/basic_cell_conversion_driver.cpp -o dist/basic_cell_conversion_driver
python tests/research/verify_basic_cell_conversion.py local-generated/original-resources/manifest.json \
  --native-driver dist/basic_cell_conversion_driver \
  --output local-generated/analysis/basic-cell-conversion-crosscheck.json
```

Use a fresh private report path. Original code, dispatch bytes, disassembly and
detailed results stay ignored. Active demo maps are unchanged. This is partial
conversion evidence, not a full generator or an original-game runtime comparison.
