# Supplied-record attachment — issues #7, #8 and #11

`LinkedRecordModel::attach12` models CODE 7 resource offset **3794** (0x0ed2),
A5 jump displacement **0x0b02**, jump-table entry 348. Generator creation branches
call this routine after obtaining a record. This increment recovers that list/grid
mutation, not the factory or its ownership rules. The active demo is unchanged.

Given a supplied record handle and valid row/column, the original routine:

1. Increments header word +18 modulo 65536.
2. Copies header long +20 into record long +56, then stores the supplied handle
   into header +20, prepending it to the raw list.
3. Stores row/column at record bytes +48/+49.
4. Stores the handle at grid-cell long +12, using the 104-byte header and
   19×67 grid of 20-byte records.

There is no occupancy check, duplicate check, unlink, allocation or disposal call.
An existing cell link is simply overwritten. Attaching the current head again
creates a self-link and still increments the count. Opaque old head values are
copied without being dereferenced. These are observed field transitions, not an
assertion that every authored state is a valid gameplay world.

The native model requires a nonzero supplied handle present in its record map,
and row 0–18/column 0–66. It validates these conditions before mutation. The
original sign-extends byte coordinates and writes through pointers without those
checks; rejection is a native model safety contract, not recovered error behavior.
No terrain, inventory capacity, spawning, allocation or record-type meaning is
inferred from this routine alone.

## Connected checks

The private oracle runs original attachment instructions, optionally followed by
the original head-removal routine at CODE 7 offset **3872**. Both execute directly,
with no callbacks, services, traps, RNG or result shims. The source is checked
against SHA-256:
`43eb181114493dd938496157cf0943d5fb5d152b56086fb684122fe50385e852`.

**30,552 attachment cases** cover all **1,273 coordinates**, count words 0, 1,
32767, 32768, 65534 and 65535, and four head profiles: null, another handle, the
supplied handle, and 0xffffffff. Initial record coordinates/next pointers and an
occupied cell link are authored. **15,276 cases** then call original removal.
Count, head, record coordinates/next and cell link match the composed native model.
Every other grid/header byte, every other byte of the authored 112-byte record,
and surrounding guards remain unchanged. Return/stack balance and saved registers
are checked. The native driver also checks every unrelated grid byte.

Removing the just-attached head decrements the count and clears its cell link and
next pointer. It does **not** restore the previous occupied cell link, previous
record coordinates or previous next pointer. Tests deliberately avoid claiming
that attach/remove restores the whole input state. The supplied record is not
freed, and arbitrary previous heads are not traversed in these head-removal cases.
Existing non-head removal tests remain separate.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/record_attach_driver.cpp -o dist/record_attach_driver
python tests/research/verify_record_attach.py local-generated/original-resources/manifest.json \
  --native-driver dist/record_attach_driver \
  --output local-generated/analysis/record-attach-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private report path. Original bytes, disassembly and
detailed reports remain ignored. Public tests contain authored records only.
They freeze prepend/count wrap, overwrite behavior, immediate removal, self-link
behavior and unchanged state after invalid coordinate/handle rejection.

Local `sh scripts/test_local.sh` passed **56 Python tests** and native regressions
with both optional graphics decoders available. Rebuilt local CMake targets and
ran CTest: **18/18 ASan/UBSan**, **19/19 SDL** passed. The existing linked-record
test was expanded; no new CTest executable was added. An initial test compilation
failed on an unqualified namespace; it was corrected and all final test binaries
were rebuilt with checks enabled. Production Python tools are unchanged (last
measured coverage 82%). No Android build/runtime, original game boot, Actions
run/upload or release was performed.

The CODE 9 factory allocates/copies template records and performs additional
conditional effects; it remains unmodeled here. Its resources, allocator behavior
and special branches must be recovered before claiming connected glyph creation.
Full generator/progression and original gameplay comparisons also remain open.

The following [common factory-tail increment](RECORD_FACTORY_TAIL.md) recovers
one bounded RNG postprocessing stage before the final template lookup/callback.
It still takes authored record bytes and does not claim allocation or complete
factory/attachment integration.
