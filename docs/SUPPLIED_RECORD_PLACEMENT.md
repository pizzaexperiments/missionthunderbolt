# Prepared supplied record through list/grid placement

`SuppliedRecordPlacementModel` composes the supplied-allocation factory, actual
follow-up model and recovered list/grid attachment. The caller supplies an
existing nonzero destination handle, record storage, templates/descriptors,
children, metadata, RNG and valid grid coordinates. It does not allocate a record
or execute an original glyph caller.

The factory stages produce the record, then attachment increments header count
with word wrap, prepends the destination handle, overwrites target-cell long +12
and writes the raw record's coordinates/next link. The logical node view and full
112-byte record stay consistent. An occupied link is not released/restored, and
an old head equal to the destination produces the original self-link behavior.
The factory result retains whether its source-template gate requested follow-up;
that follow-up has already executed when the flag is true.

Destination, RNG, header, grid and node publication are staged. Missing supplied
handles, invalid coordinates, unsupported factory inputs or missing required
children reject before the caller's state changes. This transaction is native
model safety behavior, not original rollback semantics.

## Sequential original-instruction comparison

The oracle executes the original supplied-allocation CODE 9 factory stage,
including actual original CODE 7 follow-up calls. It then authors a separate ABI
call frame for original CODE 7 entry 3794 and runs attachment through return.
This is a comparison of sequential original stages; the original factory return
ABI, allocator and surrounding glyph caller are **not** executed or claimed.
No allocator/callback/RNG result is supplied by an observation hook.

All **1,005 cases** match final record bytes, header count/head, cell link, selected
template, complete RNG state and trace. The cases include **670 original
follow-up calls** and **3,350 factory RNG draws**. Five corner/row-edge coordinate
profiles, four count-word profiles and three head profiles cover wrap, null/
opaque/self heads and overwritten occupied links. All unrelated grid/header
bytes, record/child/source guards and metadata remain checked. Attachment is
separately checked to leave RNG unchanged and preserve caller registers/stack.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/supplied_record_placement_driver.cpp -o dist/supplied_record_placement_driver
python tests/research/verify_supplied_record_placement.py local-generated/original-resources/manifest.json \
  --native-driver dist/supplied_record_placement_driver \
  --output local-generated/analysis/supplied-record-placement-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private report path. Source fingerprints match the
preceding finalized-factory oracle. All templates/records/children/worlds are
authored. Original bytes, disassembly and detailed evidence remain ignored.
Public regressions freeze callback-plus-placement results, occupied-cell/count
wrap behavior, coherent raw/node links and unchanged state after rejected input.

Local suites passed 56 Python tests plus native regressions, 23/23 ASan/UBSan
and 24/24 SDL checks with both optional picture decoders. No failures/skips
occurred in this increment. Production Python tools are unchanged (last coverage
82%). No Android build/runtime, original game boot, Actions run/upload or release
was performed. All five Actions workflows remain disabled.

This PR targets `feature/factory-followup-stack` (PR #43), which targets
`feature/record-followup` (PR #42). Review/merge in that order, retargeting dependent
PRs to `develop` as predecessors land. New work need not wait for those merges.
Allocator/child creation, unsupported variants, full glyph/progression integration
and original gameplay validation remain unfinished. The active demo is unchanged.
