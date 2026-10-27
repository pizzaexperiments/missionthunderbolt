# Synthetic regressions, mutation testing and coverage — issue #22

```sh
sh scripts/test_local.sh
cmake -S . -B dist/sanitizers -DCMAKE_BUILD_TYPE=Debug -DMT_ENABLE_SANITIZERS=ON
cmake --build dist/sanitizers --parallel 4
ctest --test-dir dist/sanitizers --output-on-failure
```

Local GCC ASan/UBSan: **ten native tests passed** (core, API, save, C ABI,
seeded mutations, manual WAIT, and the separate RNG, grid-layout, selector and fallback
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

The current recorded checkpoint is **45 tests passed / 86% coverage**. This is measured Python
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
