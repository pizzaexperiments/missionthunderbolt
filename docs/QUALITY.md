# Synthetic regressions, mutation testing and coverage — issue #22

GitHub Actions is currently [paused](../.github/ACTIONS_PAUSED.md), including
manual dispatch. Use local commands and post results in the PR.

```sh
sh scripts/test_local.sh
cmake -S . -B dist/sanitizers -DCMAKE_BUILD_TYPE=Debug -DMT_ENABLE_SANITIZERS=ON
cmake --build dist/sanitizers --parallel 4
ctest --test-dir dist/sanitizers --output-on-failure
```

Local GCC ASan/UBSan: **sixteen native tests passed** (core, API, save, C ABI,
seeded mutations, manual WAIT, and the separate RNG, grid-layout, selector, fallback, linked-record, release, connected lifecycle, A5 initialization, glyph preparation and basic cell conversion
research models). The mutation test exercises 2,000 corrupt save inputs,
extreme numeric API arguments and locale-independent serialization. All assertions
remain active in Release test targets. No sanitizer assertions are disabled.

Python tests construct resource forks, AppleDouble, indexed PICT and sound
resources synthetically; they test structured truncations and 1,000 seeded
single-byte mutations in addition to format-specific malformed cases. Unexpected
exceptions fail the tests. The corpus contains no original game bytes. ZIP
traversal/failure cleanup and forced Git-index resource additions have regressions.

The parser/tool coverage gate uses coverage.py 7.10.7, includes subprocesses and
requires **80%** statement coverage over all Python scripts:

```sh
python -m pip install coverage==7.10.7
mkdir -p dist/coverage
export COVERAGE_FILE="$PWD/dist/coverage/.coverage"
python -m coverage run -m unittest discover -s tests -p 'test_*.py' -v
python -m coverage combine
python -m coverage report
```

The current recorded checkpoint is **56 tests passed / 82% coverage**. This is measured Python
statement coverage, not native branch coverage or a fidelity metric. The
manual-only quality workflow runs the same gate and combined native sanitizers;
it has not been triggered in this task. Existing deterministic seed/action/save
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

The 2026-10-26 local campaign completed **1,722,666 executions in 121 seconds**,
with no unexpected exception, failed invariant, crash/timeout artifact or memory-
limit failure. Final libFuzzer feedback was `cov: 335`, `ft: 837`, 218 retained
corpus units and **71 MB peak RSS**. These are campaign feedback counters, not
percent statement coverage and not evidence of historical fidelity. The separate
unit-test coverage figure above is measured independently.

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
