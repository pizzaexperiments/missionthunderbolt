# Codex / contributor instructions

This is a **research prototype**, not a faithful port yet. Treat all gameplay as synthetic unless traced to source evidence. Source prototype is under `android/app/src/main/cpp/`, Android host in `android/app/src/main/java/`; tests in `tests/`.

## How to work
1. Read `README.md`, `docs/ROADMAP.md`, `docs/API.md`, and the selected GitHub issue.
2. Make a small plan and a single-purpose pull request referencing the issue.
3. Add deterministic unit tests for engine/parser changes. Run:
   ```sh
   g++ -std=c++17 -Wall -Wextra -Werror android/app/src/main/cpp/game.cpp tests/core_test.cpp -o /tmp/mt-core && /tmp/mt-core
   g++ -std=c++17 -Wall -Wextra -Werror android/app/src/main/cpp/game.cpp android/app/src/main/cpp/api.cpp tests/api_test.cpp -o /tmp/mt-api && /tmp/mt-api
   ```
4. For Android, install Java 17, SDK platform 35, build-tools 35.0.0, NDK 27.2.12479018, CMake 3.22.1, Gradle 8.7 and run `cd android && gradle --no-daemon assembleDebug`. Record exact CI run.
5. PR description must include test results, screenshots/logs where relevant, risks, unresolved gaps, and no unverified claims.

## Proprietary input boundaries
- Do **not** commit, embed, attach to public GitHub issues, upload as Actions artifact, or include in publicly downloadable APK any original game executable/resources/PICT/snd/manual/StuffIt archive unless the contributor documents redistribution permission.
- Keep original inputs in local `local-original/` (ignored), and generated derivatives in `local-generated/` (ignored).
- Parser tests should use synthetic fixtures.
- Users who lawfully possess the game may import their local archive for research. Do not circumvent DRM or attempt to acquire unauthorized assets.

## Product goals
- First produce an installable **synthetic demo** Android APK with CI.
- Then recover original behavior through documented, independently verifiable analysis.
- Two UIs (Classic and Modern) share one deterministic rules engine.
- Portable C++ core; native Android, Windows and macOS host apps; no runtime Mac emulator.
- Stable in-process C ABI already exists. HTTP API is optional (#24).
