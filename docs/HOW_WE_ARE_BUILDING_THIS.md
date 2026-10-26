# How We're Building Mission Thunderbolt — An LLM Capability Experiment

> **Purpose:** Restore a classic Macintosh game as a native, cross-platform application while documenting what a large language model (LLM) can actually accomplish when given original software artifacts, developer tools, tests, and access to a source repository.

## The project in one paragraph

We are attempting to turn the original *Mission: Thunderbolt* Macintosh application into a native game for **Android first**, followed by **Windows and modern macOS**. The long-term goal is **faithful Classic gameplay** with **optional Modern presentation and controls**, running **without a Macintosh emulator in the shipped app**. Because we do not have verified original high-level source code, this is a preservation and reverse-engineering effort—not a straightforward recompile. We begin by inventorying Macintosh resources, recovering observable behavior, and gradually rebuilding a portable game engine that can be validated against the original.

## Why this is an LLM experiment

This repository is also an experiment in **end-to-end AI-assisted software engineering**. We want to see how far an LLM can get on a real, underspecified, multi-stage project involving:

1. **Artifact archaeology:** understanding legacy StuffIt archives, AppleDouble metadata, resource forks, Motorola 68K code, PICT graphics, and Macintosh audio.
2. **Reasoning under uncertainty:** separating confirmed observations from plausible hypotheses and avoiding invented game mechanics.
3. **Engineering execution:** writing buildable C++ code, Android integration, tests, conversion scripts, documentation, and automation.
4. **Tool use and collaboration:** inspecting files, using local compilers/test tools, creating GitHub commits/issues, and producing reproducible handoffs for Codex and human contributors.
5. **Persistence across stages:** maintaining a consistent plan, architecture, and evidence trail as work is resumed in new sessions.
6. **Self-correction:** diagnosing failed builds, revising assumptions, rerunning tests, and recording failures rather than declaring success prematurely.

The question is **not** merely whether an LLM can generate source code. It is whether it can help move a complicated legacy-software recovery project toward a verifiably working result.

## How the work is divided

| Stage | What happens | Evidence of completion |
| --- | --- | --- |
| 0. Provenance | Document origin, rights, archive versions, and distribution limits. | A traceable provenance record and a safe local-input workflow. |
| 1. Extraction | Recover and index Macintosh executable/resource forks; record types, IDs, sizes, hashes. | Reproducible scripts and manifests against supplied archives. |
| 2. Asset recovery | Decode PICT artwork and `snd ` resources into modern formats. | Validated conversions and comparisons to original rendering/audio. |
| 3. Behavioral research | Observe the original in a compatible reference environment; analyze 68K CODE/CREL and Macintosh APIs. | Annotated disassembly, capture logs, and evidence-linked behavior specifications. |
| 4. Engine reconstruction | Implement maps, turns, movement, combat, AI, items, saves, and mission progression in portable C++. | Deterministic tests and comparisons to original behavior; no speculative fidelity claims. |
| 5. Native frontends | Connect the engine to Android, Windows, and macOS with Classic and Modern presentation modes. | Installable builds and device/OS acceptance tests. |
| 6. Release | Package, document, verify, and distribute only material that we have permission to distribute. | Reproducible release artifacts, checksums, and rights review. |

The work is tracked in [GitHub Issues](https://github.com/pizzaexperiments/missionthunderbolt/issues) and sequenced in [ROADMAP.md](ROADMAP.md).

## Architecture

```text
Locally owned historical archives (not committed publicly)
                 |
                 v
  Import / validation / extraction tools
                 |
       +---------+----------+
       |                    |
   Resource catalog    68K analysis and
   PICT / sound data   behavioral observations
       |                    |
       +---------+----------+
                 |
       Evidence-backed specifications
                 |
          Portable C++ core
       (deterministic game state)
                 |
        Versioned in-process C API
                 |
       +---------+-----------+
       |         |           |
     Android   Windows     macOS
       |         |           |
    Classic or Modern presentation
```

An **emulator may be used to inspect the original** and collect reference observations. An emulator is **not** intended to be part of the finished native game. The C API is a library integration interface; the project does **not** currently require an online service or HTTP API.

## Current verified state and limitations

As of **October 26, 2026**, the repository contains a **synthetic C++ demonstration engine**, Android/JNI project source, a versioned C API, smoke tests, and a research roadmap. The synthetic map and movement code are **not** recovered *Mission: Thunderbolt* game rules.

Historical files supplied in the conversation have been inspected outside this public repository; reported recovery includes classic Macintosh CODE/CREL, PICT, and sound resources. Resource presence is **not** equivalent to completed disassembly, successfully decoded artwork, or a playable original game.

Portable C++ and API checks have passed in earlier validation. An Android GitHub Actions run failed during Android SDK setup before APK compilation; a subsequent workflow change was made. **No APK should be described as successfully built, installable, or device-tested until a build artifact and a test result demonstrate that.** The environment used for portions of this research may lack Android SDK/NDK and cannot validate an APK locally.

The project does **not** currently claim:
- a complete decompilation or reconstruction of the original engine;
- a faithful gameplay port;
- a usable set of all converted art and audio;
- an Android APK verified on a phone;
- native Windows/macOS release packages.

Status claims must be updated only with links to concrete evidence.

## How we measure the LLM's performance

For each milestone, record:

- **Task definition:** what was requested, assumptions, and what was unknown.
- **Inputs and provenance:** which version or file was examined; hashes where appropriate, without exposing restricted assets.
- **LLM contribution:** code, tests, disassembly notes, plans, debugging, documentation, or GitHub operations.
- **Independent verification:** commands run, exit codes, automated tests, build logs, screenshots, emulator observations, and human checks.
- **Errors and recovery:** incorrect hypotheses, tool/environment limitations, failed builds, and what fixed them.
- **Human intervention:** decisions, credentials, historical references, rights confirmation, or hardware supplied by people.
- **Outcome:** `not started`, `in progress`, `tested prototype`, `validated against original`, or `shipped`.

We should distinguish **LLM-generated output** from **LLM-verified behavior**. A plausible-looking implementation, successful compilation, and a faithful port are three different achievements. Keep the measurements and negative results, not just success stories.

## Collaboration model

- **ChatGPT / LLM sessions:** analyze supplied files, propose and implement bounded changes, run available local tests, and maintain the written evidence trail.
- **Codex:** take focused, issue-sized tasks from the repository; make pull requests with reproducible checks and clear uncertainty reports.
- **Human maintainers:** supply legitimately obtained reference material, decide on design/rights matters, test on hardware, review fidelity, and accept releases.
- **GitHub:** source-of-truth for code, issues, discussions, PRs, and documented decisions—not the default place to publish copyrighted input files.

Work proceeds in **bounded sessions**, not as an unattended agent that continues indefinitely after a conversation ends. Each session should leave a concrete checkpoint (commit, test report, annotated finding, or updated issue) so another session can continue safely.

## Local testing and GitHub Actions credits

The primary verification path is **local**: portable C++ builds/tests, fixture-based parser tests, command-line demonstration host, and resource audits. Android requires a configured SDK/NDK/Gradle toolchain. If GitHub Actions credits are unavailable, workflow runs should not be used as the main feedback loop; document exact local build commands and collect artifacts from a verified local build instead. A source file named `.apk` is not proof of a working APK.

When an APK is produced, record:
1. build tool versions and build command;
2. APK path, size, SHA-256, package ID, and architecture;
3. install/launch result on an Android device or emulator;
4. known differences from the historical game;
5. whether original commercial assets are included and under what permission.

## Rights and preservation

The public repository should contain **newly written code, tests, documentation, and redistributable synthetic fixtures** unless permission for historical content is confirmed. Keep the original `.sit`, Macintosh binaries/resource forks, copyrighted graphics/audio/manuals, and their restricted derivatives in ignored local directories or a separately permissioned store. A user-provided archive may be analyzed locally, but that does not automatically authorize public redistribution or bundling it into a public APK.

Suggested local structure:

```text
android/           Android Studio app and JNI bridge
desktop/           Native desktop host prototypes
tests/             Unit and regression checks
scripts/           Import, audit, conversion and local test tools
docs/              Architecture, research, roadmap and experiment evidence
local-original/    Private local historical archives (gitignored)
local-generated/   Private extracted or converted original assets (gitignored)
dist/              Local build artifacts (gitignored)
```

## What counts as success?

**Near-term:** a reproducibly built, installed, and tested **native Android demonstration APK**, without using the original game rules as an unsupported claim.

**Mid-term:** decoded and catalogued historical resources, documented original behavior, and a deterministic reconstructed engine with meaningful test coverage.

**Long-term:** a faithful, native, legally distributable *Mission: Thunderbolt* experience on Android, Windows, and macOS, with both Classic and Modern interfaces.

The most valuable result of this experiment is not only a finished game: it is an auditable record of **where the LLM accelerated real engineering, where it made mistakes, what required human judgment, and what was independently verified**.

---

**Related:** [Project roadmap](ROADMAP.md) · [C API](API.md) · [GitHub issues](https://github.com/pizzaexperiments/missionthunderbolt/issues) · [Root contributor instructions](../AGENTS.md)
