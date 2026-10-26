# Mission Thunderbolt — Native Restoration

Research project for a **native** Android port of classic Macintosh *Mission: Thunderbolt*, with portable C++ core and optional Classic / Modern presentation modes.

## Current state

This repository begins with a **demonstration engine**, not a recreation of original gameplay. Original Macintosh 68K CODE/CREL resources have been recovered separately; no game mechanics are claimed to be disassembled yet. No APK has been built or verified.

## Goals

- Android app built with Android SDK/NDK, no Macintosh emulator at runtime.
- Portable C++ gameplay core suitable for future Windows/macOS hosts.
- Classic presentation and optional modern accessibility and touch features.
- Reverse-engineering research and regression tests separating verified facts from hypotheses.

## Build

Open `android/` in Android Studio, install SDK platform 35 and NDK/CMake, and build `assembleDebug`. GitHub Actions is configured for automated build validation. The project has not yet been device-tested.

## Rights

Original game binaries, art, sound, manuals and resource forks are **not included** pending rights review. Do not upload these to a public repo without authorization.

See `docs/ROADMAP.md` for progress and limitations.
