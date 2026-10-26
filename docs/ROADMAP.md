# Mission Thunderbolt native port master plan

**Status (October 26, 2026):** C++ core/API tests passing; Android CI SDK setup failing before APK build (run 40402366349). The code is a synthetic demonstration, **not** original gameplay. No installable APK has been verified.

## Milestones and execution order

### M0 — Reproducible research demo APK (highest priority)
- [#1](https://github.com/pizzaexperiments/missionthunderbolt/issues/1) fix Android CI and emit debug APK
- [#2](https://github.com/pizzaexperiments/missionthunderbolt/issues/2) local build/device testing
- [#25](https://github.com/pizzaexperiments/missionthunderbolt/issues/25) Codex contributor instructions
- [#14](https://github.com/pizzaexperiments/missionthunderbolt/issues/14) modular native engine
- Android app issues [#17](https://github.com/pizzaexperiments/missionthunderbolt/issues/17), [#18](https://github.com/pizzaexperiments/missionthunderbolt/issues/18)

### M1 — Authorized game input and evidence
- [#3](https://github.com/pizzaexperiments/missionthunderbolt/issues/3) legal provenance and local-only asset workflow
- [#4](https://github.com/pizzaexperiments/missionthunderbolt/issues/4) resource parser and inventories
- [#5](https://github.com/pizzaexperiments/missionthunderbolt/issues/5) PICT decoder and catalog
- [#6](https://github.com/pizzaexperiments/missionthunderbolt/issues/6) original gameplay behavior reference
- [#7](https://github.com/pizzaexperiments/missionthunderbolt/issues/7) 68K/CREL call graph
- [#13](https://github.com/pizzaexperiments/missionthunderbolt/issues/13) audio decoding

### M2 — Faithful gameplay replacing the demo
- [#8](https://github.com/pizzaexperiments/missionthunderbolt/issues/8) map generation/progression
- [#9](https://github.com/pizzaexperiments/missionthunderbolt/issues/9) movement/turns/FOV
- [#10](https://github.com/pizzaexperiments/missionthunderbolt/issues/10) combat
- [#11](https://github.com/pizzaexperiments/missionthunderbolt/issues/11) items/inventory
- [#12](https://github.com/pizzaexperiments/missionthunderbolt/issues/12) enemy/ally AI
- [#15](https://github.com/pizzaexperiments/missionthunderbolt/issues/15) save/load
- [#16](https://github.com/pizzaexperiments/missionthunderbolt/issues/16) faithful Classic UI

### M3 — Portable distribution and quality
- [#19](https://github.com/pizzaexperiments/missionthunderbolt/issues/19) Windows
- [#20](https://github.com/pizzaexperiments/missionthunderbolt/issues/20) macOS
- [#22](https://github.com/pizzaexperiments/missionthunderbolt/issues/22) regression tests, fuzzing and sanitizers
- [#23](https://github.com/pizzaexperiments/missionthunderbolt/issues/23) release signing, SBOM and checksums
- [#24](https://github.com/pizzaexperiments/missionthunderbolt/issues/24) optional public HTTP API decision

## Delivery directory conventions

```text
android/                          # Gradle project, Java host and JNI/C++ core
tests/                            # Core and ABI checks
docs/                             # Research and architecture notes
scripts/                          # Original-import validation and future converters
local-original/                   # IGNORED: locally supplied .sit/.zip and resource forks
local-generated/                  # IGNORED: extracted PICT/PNG/snd/analysis output
dist/                             # IGNORED: local APK and desktop packages
.github/workflows/                # Public-source CI and APK artifact upload
```

Local original source archive convention: `local-original/mission_thunderbolt.sit`. A future **authorized redistribution** can use GitHub Releases or separately permissioned storage, but do not put commercial game assets in a public release before rights are verified.

## Codex workflow
Start with #1, then #2 and #25. For each issue: inspect relevant code, propose smallest testable PR, run tests, document evidence and unblock dependencies. Never claim the full port is finished because a demo builds.
