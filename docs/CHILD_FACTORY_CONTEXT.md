# Explicit child-factory context — issues #7/#11

The supplied-allocation [child factory](CHILD_RECORD_FACTORY.md) now has an
explicit `Context&` overload for raw types 37, 77, 137 and 138. Calls without
context retain the previous capability boundary and reject those types. Both
forms still reject types 36, 70 and 166, which need unresolved external or
recursive services. No original tables or allocator are supplied.

The authored context contains fifty raw lookup bytes, a raw factor word, a
counter word and an arithmetic address base. These are explicit inputs, not
recovered startup values or established item properties. The address value is
never dereferenced by the native model. Record, RNG and context publish together
only after success.

| Raw type | Context-dependent operation after prefix |
| --- | --- |
| 37 | A zero-based-50 draw selects a lookup byte and replaces word +8. Lookup values other than 2, 4, 6 and 33 permit a zero-based-5 test; if zero, one-based-3 replaces word +10 and multiplies word +14 with word truncation. Negative signed-byte values are eligible too. |
| 77 | Caller low byte replaces byte +2. A positive signed caller word sets word +8 to 7, subtracts 7 from byte +6, sets byte +7 to 4 and adds 10 to word +16; otherwise word +8 becomes 10. Word +4 receives the truncated signed-byte +7 × signed context factor product. |
| 137, 138 | Increment the context counter with word wrap and copy it to word +40. Long +42 becomes address base +5000−zero-based-500 with long wrap. Set byte +24 bit 3. |

The maximum composed trace is eleven draws. A context supplied to a previously
supported type remains unchanged unless that type explicitly updates it.

## Local verification — 2026-10-30

Unicorn 2.1.4 original instructions matched **1,725 cases / 3,621 draws**,
including the eleven-draw path and all twelve required context branch blocks.
Cases cover all 256 lookup-byte values and all fifty indexes against distinct
neighboring lookup inputs, signed caller/byte/factor edges, counter overflow and
address wrapping. Full record, ordered bound/mode/result, complete RNG state and
counter match. Lookup bytes, external factor data/pointer, base address, source
tables, frame, stack and output guards are enforced; no helper results are
shimmed. CODE 1/5/9/12 fingerprints match the preceding factory oracle.

Complete-output digest:
`b2093242381d2e5b6d7378d30d82beacc91dbd939ce54bb6bf9610215f367e1e`.
Private inputs, listings and detailed reports remain ignored.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/child_factory_context_probe.cpp -o dist/child_factory_context_probe
python tests/research/verify_child_factory_context.py \
  local-generated/original-resources/manifest.json \
  --native-driver dist/child_factory_context_probe \
  --output local-generated/analysis/child-factory-context-crosscheck.json
```

The shared oracle accepts context only in explicit factory mode. Default prefix
**1,458 cases / 4,368 draws** and no-context factory **2,096 cases / 5,302 draws**
were rerun with their previous digests unchanged. Local native regressions and
full **28/28 ASan/UBSan**, **29/29 SDL** checks passed. Per-PR Python/smoke results
are recorded with the PR.

Historical table values, allocation, remaining service-dependent types, parent
integration, inventory semantics and original-game comparisons remain incomplete.
The active demo and Android host are unchanged; no new Android verification,
Actions execution, merge, signing or publication is claimed by this increment.

The separate [five-child chain helper](CHILD_CHAIN.md) composes supported child
factories with supplied records when the parent's old child pointer is null.
It does not enable raw type 36 in this factory API: replacement/release and the
outer factory composition remain outside that bounded helper.
