# Bounded supplied-record child chain — issues #7 and #11

`ChildChainModel` composes the CODE 9 helper at `0x4e00` through its `RTS` at
`0x4eca` for an explicitly empty old parent field +30. It invokes the existing
supplied-allocation child factory five times, maintaining one shared RNG and
explicit context. It does not enable raw type 36 in `ChildRecordFactoryModel`;
the outer factory's type-36 dispatch remains rejected.

The helper's nonempty-old-branch path calls recursive release logic. That domain
is excluded: a nonzero parent long +30 is rejected before any outputs or state
change. The model never releases, allocates, dereferences a historical handle,
or assigns inventory meaning to the records.

## Composed operations

Each child factory receives level 1 and the following template variant. Its
prefix/type dispatch completes before the helper's one-based overwrite draw.
Only word +10 is overwritten; earlier factory changes to other fields remain.

| Child | Template variant | One-based bound | Bias added to word +10 draw |
| --- | --- | --- | --- |
| 1 | 31 | 200 | 200 |
| 2 | 27 | 50 | 25 |
| 3 | 28 | 50 | 25 |
| 4 | 37 | 200 | 100 |
| 5 | 72 | 25 | 25 |

Parent long +30 becomes the first supplied handle. Long +26 in each of the
first four records points to the next supplied handle. The fifth record's
long +26 is retained from its completed factory result; the model does not
invent a terminal null or traverse that raw value.

Template variants select supplied records, not assumed type numbers. A selected
template may take any dispatch branch supported by the existing context-aware
factory. Nested types 36, 70 and 166 remain unsupported and are rejected during
prevalidation. No historical template or lookup bytes are provided.

## Native contract

```cpp
mt::ChildChainModel::Record parent{};
mt::ChildChainModel::Records children{}; // five fixed 56-byte records
mt::ChildChainModel::Handles handles{{0x20000,0x20038,0x20070,0x200a8,0x200e0}};
// templates, rng and context are supplied authored research inputs.
auto result=mt::ChildChainModel::prepare(parent,0x10000,children,handles,
                                        templates,rng,context);
```

All six logical record handles must be nonzero and word-aligned. Their 56-byte
ranges must be disjoint and fit in the unsigned 32-bit address space. These
values are symbolic inputs, not host addresses or ownership claims. The parent
must occupy a distinct host object from the five children, and no output record
may be the same object as a supplied template. Partial host overlap is outside
the fixed-object contract.

Parent, all five output records, RNG and context are staged and published only
after successful composition. Validation failures preserve every caller input.
The result contains the ordered bound/mode/result draw trace: each factory's
trace followed by that child's helper overwrite draw. `factory_draw_counts`
records the five factory trace lengths, allowing their boundaries to be checked.
The explicit context retains the factory's raw lookup/factor/counter/address
contract; it does not supply original startup values.

## Local checks

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/child_chain_test.cpp -o dist/child_chain_test
./dist/child_chain_test
c++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -fno-omit-frame-pointer -Iandroid/app/src/main/cpp \
  tests/child_chain_test.cpp -o dist/child_chain_sanitized_test
./dist/child_chain_sanitized_test
```

Both focused commands passed. Authored tests cover an exact forced RNG trace,
all five links and overwrite counts, preservation of the fifth copied long +26,
128 composed shared-state cases, counter/address wrapping, and rejection of
invalid handles, unsupported nested dispatch, old nonempty branches and host
aliasing. Source templates and unaffected parent bytes are preserved.

The separate original-instruction comparison must state its supplied-allocation
boundary explicitly: each child factory's allocator call is excluded, a supplied
destination is substituted at that boundary, and original post-allocation
instructions resume. Such a comparison cannot establish allocator success,
allocation failure, ownership/release behavior or the outer type-36 factory.
Detailed original-derived reports and disassembly remain private. Historical
inventory semantics, recursive cleanup and original gameplay remain open.
All validation runs locally while GitHub Actions is paused.

## Original-instruction comparison — 2026-10-30

Unicorn 2.1.4 matched **771 cases, 3,855 children and 12,292 ordered RNG draws**.
The largest case used 37 draws, and the largest child factory used its full
11-draw path. Parent and all five complete records, all 103 RNG state words,
context counter, ordered draws and per-factory draw counts matched the native
model. Source tables, read-only context, record/RNG/stack guards, original code,
return registers, child-call ABI and retained fifth long +26 were checked.

There were exactly **3,855 explicit supplied-allocation substitutions**: five
per case. Execution stops before each allocator `JSR` at `0x4848`, verifies its
pending arguments `(1,56)`, supplies the chosen destination in D0 and resumes at
`0x484c`. The original register move, factory copy/prefix/dispatch, helper and
RNG instructions then execute. The allocator itself and the nonempty-old-branch
release path do not execute. No RNG result is substituted. This boundary is
part of the comparison's scope, not proof of historical allocation behavior.

Complete-output digest:
`11968f26224d9715b69914a9ac31e1f62f262833c5395536784a4556a7d6b456`.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/child_chain_probe.cpp -o dist/child_chain_probe
python tests/research/verify_child_chain.py \
  local-generated/original-resources/manifest.json \
  --native-driver dist/child_chain_probe \
  --output local-generated/analysis/child-chain-crosscheck.json
```

The integration checkpoint passed **84 Python tests with no skips**, native
smoke tests, **31/31 ASan/UBSan CTest checks** and **32/32 SDL CTest checks**.
After strengthening the frozen full-record and rejection-atomicity tests, both
native and SDL child-chain targets were rebuilt and their focused checks passed.
The synthetic full-record checks explicitly retain factory word +14 even when
the helper overwrites word +10; the helper does not recompute that earlier field.
