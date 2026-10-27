# Local validation and resource research

This repository contains a **synthetic demo**, not recovered original gameplay.

With Python 3, C++17 compiler and POSIX shell run:
```sh
sh scripts/test_local.sh
./dist/mt_desktop_demo
```
The script runs the current synthetic Python suite, private-input index guard,
core/API/save/mutation C++ tests and a terminal-host smoke check. Root CMake/CTest
also exercises a real C client; see [quality gates](QUALITY.md) for sanitizer and
coverage commands.

To audit game resources you legitimately possess, put extracted `.rsrc` forks locally under `local-generated/resource_forks/` (ignored by Git), then:
```sh
python3 scripts/audit_resources.py local-generated/resource_forks --output local-generated/resource_manifest.csv
```
The report contains type/ID/size/PICT dimensions/SHA256 metadata only. It **does not decode PICT pixels** and does not disassemble CODE.

**APK status:** local debug and unsigned release APK/AAB builds passed; the
synthetic debug app installed/launched and passed API 23 emulator checks. See
[Android development](ANDROID_DEVELOPMENT.md) and [runtime evidence](ANDROID_RUNTIME.md)
for exact versions, counts and limitations. CI remains manual-only to conserve credits.

Never publish original game archives, code segments, art, audio, or derivatives without confirming redistribution permission.

## Manual/RNG increment — 2026-10-26

`sh scripts/test_local.sh` passed 41 Python tests and native core/API/save/mutation,
manual-WAIT and research-RNG regressions. With the activated SDK CMake toolchain,
`cmake --build dist/sanitizers --parallel 4` plus CTest passed **7/7** ASan/UBSan
tests; the SDL build/CTest passed **8/8**, including queued WAIT input. An initial
shell lacked CMake on PATH; activating the documented toolchain resolved that
setup failure before these results.

The WAIT debug/test APK build passed. Android instrumentation passed **8 tests**
on API 23 x86_64, font scale 1.0, portrait, target SDK 35. The subsequent lifecycle
smoke preserved turns across process death and three background cycles with a
clean app crash buffer. Earlier 1.3× font/landscape results cover the prior seven-
test suite; they are not results for the new eighth test. Physical ARM64, API 35
runtime and native Windows/macOS remain unverified. See [manual rules](MANUAL_RULES.md)
and [isolated RNG evidence](RNG_RESEARCH.md) for scope and unresolved fidelity.

The current WAIT-enabled debug APK is `dist/mission-thunderbolt-research-debug.apk`,
SHA256 `0a43671dbd1b0a3a3e1bdb7ecc3490c87e40eb0feccfe5be058e32d30d9df48f`.
It is a debug-signed synthetic research demo, not a release build.

## RNG initialization, timed sound and map accessibility increment

The private initializer oracle passed **37 initializers, 2,368 continued draws
and 12 low-memory accessor cases**; **2,405 complete C++/68000 state comparisons**
matched. The normal test script and sanitizer/SDL suites passed (45 Python,
7 ASan/UBSan, 8 SDL). Python statement coverage is **86%**, above the 80% gate.
The sound catalog returned expected exit 2: 137 single-buffer conversions and
one explicitly sample-only preview with retained timed commands; no malformed
resources. Complete timed playback is still unimplemented.

Android debug/test APK builds, debug lint and unsigned release APK/AAB builds
passed. The current **12 Android instrumentation tests** and subsequent lifecycle
process-death/three-background-cycle smoke passed on API 23 x86_64, normal font,
portrait, target SDK 35. The framework accessibility-tree readiness failure and
its tested harness correction are recorded in ANDROID_RUNTIME.md. This is not
physical TalkBack usability, API 35 runtime or original-game verification.

Updated accessibility-enabled debug demo: `dist/mission-thunderbolt-research-debug.apk`,
SHA256 `c591ca1bf008af08d086ab48f7d96073457baa4d1f2e9ff049970789035123fe`.
The earlier WAIT-only APK hash above describes the earlier checkpoint.

The optional Atheris 3.1.0 synthetic parser campaign completed 1,722,666 executions
in 121 seconds, with no failure artifacts and 71 MB peak RSS. Reproduction and
limits are recorded in QUALITY.md; this is not original-game differential coverage.

## Grid-helper and selector increment — 2026-10-27

The original-instruction/native comparisons passed 120 pointer-builder cases
(152,760 cell addresses), all 65,536 coordinate byte pairs, 2,048 candidate-gate
probes and 105 selector/RNG cases. Selector outcomes were 29 direct, 36 neighbor
and 40 stopped before the unresolved fallback. Source fingerprints, synthetic
allocator/direction inputs, exact commands and limits are recorded in
[GRID_RESEARCH.md](GRID_RESEARCH.md). A real Ghidra synthetic fixture also verified
the new exact-A5 filter: two direct references accepted, alias/indexed references
excluded. Original output remains private.

`sh scripts/test_local.sh` passed 45 Python tests and the native regressions.
CMake/CTest passed **9/9 ASan/UBSan** and **10/10 SDL** checks. The parser Python
source is unchanged; its last measured statement coverage remains 86%. These new
research headers are exercised by standalone tests and are not connected to the
active demo engine. Android/desktop host application logic was not changed, and
no new Android/device verification is claimed for this increment. The existing
APK, signing and physical-device limitations above remain applicable.

## GitHub connection and closeout — 2026-10-27

The authenticated API returned HTTP 200 for this repository, and creating draft
PR #26 plus issue evidence comments/closures succeeded. Issues #4, #24 and #25
were confirmed closed as completed after refreshing their live bodies/comments.
The environment's older policy snapshot did not reflect the working API route.
Existing credentials were reused. No code or test behavior changed for closeout;
previous local verification remains the evidence. No Actions run or merge occurred.

## Post-merge fallback and native demo audio — 2026-10-27

The live API confirmed PR #26 merged into develop as
`a851a724e7d371d4e8307982b70202549502d50b`. The active feature branch was
fast-forwarded to that head while preserving the in-progress changes.

Fallback verification passed **1,068** isolated cases and **105** composed
selector/fallback cases, comparing grid bytes, RNG state and synthetic callback
order. Original linked-record callbacks and historical direction values remain
unverified. `sh scripts/test_local.sh` passed 45 Python tests plus native
regressions; CMake/CTest passed **10/10 ASan/UBSan** and **11/11 SDL** checks.

The opt-in authored PCM path passed **15 Android instrumentation tests**, with
**528 consumed frames** reported at 22,050 Hz, on API 23 x86_64/normal portrait/
target SDK 35. The static-track initialization-order defect found in the first
attempt was corrected before the successful complete run. Process-death restore
and three background cycles passed with a clean app crash buffer. Debug/test
builds, debug lint, unsigned release APK/AAB builds and release lint passed.
The `-no-audio` emulator verifies platform frame consumption, not audible output
or original audio fidelity. Physical/API35/OS focus competition remain unrun.

Current audio-enabled debug demo: `dist/mission-thunderbolt-research-debug.apk`,
SHA256 `627c494b01c98bb2c017e113b6739d4af17cb62209feb1973209250fb20a0c18`. Earlier hashes
above identify their prior checkpoints. Sound defaults off; no original audio
is packaged. This is a debug-signed synthetic demo, not a production release.

## Release dependency evidence and #2 closeout — 2026-10-27

PR #27 was verified merged into develop as
`f693dfd511ea5e7d18653a92f4dc9ab426626c3d`; the existing feature branch was
fast-forwarded to it. Issue #2 was closed against its four stated criteria,
with evidence linked in ISSUE_CLOSEOUT_REVIEW.md. No Actions run was requested.

`sh scripts/test_local.sh` passed **49 Python tests** and all native regressions.
The first attempt exposed a new test import-path error; adding its own script
path initialization fixed it. Final coverage.py 7.10.7 run/combine/report passed
at **84%** across all Python tools (80% required). Root CMake/CTest passed
**10/10 ASan/UBSan** checks. No parser fuzz campaign was repeated.

With the documented JDK17/Gradle8.7/NDK27.2.12479018 toolchain,
`gradle --no-daemon --console=plain assembleRelease bundleRelease
exportReleaseRuntimeDependencies` passed. After extending the runtime report to
include local-file artifacts, its export was rerun successfully. The dependency
collector passed on the unsigned release APK and AAB with four ABIs, matching
ELF build IDs and dynamic dependencies; it recorded 16 ABI/archive entries.
There are no Java runtime modules/artifacts. System requirements are libc.so,
libdl.so and libm.so. Regression tests reject stale build IDs, changed artifact
hashes, newly added file dependencies and foreign static archives.

App Java/gameplay code was unchanged; the CMake change emits a linker map. No new
device/runtime test, audible output test, Windows/macOS run, signed release or
publication is claimed. The previous debug APK remains the downloadable demo.
NDK composite notices are preserved by the manual workflow; per-component
license attribution and the rest of issue #23 remain open.

## Independent graphics decoder increment — 2026-10-27

`python3 scripts/verify_pict_independently.py --manifest
local-generated/original-resources/manifest.json --output
local-generated/independent-pict-resources.json` returned the expected **exit 2**:
907 exact matches, one pixel mismatch, no dimension mismatch or failed decoder.
The standalone command over all 26 INTRO/END files returned exit 0 with 26 exact
matches. ImageMagick 7.1.1-43 Q16 was the independent implementation. The preserved
30×65 monochrome mismatch and an authored reproduction are detailed in
PICT_CATALOG.md; no decoder logic or comparison tolerance was changed to hide it.

`sh scripts/test_local.sh` passed **53 Python tests**, with the optional real
ImageMagick synthetic test executed, plus native regressions. The complete
coverage.py run/combine/report passed at **82%**, above the 80% gate. Native
production code is unchanged from the already-passing 10-test sanitizer run.
No Android or desktop runtime, original-game screenshot, audible output, CI run
or public release is newly claimed. Private pictures/comparison outputs stay
ignored; only authored fixtures, tool code and summary counts enter Git.

## GraphicsMagick follow-up — 2026-10-27

PR #28 was verified merged as `b1388131976492c6ce978fc48d920bb2afaea9e4`; the
feature branch was fast-forwarded. GraphicsMagick's independent resource run
returned expected exit 2: **808 exact, 100 failed, zero pixel/dimension mismatches**.
Its standalone run returned exit 0: **26 exact**. Joining source fork/ID/SHA
records with the retained ImageMagick report established **934/934 pictures
matching at least one external decoder**. GraphicsMagick matches the previously
disputed 30×65 picture. An authored indexed one-bit PixMap reproduces the
ImageMagick padding discrepancy while matching GraphicsMagick and known pixels.
No native PICT output or pixel tolerance changed. Full commands, tool identity,
limits and visually attributed panels are in PICT_CATALOG.md.

With optional GraphicsMagick supplied via `GRAPHICSMAGICK_EXECUTABLE` and its
normal library search path, `sh scripts/test_local.sh` passed **56 Python tests**
and all native regressions. Both optional external-decoder tests executed.
coverage.py run/combine/report passed at **82%** (80% gate). Root CMake/CTest
passed **10/10 ASan/UBSan** checks. No new Android/desktop runtime or original
gameplay validation is claimed. Third-party comparison tools, original inputs
and detailed comparison outputs remain outside public source/packages.

## Linked-record helpers — 2026-10-27

The live API verified PR #29 merged into develop as
`42535e509f7e1f08ccceff29de3b6180ed6971a3`; the active feature branch was
fast-forwarded. Isolated linked-record research then passed **131,072 original
query probes** and **715 original/native unlink comparisons** (449 removals,
266 research-budget stops). Final verification includes callee-register, stack,
read-only query and unrelated-byte/guard checks. The first oracle attempt failed
because setting supervisor mode after A7 swapped out the initialized stack;
initializing SR before A7 fixed the test setup. No original instructions or
assertions were changed. Commands, fingerprints, raw fields and limits are in
GRID_RESEARCH.md. Reports and static disassembly stay private.

`sh scripts/test_local.sh` passed **56 Python tests** and native regressions with
both optional external picture decoders present. Root CMake/CTest passed
**11/11 ASan/UBSan** and **12/12 SDL** tests, including the new linked-record
regression and authored fallback interface composition. Python tools under the
coverage gate are unchanged; their last measured statement coverage remains 82%.
The source-only research model is not linked into active Android/SDL gameplay;
no new Android build, runtime test or fidelity claim is made. Full original
selector/lifecycle composition and game rules remain incomplete.

## Record release control flow — 2026-10-27

The live API confirmed PR #30 merged as
`0b927d8f141d4a3c96831bdeaa2968643fc06980`; the existing feature branch was
fast-forwarded. The original release walkers matched the native model on
**1,730 authored cases** (334 complete, 1,396 budget stops). Final modeled fields
are compared exactly; callback order and intermediate state fingerprints are
checked alongside unrelated original bytes/guards and normal return state.
A separate CODE 11 wrapper sweep matched **131,072 prefix probes**, observing
one DisposePtr call with the prefix address. The Macintosh trap was skipped.
Source profiles, commands, preconditions and scope are in GRID_RESEARCH.md.

`sh scripts/test_local.sh` passed **56 Python tests** and native regressions, with
both optional picture decoders present. Root CMake/CTest passed **12/12 ASan/UBSan**
and **13/13 SDL** checks. The first new unit run had an incorrect expected research
step count of six; the independent original oracle reports five for that authored
shape. The expectation was corrected to five, retaining the assertion and model.
Native interface composition covers filter, unlink and both release helpers,
including partial mutations through fallback rejection. Original whole-selector/
lifecycle composition remains unrun.

Production Python scripts are unchanged (last measured coverage 82%). No new
Android APK/runtime, original game boot, allocator reclamation or public release
is claimed. Original disassembly and comparison reports remain ignored.

The release-model source was committed locally as `9b20560`. The subsequent Git
push failed authentication, and a read-only authenticated API recheck returned
HTTP **401 Bad credentials**. Current environment status exposes no ready GitHub
credential binding, and no GitHub connector tools are available. The existing
credential was not printed or replaced. PR payload/description and a source-only
patch were prepared locally; no follow-up PR, issue update or remote branch push
is claimed for this increment. Publishing awaits a refreshed credential connection.
