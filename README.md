# Mission Thunderbolt — Native Restoration

Research project for a **native** Android port of classic Macintosh *Mission: Thunderbolt*, with portable C++ core and optional Classic / Modern presentation modes.

**[How we're building this — an LLM capability experiment](docs/HOW_WE_ARE_BUILDING_THIS.md)** explains the restoration strategy, test methodology, human/AI responsibilities, and verified limitations.

## Current state

This repository begins with a **demonstration engine**, not a recreation of original gameplay. Original Macintosh 68K CODE/CREL resources have been recovered separately; no game mechanics are claimed to be disassembled yet. No APK has been built or verified.

## Goals

- Android app built with Android SDK/NDK, no Macintosh emulator at runtime.
- Portable C++ gameplay core suitable for future Windows/macOS hosts.
- Classic presentation and optional modern accessibility and touch features.
- Reverse-engineering research and regression tests separating verified facts from hypotheses.

## Build

See [Android development](docs/ANDROID_DEVELOPMENT.md) for pinned tools, build/install/launch commands and troubleshooting. Local APK builds have passed; [evidence and remaining checks](docs/verification/android-build.md) distinguish build, installation and gameplay validation. GitHub Actions is manual-only to conserve credits.

## Rights

Original game binaries, art, sound, manuals and resource forks are **not included** pending rights review. Do not upload these to a public repo without authorization.

See `docs/ROADMAP.md` for progress and limitations.
