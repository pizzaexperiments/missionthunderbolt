# Synthetic regressions, mutation testing and coverage — issue #22

GitHub Actions is currently [paused](../.github/ACTIONS_PAUSED.md), including
manual dispatch. Use local commands and post results in the PR.

## Current local validation

```sh
sh scripts/test_local.sh
cmake -S . -B dist/sanitizers -DCMAKE_BUILD_TYPE=Debug -DMT_ENABLE_SANITIZERS=ON
cmake --build dist/sanitizers --parallel 4
ctest --test-dir dist/sanitizers --output-on-failure
cmake -S . -B dist/sdl -DCMAKE_BUILD_TYPE=Debug -DMT_BUILD_SDL_HOST=ON
cmake --build dist/sdl --parallel 4
ctest --test-dir dist/sdl --output-on-failure
```

The latest [five-child helper](CHILD_CHAIN.md) increment passed **31/31 ASan/UBSan**
and **32/32 SDL** CTest checks locally, plus 84 Python tests with zero skips and
all local native/demo smoke checks. After strengthening the new test, its target
was rebuilt and passed again under both sanitizer and SDL configurations.
The preceding [copy increment](CHILD_RECORD_COPY.md) passed **30/30 ASan/UBSan**
and **31/31 SDL**. The earlier verified native baseline at
**`f67e717`** was **29/29 ASan/UBSan** and **30/30 SDL**; see
[word-selector validation](CHILD_RECORD_WORD_SELECTOR.md).
The coverage refresh itself did not rerun CMake; these native counts come from
the separately completed local native checks. Subsequent targets require their
own build/test evidence; do not infer passed counts from the configured target
list. SDL validation requires SDL2 development files. The mutation test exercises
2,000 corrupt save inputs,
extreme numeric API arguments and locale-independent serialization. All assertions
remain active in Release test targets. No sanitizer assertions are disabled.

Python tests construct resource forks, AppleDouble, indexed PICT and sound
resources synthetically; they test structured truncations and 1,000 seeded
single-byte mutations in addition to format-specific malformed cases. Unexpected
exceptions fail the tests. The corpus contains no original game bytes. ZIP
traversal/failure cleanup and forced Git-index resource additions have regressions.

## Python statement coverage

The parser/tool coverage gate uses coverage.py 7.10.7, includes subprocesses and
requires **80%** statement coverage over Python scripts under `scripts/`, as configured in
`.coveragerc`. Use Python 3.12 and an isolated environment with
`python -m pip install coverage==7.10.7`. Install both ImageMagick (`convert`) and
GraphicsMagick (`gm`) to execute the optional real-decoder tests; an environment
that skips those tests does not have the same decoder coverage as this checkpoint.

The **2026-10-30** baseline measurement at **`f67e717`** passed **84 Python tests,
zero skips**, including both actual decoder checks. The combined report covers
**1,065 of 1,276 statements** with **211 missing**: **83.4639498433%**, displayed
as **83%** by the text report, above the unchanged 80% gate. Six parallel data
files were combined. This is Python statement coverage, not native branch
coverage, Android device coverage or a historical-game fidelity metric.

The copy-guard and five-child increments leave the production Python scripts and synthetic
Python tests unchanged, so this measurement covers those same files on the
current branch. Their optional original-instruction research oracles live
outside the `scripts` coverage source and the synthetic test gate. Neither those
oracles nor the original game instructions are measured by this percentage.

Actual tools were **Python 3.12.14**, **coverage.py 7.10.7** with its C extension,
**GraphicsMagick 1.4 snapshot-20250331 Q16**, and **ImageMagick 7.1.1-43 Q16
x86_64**. The selected private QA environment already contained the pinned
coverage version; no install was needed. Exact local reproduction commands for
that environment are:

```sh
export GRAPHICSMAGICK_EXECUTABLE=/workspace/.cloud-setup/graphicsmagick/usr/bin/gm
export LD_LIBRARY_PATH=/workspace/.cloud-setup/graphicsmagick/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export COVERAGE_FILE="$PWD/dist/coverage/quality-baseline-f67e717/.coverage"
mkdir -p dist/coverage/quality-baseline-f67e717
/workspace/.cloud-setup/qa-python/bin/python -m coverage erase
/workspace/.cloud-setup/qa-python/bin/python -m coverage run -m unittest discover -s tests -p 'test_*.py' -v
/workspace/.cloud-setup/qa-python/bin/python -m coverage combine
/workspace/.cloud-setup/qa-python/bin/python -m coverage report
/workspace/.cloud-setup/qa-python/bin/python -m coverage json -o dist/coverage/quality-baseline-f67e717/coverage.json
/workspace/.cloud-setup/qa-python/bin/python -m coverage xml -o dist/coverage/quality-baseline-f67e717/coverage.xml
```

The interpreter and decoder paths above are machine-specific; substitute your
own isolated Python and installed GraphicsMagick paths on another host.
`coverage erase` clears only the selected checkpoint's data, avoiding accidental
mixing with previous measurements. Raw reports remain under ignored `dist/`.
The disabled manual quality workflow describes the same gate and native
sanitizers; it was not enabled or triggered. Existing deterministic seed/action/save
checks are demo regressions. Original-vs-port differential traces, screenshot
goldens and recovered gameplay coverage still require #6–#12 research. Standalone
mutation runs are not a substitute for an ongoing coverage-guided fuzz campaign.

## Optional coverage-guided parser target

Atheris 3.1.0 provides bytecode coverage feedback to its bundled libFuzzer. The
optional harness exercises resource-fork, AppleDouble/AppleSingle, indexed PICT
and sound parsing in memory. It accepts documented ValueError rejections;
unexpected exceptions, invariant failures, timeouts and memory limits fail the
campaign. It does not require or read the historical archive.

```sh
python -m pip install --only-binary=:all: atheris==3.1.0
python tests/fuzz_parsers.py --seed-corpus dist/fuzz-parsers-corpus
mkdir -p dist/fuzz-parsers-artifacts
python tests/fuzz_parsers.py dist/fuzz-parsers-corpus \
  -max_total_time=120 -max_len=4096 -timeout=10 -rss_limit_mb=1024 \
  -seed=1703 -print_final_stats=1 -artifact_prefix=dist/fuzz-parsers-artifacts/
```

Seed generation refuses existing directories and creates eleven authored fixtures
or minimal rejection cases. Retain/minimize discoveries under ignored `dist/`;
turn confirmed defects into small synthetic regression cases. This optional
Linux/Python campaign does not replace the native ASan/UBSan suite, longer-running
scheduled campaigns, large-input testing or original differential goldens.

### Historical campaign result — 2026-10-26

That local campaign completed **1,722,666 executions in 121 seconds**,
with no unexpected exception, failed invariant, crash/timeout artifact or memory-
limit failure. Final libFuzzer feedback was `cov: 335`, `ft: 837`, 218 retained
corpus units and **71 MB peak RSS**. These are campaign feedback counters, not
percent statement coverage and not evidence of historical fidelity. The separate
unit-test coverage figure above is measured independently.

## Historical native and research checkpoints

An earlier GCC ASan/UBSan checkpoint passed **sixteen native tests** (core, API,
save, C ABI, seeded mutations, manual WAIT, and the separate RNG, grid-layout,
selector, fallback, linked-record, release, connected lifecycle, A5 initialization,
glyph preparation and basic cell conversion research models). The earlier
**56 Python tests / 82% statement coverage** checkpoint is superseded by the
dated measurement above. The increment-specific results below remain historical
evidence, not current suite counts.

The connected direct-grid increment (2026-10-27) passed **17/17 ASan/UBSan**
and **18/18 SDL** CTest checks, plus 56 Python tests and native smoke tests.
Its optional private original-instruction comparison matched 131,072 base-word
probes and 111 complete grids/141,303 cells. See DIRECT_GRID_CONVERSION.md for
scope and reproduction; this does not establish full generator/gameplay fidelity.

The six-branch level-word increment (2026-10-27) passed **18/18 ASan/UBSan**,
**19/19 SDL** and 56 Python tests plus native checks. Its private connected oracle
matched 188 maps/239,324 cells and 57,618 original RNG events with complete state
comparison. The default direct-only oracle also passed again. Commands/scope:
LEVEL_GRID_CONVERSION.md. Actions remains disabled; evidence is posted in the PR.

The supplied-record prepend increment expands the existing linked-record native
test. Local checks passed 56 Python tests plus native regressions, **18/18
ASan/UBSan** and **19/19 SDL**. The private original comparison matched **30,552
attachments**, including **15,276 attach/head-removal sequences** and preserved
bytes/guards. See RECORD_ATTACHMENT.md for commands, the corrected initial test
compile failure and factory/ownership limitations. No Actions run was used.

The common factory-tail increment passed **19/19 ASan/UBSan**, **20/20 SDL**
and 56 Python tests plus native checks. The private connected oracle matched
2,002 records, 727 zero-result paths and 7,091 tail draws, comparing all output
bytes and complete RNG state. It also executed 65,472 authored warm-up draws
outside the measured tail. Scope/commands: RECORD_FACTORY_TAIL.md. No Actions
were used; whole-factory or gameplay fidelity is not established.

The supplied-allocation template-factory increment passed **20/20 ASan/UBSan**,
**21/21 SDL**, 56 Python tests and native regressions. Private original checks
matched 32,768 copy probes plus 1,960 connected cases/6,531 draws/971 callback
boundaries; the prior standalone tail oracle also passed again. Scope, commands
and unrun factory stages: RECORD_TEMPLATE_FACTORY.md. No Actions were used.
