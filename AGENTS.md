# Codex and contributor operating guide

## Branch policy — mandatory
- `develop` is the default **integration** branch.
- Start all implementation branches from the current `develop` head, using `feature/<topic>` or `fix/<topic>`.
- For this active workstream, use `feature/offline-research-tooling`; do not commit directly to `develop` or `main`.
- When work has passed review and local verification, open a PR **feature → develop**. Merge only with approval.
- `main` is release-only. When a release is ready, open a reviewed **develop → main** PR. No direct commits to `main`.
- GitHub Actions credits are unavailable; workflow is manually triggered only. Run tests locally and put test evidence in PRs.

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
