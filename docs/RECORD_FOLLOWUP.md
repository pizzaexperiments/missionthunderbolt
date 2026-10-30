# Factory follow-up child selection

`RecordFollowupModel` models CODE 7 entry 9972 (0x26f4), A5 jump 0xb92.
It reads an authored 112-byte parent, up to 13 child handles in slots +60 onward,
and explicit source-template flags and signed threshold metadata. It does not
infer equipment, inventory, combat or spawning semantics. No RNG, allocation,
service callback or child mutation occurs in this routine.

For parent type word 72, a reverse scan first considers children with nonzero
byte +18. If signed child word +8 exceeds the threshold selected by the parent's
signed byte +18, parent byte +18 becomes child byte +1 and that scan stops. This
is the first eligible reverse slot, not a maximum over children.

The routine always clears parent byte +22 and bit 5 of byte +20. If source-template
byte +20 bit 5 is set, it reverse-scans children for the greatest signed word +16,
requiring a value greater than 1, zero word +8, clear bit 1 in child bytes +24/+25
and clear bit 3 in +24. Strict comparison retains the highest slot on ties.
A selection sets parent byte +22 to its slot and bit 5 of +20. Slot zero is valid;
the flag distinguishes it from no selection. All other parent and child bytes
are preserved except the special type-72 update.

The native model validates type 0–75, child count 0–13 and required supplied
handles before mutation. Negative/out-of-buffer counts and missing handles are
model safety rejections, not original error behavior. Paths that do not inspect
children need not supply their handles. Thresholds cover all 256 byte patterns;
the oracle maps them to authored metadata rows at signed-byte offsets from the
supplied base. Actual original resource bounds and metadata meanings remain unknown.

## Local evidence

Original CODE 7 SHA-256:
`43eb181114493dd938496157cf0943d5fb5d152b56086fb684122fe50385e852`.
The oracle executes the original routine through return, with no result shims.
**11,133 cases** cover counts 0–13, multiple types/template gates, byte and signed
word boundaries, flag sweeps, all signed-byte metadata indices, threshold/child
comparison edges and equal-score reverse selection. Every output parent byte
matches. Source templates, metadata, child bytes, pointers and guards remain
unchanged; stack balance and saved registers are checked.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/record_followup_driver.cpp -o dist/record_followup_driver
python tests/research/verify_record_followup.py local-generated/original-resources/manifest.json \
  --native-driver dist/record_followup_driver \
  --output local-generated/analysis/record-followup-crosscheck.json
```

Use Unicorn 2.1.4 and a fresh private report path. All records, tables and histories
are authored; original bytes/disassembly/detailed reports stay ignored. Public
regressions freeze reverse ties, slot-zero selection, flag gates, the type-72
first match and unchanged records after invalid inputs. Local tests passed
56 Python tests plus native regressions, 21/21 ASan/UBSan and 22/22 SDL checks,
with both optional picture decoders. No failures/skips occurred. No Android
build/runtime, original game boot, Actions run/upload or release was performed.

The source-template flag determines whether the factory calls this routine.
Connecting that call to the supplied-allocation factory is the next dependent
increment; original allocation, child creation and unsupported variants remain
unfinished. GitHub Actions remains disabled. Sequential stacked PRs are explicitly
authorized; merging still requires maintainer approval.

The dependent [factory composition](FINALIZED_TEMPLATE_FACTORY.md) connects this
routine through original CODE 9, including 670 actual original callback calls.
