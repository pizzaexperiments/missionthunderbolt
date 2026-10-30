# Codex and contributor operating guide

## Branch policy — mandatory
- `develop` is the default **integration** branch.
- Start independent implementation branches from current `develop`, using `feature/<topic>` or `fix/<topic>`.
- The maintainer authorizes sequential stacked PRs: dependent branches may start from the preceding PR head and target its branch. Document the dependency, keep each diff reviewable, and continue without waiting for merges.
- Open independent PRs **feature → develop** and dependent PRs **feature → predecessor** after local verification. Do not commit directly to `develop` or `main`. Merge only with approval.
- `main` is release-only. When a release is ready, open a reviewed **develop → main** PR. No direct commits to `main`.
- GitHub Actions is paused: all five workflows are disabled. Do not enable or dispatch any workflow unless the maintainer explicitly requests it. Run tests locally and post exact results in the PR; see `.github/ACTIONS_PAUSED.md`.

## Project reality
This is a research prototype, **not** a faithful reconstruction. Do not claim old game logic is implemented without corroborating original reference behavior. Do not claim a verified APK without a build artifact and device/emulator test.

## Local tests
```sh
sh scripts/test_local.sh
```
Requires Python 3 and a C++17 compiler. Output in ignored `dist/`.

## Work on issues
Read `README.md`, `docs/ROADMAP.md`, `docs/LOCAL_TESTING.md`, and the assigned issue. Deliver small, separately reviewable changes with tests and precise verification evidence. Document blockers and uncertainty.

## Copyright and original assets
Do not publish, commit, embed in releases, or attach commercial game binaries/resources/audio/manuals without determining rights. Local archive import goes in ignored `local-original/`; derived data under ignored `local-generated/`. Synthetic fixtures are preferred for public tests.

## Release targeting
Native Android first, Windows/macOS later, with a portable C++ engine and Classic/Modern UI. No Mac emulation at runtime. External HTTP API is optional; in-process C ABI already exists.

## Verification and definition of done
- Use the existing isolated checkout; do not create a Git worktree unless requested.
- Read the selected issue and linked evidence; make an issue-sized plan before editing.
- Run `sh scripts/test_local.sh`; use root CMake/CTest for C ABI, sanitizer and SDL checks.
  Android uses Java 17, Gradle 8.7, SDK/target 35, build-tools 35.0.0,
  NDK 27.2.12479018 and CMake 3.22.1; see docs/ANDROID_DEVELOPMENT.md.
- Keep original inputs and derivatives ignored. Run `python3 scripts/check_public_inputs.py --staged`
  and review staged paths/content before committing; path checks do not grant rights.
- Add deterministic regressions for engine/parser changes, with no proprietary fixtures.
  Never disable assertions, integrity checks or failing checks to claim readiness.
- Record exact commands, test counts, platform/ABI, failures/skips/unrun checks and artifact
  identity where relevant. Build, install, launch, gameplay fidelity and release signing
  are separate claims. Manual 1.0 and executable 2.0.g are not assumed equivalent.
- A reviewable commit/PR references its issue, explains behavior and validation, records
  remaining gaps and includes only shareable evidence. Do not mark an issue complete
  while original-specific acceptance is untested. Keep docs/ROADMAP.md current.
- Do not run GitHub Actions while the pause is in effect, including manual dispatch.
  Billing-cycle resets do not authorize re-enabling it. No automatic push/PR CI or
  release publication. Merge requires maintainer approval.
