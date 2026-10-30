# Supplied-allocation child-record copy — issues #7 and #11

`ChildRecordCopyModel` implements the bounded CODE 9 copy after allocation has
completed. It copies all 56 bytes from a supplied record, then clears the two
four-byte fields at offsets 26 and 30. Every other byte remains the source value.
No ownership, inventory role or historical pointer validity is inferred.

The original function starts at resource-relative offset `0x527e`. The compared
body starts at `0x5290`, immediately after the allocator returns, and includes
its final `RTS` at `0x52b0`. The allocator call at `0x528c` and all earlier
instructions are excluded. The model takes fixed 56-byte source/destination
objects; it neither allocates nor substitutes a return value for an allocator
call. Distinct objects and exact same-object aliasing are supported. Partial
source/destination overlap is outside the native contract and was not compared.

## Native interface

```cpp
mt::ChildRecordCopyModel::Record source{}, destination{};
mt::ChildRecordCopyModel::copy(destination, source);
```

The implementation stages the source before clearing offsets 26 through 33.
A distinct source remains unchanged. Exact self-copy clears those eight bytes
in the same record and preserves its other bytes. Both input objects have a
fixed size, so there is no unchecked external index or allocation-failure path.

## Reproduction

Synthetic checks require only a C++17 compiler:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/child_record_copy_test.cpp -o dist/child_record_copy_test
./dist/child_record_copy_test
c++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -fno-omit-frame-pointer -Iandroid/app/src/main/cpp \
  tests/child_record_copy_test.cpp -o dist/child_record_copy_sanitized_test
./dist/child_record_copy_sanitized_test
```

The optional original-instruction comparison requires a lawfully supplied,
hash-checked local extraction and Unicorn 2.1.4 in the selected Python
environment. It is separate from normal public synthetic tests:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/child_record_copy_probe.cpp -o dist/child_record_copy_probe
python tests/research/verify_child_record_copy.py \
  local-generated/original-resources/manifest.json \
  --native-driver dist/child_record_copy_probe \
  --output local-generated/analysis/child-record-copy/original-comparison-final.json
```

The script refuses an existing report and rejects destinations inside public
checkout paths. Keep reports and original inputs private. No historical bytes
or disassembly are included in the public native test, probe or guide.

## Comparison evidence and boundaries

The local comparison passed **33,280 cases**: 28,672 position/value basis cases,
4,096 seeded random cases and 512 uniform-value cases. There were **16,640
distinct-object and 16,640 exact self-alias cases**. All source/destination bytes
matched the native model. Source/destination guard regions, the supplied frame
and original code remained unchanged except for the destination record.

Execution begins with the allocated destination in D0, the source pointer in
the supplied caller frame, and the original pending allocation arguments on the
stack. No instruction before `0x5290` executes, and no service hook supplies an
allocator result. The oracle bounds execution to the copy body and bounds every
write to the 56-byte destination. It checks D0 returns that destination, A4/A6
are restored, SP reaches the supplied frame plus eight, and the copy-loop source
and destination registers advance by 56 bytes. A 100-instruction cap rejects an
unexpected loop or endpoint.

Both alias modes cover every position/value pair independently. The report
records a SHA256 over all compared result lines for later exact regression
tracking. The final result digest is
`b0d2084efd7c3904a01b47d9ca47fa127d04047b111989cd5cd1488f6a1378f1`.
The CPU translation cache is flushed after hook registration and
before measured execution.

The focused native and ASan/UBSan tests also passed, including guarded distinct
and exact self-alias objects. These results establish the supplied-record copy
boundary, not the original allocator, null/failure behavior, partial overlap,
reference counting, recursive ownership, whole child factory or gameplay.
All GitHub Actions remain paused; validation ran locally.

The integration checkpoint also passed all **84 Python tests with no skips**,
**30/30 native ASan/UBSan CTest checks**, and **31/31 SDL-enabled CTest checks**.
These broader checks cover the research prototype; they do not extend the
original-instruction comparison beyond the supplied-allocation copy body.
