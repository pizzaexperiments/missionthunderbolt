# Synthetic regressions, mutation testing and coverage — issue #22

```sh
sh scripts/test_local.sh
cmake -S . -B dist/sanitizers -DCMAKE_BUILD_TYPE=Debug -DMT_ENABLE_SANITIZERS=ON
cmake --build dist/sanitizers --parallel 4
ctest --test-dir dist/sanitizers --output-on-failure
```

Local GCC ASan/UBSan: **five native tests passed** (core, API, save, C ABI and
seeded mutations). The mutation test exercises 2,000 corrupt save inputs,
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

The current recorded checkpoint is **38 tests passed / 84% coverage**. This is measured Python
statement coverage, not native branch coverage or a fidelity metric. The
manual-only quality workflow runs the same gate and combined native sanitizers;
it has not been triggered in this task. Existing deterministic seed/action/save
checks are demo regressions. Original-vs-port differential traces, screenshot
goldens and recovered gameplay coverage still require #6–#12 research. Standalone
mutation runs are not a substitute for an ongoing coverage-guided fuzz campaign.
