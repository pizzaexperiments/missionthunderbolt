# Isolated RNG research — issues #7 and #8

The original executable identifies version 2.0.g. This research uses private,
hash-checked CODE resources; no original binary, disassembly or decompiler output
is included in Git. No Mac ROM, OS or original game was booted. Analytical load
addresses and authored jump stubs are test scaffolding, not recovered runtime
addresses. Unicorn 2.1.4 is an optional research dependency, never shipped.

Static constant searches led to two candidate generators. Inspection of their
multiply helper and callers, followed by executing the isolated original 68000
instructions, supports this arithmetic:

- CODE 12 entry 29850 (jump 617): advance state at A5-0xb26 using unsigned
  32-bit `state * 1103515245 + 12345`, return `(state >> 16) & 32767`.
- CODE 5 entry 32072: same operation with a separate state at A5-0x5702.
- CODE 5 entries 32110/32200 (jumps 205/206): for a positive signed-16-bit bound,
  advance the CODE-12 generator to select one of 100 table slots, take the old
  value modulo the bound (plus one for entry 32200), replace that slot with the
  CODE-5 generator output, and store the result at A5-0x56fe.
- Nonpositive bounds return/store 0 or 1 respectively without advancing either
  generator or the table. Multiplication/remainder helpers are in CODE 1.

`engine/shuffled_lcg_model.hpp` implements a separate research model. It accepts
explicit state and a 100-entry 15-bit table; it does **not** invent initialization.
The existing demo RNG and generation remain unchanged. Generic Ghidra compiler
assumptions can misstate return widths; instruction-level checks explicitly mask
the CODE-12 primitive to its 16-bit return.

## Reproduce with private inputs

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/rng_model_driver.cpp -o dist/rng_model_driver
# Use a Python environment with unicorn==2.1.4 installed.
python tests/research/verify_rng_cpu.py local-generated/original-resources/manifest.json \
  --native-driver dist/rng_model_driver \
  --output local-generated/analysis/rng-native-crosscheck.json
```

The harness refuses unsupported resource hashes and existing output files, selects
Unicorn's **68000** model explicitly, and limits instruction counts. On 2026-10-26,
140 primitive/seed cases and 54 wrapper cases passed. Inputs cover edge seeds,
64 deterministic random seeds per primitive, nine signed bounds and three seed
pairs per wrapper. All output values, stored results, both seeds and all 100 table
entries matched the mathematical model. The actual C++ model separately matched
the isolated instruction outputs for all 54 wrapper cases. Public native tests
freeze an independently cross-checked synthetic-input case and reject unsupported
bounds/table values.

Seeding, table initialization, complete call-site roles, RNG consumption order,
map generation and progression remain unknown. Matching isolated instructions is
stronger evidence for these arithmetic routines; it is not a full original-game
behavior comparison or completion of #7/#8.
