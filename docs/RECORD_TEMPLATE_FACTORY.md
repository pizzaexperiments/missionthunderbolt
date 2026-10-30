# Supplied-allocation template factory — issues #7, #8 and #11

`RecordTemplateFactoryModel` connects template selection/copy, a supported subset
of pure variant branches, the recovered RNG tail, and the final follow-up gate.
The original comparison starts at CODE 9 offset **0x00bc**, after allocation and
after the supplied destination pointer has been loaded. It includes the original
eight-byte allocation-argument cleanup. It stops at **0x1334** if a callback is
required, otherwise at **0x133c**, before pointer return/register restoration.
No allocator, child creator, final callback or whole-factory return is simulated.
The active demo is unchanged.

## Three different indices/values

- The nonnegative signed-word **variant** selects a copy source: 0–75 copy their
  own 112-byte slot; 76–32767 copy slot zero. This is a signed comparison.
- The same variant selects the type-specific dispatch: 0–88 use its table;
  89–32767 skip directly to the common tail. Copying slot zero does not reset the
  variant used by this dispatch.
- The copied **word at record +0** selects descriptor byte `type*12+8` and later
  template byte `type*112+20`. These lookups need not use the copy-source index.

The model's supplied table has 76 authored slots and restricts copied type words
to 0–75. That is the tested model domain, not a claim about original resource
counts or the validity of all historical templates. A nonzero descriptor byte
would enter unresolved child creation; the model rejects it before output/RNG
mutation. Negative/out-of-word variants, invalid caller words/type indices and
unsupported variant branches also reject before mutation. These are model
capability/safety contracts, not original error handling.

The model copies the entire selected record and clears output byte +20 bit 5.
It supports **65 variants below 89**: 49 go directly to the common tail; eight
share a byte +21 bit-4 set; eight more cover raw flag/field adjustments. Those
additional adjustments include variants 35/46 sharing signed division by five,
variant 38 adding arithmetic half of the caller word, and variant 65 adding the
**sign-extended low word** of `100*caller` to long +4. Variant 39 tests global byte
A5−0x9e8. Field writes, shifts/division rounding and width wrap are modeled without
assigning terrain, item, enemy or progression meanings.

After the common RNG tail, the follow-up gate tests bit 5 in the **source template
indexed by the copied type word**. It does not test the cleared output flag. The
model returns `requires_followup` but never calls or supplies a callback result.
The supplied destination is separate from the immutable authored source table.

## Connected local evidence

- **32,768 template-copy probes**, every nonnegative word variant, compare all
  112 copied bytes and the original final source pointer, with source/output
  guards, context registers and stack balance checked. This bounded copy test
  includes variants whose later effects remain unsupported.
- **1,960 connected factory cases** cover all 65 supported variants below 89,
  five fallback variants (89, 90, 255, 256, 32767), 14 signed caller-word values
  and two flag/table-type profiles. The second profile remaps copied type words
  to separate copy selection from descriptor/final-template lookup.
- Every output byte, selected source index, complete RNG state, ordered draw trace
  and follow-up predicate match. There were **653 zero-result paths**, **6,531
  tail draws**, and **971 required-follow-up boundaries**. The other 989 cases
  stop at the no-callback endpoint. No final callback was executed or shimmed.

All template and descriptor bytes are authored. The descriptor child byte is zero
in connected cases; public regressions separately test atomic rejection for a
nonzero byte. Original CODE 9 prefix/dispatch/tail and original CODE 1/5/12 RNG
initialization, arithmetic and wrappers execute directly. Authored warm-up draws
and table profiles are explicit inputs. Unmodeled services fail. The callback
observer stops execution before the push/call; it does not provide a result.
Templates/descriptors/pointers/global/frame bytes, guards, caller words, stack,
registers and endpoints are checked. Source hashes must match the preceding
factory-tail oracle's CODE 1/5/9/12 fingerprints.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp \
  tests/research/record_template_factory_driver.cpp -o dist/record_template_factory_driver
python tests/research/verify_record_template_factory.py local-generated/original-resources/manifest.json \
  --native-driver dist/record_template_factory_driver \
  --output local-generated/analysis/record-template-factory-final.json
```

Use Unicorn 2.1.4 and a fresh private report path. Original resources, dispatch
bytes, disassembly and detailed reports remain ignored. Public tests freeze
fallback selection, distinct copy/type lookups, source-vs-output follow-up flags,
word truncation, signed shifts/division and atomic rejection using authored data.

The earlier bounded tail oracle was rerun after adding explicit setup/inspection
and endpoint parameters: **2,002 records / 727 zero paths / 7,091 tail draws**
still match. Its default entry/endpoints and guards remain in force. Local suites
passed **56 Python tests** plus native regressions, **20/20 ASan/UBSan**, and
**21/21 SDL** checks, with both optional external picture decoders. No failures
or skips occurred. Production Python tools are unchanged (last coverage 82%).

Allocation, original templates, child creation, 24 unsupported variants below 89,
the follow-up callback, factory/creation-glyph integration, progression and
original gameplay comparisons remain unfinished. No Android build/runtime,
original game boot, Actions run/upload or release was performed. All five Actions
workflows remain disabled.
