# Android runtime evidence — issues #17 and #18

Validation date: 2026-10-26. Native synthetic demo only; no original game assets
or original gameplay are packaged. Host: Linux x86_64, emulator 37.2.12, software
CPU/SwiftShader rendering. APK minimum API 23, target/compile API **35**.

## Passed

- Debug APK and instrumentation APK build; unsigned release APK/AAB build and
  release lint pass. An initial release failure exposed target API 28; raising
  the target to 35 and adding system-inset handling fixed it without suppressing lint.
- Install and launch on **API 23 x86_64**. The installed app's own configuration
  reports target SDK 35; the claim is not inferred from the source build file.
- **Seven instrumentation tests**, run at normal portrait, actual **1.3×** portrait
  font scale, and actual **1.3× landscape**. All seven pass in each configuration.
  The tests report measured fontScale/orientation/target SDK, verify scalable
  status text, target labels/sizes, mode/turn preservation, explicit restart,
  Activity recreation, keyboard focus/touch-mode transitions and joystick hold behavior.
- The touch-to-keyboard check exposed a first-direction focus loss. Keeping the
  board focusable in touch mode and dispatching directional events at Activity
  level fixes it; injected-key regressions cover it.
- The lifecycle smoke checks restart, two physical-style injected moves, pause,
  forced process stop/relaunch with state restore and three background/foreground
  cycles. No app crash appeared in the tested crash buffer.
- The board redraws on invalidation; no continuous simulation timer or wake lock
  was added. This is an implementation fact, not a battery/performance measurement.

The initial test harness wrote font_scale=1.5 but the app still measured 1.0.
That attempt is **not** counted as a font-scaling test. Changing font size through
Settings to Huge produced a measured 1.3, and both portrait/landscape runs then
passed. Normal font size and original rotation settings were restored afterward.
Synthetic screenshots and machine-readable reports remain under ignored
`dist/verification/`; do not confuse them with original reference captures.

## Reproduce

Build/install both APKs using ANDROID_DEVELOPMENT.md and run:

```sh
adb -s SERIAL shell am instrument -w org.missionthunderbolt.prototype.test/android.test.InstrumentationTestRunner
python3 tests/android_lifecycle_smoke.py --serial SERIAL --output dist/verification
```

The helper targets only the synthetic package. For this cloud machine's read-only
ADB home, an optional direct **local emulator** backend was used instead:

```sh
python3 -m pip install adb-shell==0.4.4
python3 tests/android_lifecycle_smoke.py --direct-emulator 5557 --output dist/verification
```

Select the adbd port for your own emulator. Standard emulator serial 5556 uses
adbd port 5557. The helper does not configure/start an emulator or build/install
APKs. It needs a fully booted image and records actual API/ABI/target SDK.

## Failed environment checks and unrun acceptance

The software-emulated **API 35 system image** repeatedly lost framework/package
services before successful app installation. Logs include network-stack/system
process failures. A boot_completed flag alone did not establish service health.
Trying one virtual CPU and disabling the emulator's Vulkan feature did not produce
a stable test system. API 35 application behavior is therefore **unverified**;
this is a test-environment failure, not evidence of an app defect. A stable
accelerated emulator or physical device is needed for that check.

ARM64 is compiled into the APK, but no physical ARM64 device was available.
Physical gamepad/TalkBack coverage, sustained performance, low-memory behavior,
battery/audio-focus measurements and production signing remain unrun. The current
app was silent at that checkpoint. The subsequent authored PCM path is recorded
below. Original-vs-port behavior is an entirely separate research task.

## Virtual-map accessibility increment

The next suite adds read-only virtual player/wall/floor cells with coordinates,
accessibility focus/search and explicit movement/WAIT/zoom actions. Instrumentation
checks provider behavior and also retrieves the virtual player through Android's
actual framework accessibility tree. Zoom hides offscreen cells from visible
children, clears offscreen accessibility focus, and provides a full-map reset.
These checks do not constitute a physical TalkBack speech/gesture usability test.

The expanded **12-test suite passed on API 23 x86_64**, measured font scale 1.0,
portrait, target SDK 35. An initial framework-tree attempt queried immediately
after connecting UiAutomation and received no active window. Connecting before
Activity launch and waiting for the accessibility window resolved the harness
readiness failure; the focused check and subsequent complete suite passed.
The provider checks had already passed as an 11-test intermediate suite.

The final build passed `assembleDebug`, `assembleDebugAndroidTest`, `lintDebug`,
`assembleRelease` and `bundleRelease`. A subsequent lifecycle run preserved turns
across process death and three background cycles, with a clean app crash buffer.
These new 12-test results cover normal portrait only; earlier 1.3×/landscape
results remain seven-test historical checkpoints. Release outputs are unsigned;
physical TalkBack/gamepad, ARM64, API 35 runtime and performance remain unverified.

## Opt-in authored PCM audio increment — 2026-10-27

The complete **15-test suite passed** on API 23 x86_64, normal font/portrait,
target SDK 35. The new output test measured **528 consumed PCM frames** at
22,050 Hz from the authored cue. It checks initialized static output, complete
PCM writes, frame progress, mute/zero volume, explicit focus callbacks, pause/
release, missing-service fallback, settings recreation and keyboard volume control
without a simulation turn. The first attempt exposed a static-track load-state
ordering bug; writing PCM before requiring STATE_INITIALIZED fixed it, and the
full suite passed with the playback assertion intact.

A subsequent process-death/three-background-cycle run passed with a clean app
crash buffer. Debug/test APK, debug lint, unsigned release APK/AAB and release
lint passed. The emulator used `-no-audio`: frame consumption is verified Android
output-stack behavior, not audible host/physical-device proof. Focus callbacks
were injected; real competing-client arbitration and hardware routing remain
unverified. No historical sample or cue mapping is packaged. See
[NATIVE_AUDIO.md](NATIVE_AUDIO.md) for behavior and limits.

## Configurable control placement increment — 2026-10-27

The complete **17-test suite passed on API 23 x86_64** at measured font scale
1.0/portrait and 1.3/landscape, target SDK 35. Tests measure directional row
positions and landscape child order for Auto/Left/Right, check the 48 dp placement
button and accessible description, preserve game state and hidden controls, and
verify the setting on a distinct live recreated Activity. The recreation helper
now rejects stale/destroyed Activity instances for all three recreation tests.

Initial runs exposed an API-24-only test getter and a stale Activity reference in
the harness. Actual measured geometry replaced the getter; the live-instance
check resolved the latter. Assertions remain enabled. Writing the font setting
alone left the app at 1.0; that landscape run passed 17 tests but is not counted
as 1.3 evidence. Selecting Huge through Settings produced the reported 1.3 and
the full suite passed again. The audio output check still consumed 528 authored
PCM frames; the emulator has no host audio.

Debug/test builds and debug lint passed. Unsigned release APK/AAB and release
lint passed. The debug APK signature verified (apksigner also warned that the
META-INF Gradle metadata entry is not signature-protected). Debug APK SHA-256:
`5cdd119778ec35022909c3f6552286e16c838d7d375019c347f7ddcefb7675c5`.
This identifies a local debug artifact, not a production-signed release.

To independently check placement persistence alongside process death and three
background cycles, install the debug APK, then run:

```sh
python3 tests/android_lifecycle_smoke.py --serial SERIAL --check-control-placement --output dist/verification/control-placement-lifecycle
```

The independent run passed on API 23 x86_64: Left placement and Modern/turn 2
state survived forced process death and three background cycles; the app crash
buffer was clean. The final synthetic screenshot shows portrait Left placement.

The helper deliberately resets the synthetic demo and selects Left. Physical
ARM64/TalkBack/gamepad, API 35 runtime, low-memory, performance and power checks
remain unrun. This increment does not establish original gameplay fidelity.

## Audio memory-pressure handling — issue #18

The Activity now forwards `onTrimMemory` at RUNNING_LOW or higher and legacy
`onLowMemory` to the audio component. It cancels the pending completion, abandons
focus and releases the cached static track. RUNNING_MODERATE retains the cache.
Enabled/volume settings and active/paused/closed state are retained: trimming
does not automatically replay sound or activate paused output. A subsequent
foreground cue lazily recreates output. No gameplay save schema or mechanics
change is involved.

Two instrumentation tests cover repeated release, paused/closed output, lazy
recreation and Activity forwarding at six trim levels plus repeated low-memory
callbacks. They compare the entire native serialized state (map, player, turns,
RNG and presentation, including its checksum), not only the status text.
Reflection in the test accesses existing private state; no public test API is
added to the app. Callback injection does not simulate actual resource exhaustion
or a low-memory-killer decision.

The lifecycle helper can additionally ask Android to send COMPLETE trim while
the synthetic app is backgrounded, before process death and during three
background cycles:

```sh
python3 tests/android_lifecycle_smoke.py --serial SERIAL --check-control-placement --send-memory-trim --output dist/verification/memory-pressure-lifecycle
```

The helper checks that the shell command is accepted; it does not independently
observe callback delivery or the system's real memory-pressure policy. Existing
Activity callback tests cover the handler. Physical ARM64, API 35 runtime, actual
OOM/low-memory kills, performance and battery measurements remain unverified.

Validation on 2026-10-27: all **19 instrumentation tests passed on API 23
x86_64**, measured font scale **1.3**, portrait, target SDK 35; AudioTrack consumed
528 authored PCM frames. The local runner requested 1.0 but the running framework
retained 1.3, so its final configuration assertion failed after the complete
suite passed. This is recorded as a 1.3 run only; normal-font/landscape results
for this 19-test suite are unrun. Prior 17-test configurations remain historical
checkpoints. The raw failure log and a measured-configuration report remain
under ignored local paths.

Debug/test APKs and debug lint, unsigned release APK/AAB and release lint passed
using `gradle --no-daemon assembleDebug assembleDebugAndroidTest lintDebug
assembleRelease bundleRelease lintRelease` from `android/`. Debug signature
verification passed, with the same Gradle META-INF metadata warning noted above.
Debug APK SHA-256:
`a5eb61453e883bfd76a5dff016973c8d3b58781019ea49b103bf9e1a0139f3ef`.

The initial edit used the wrong working directory and changed no files. The
first emulator launch also lacked the existing AVD locator; selecting
`ANDROID_AVD_HOME=/workspace/.cloud-setup/android-user/avd` resolved that setup
failure. The subsequent build includes the new callbacks and both tests. No
Actions or release was triggered.

The independent lifecycle run also passed on API 23 x86_64/target SDK 35:
Classic/turn 2 and Left placement survived process death and three background
cycles, with COMPLETE trim requests accepted at each background interval and a
clean app crash buffer. The final synthetic screenshot shows portrait Left
placement. Reports/screenshots remain ignored in
`dist/verification/memory-pressure-lifecycle/`.

## Reproducible performance measurements

[Android performance evidence](ANDROID_PERFORMANCE.md) now records five
process-cold launches, frame timing and PSS for the existing debug APK on API 23
x86_64 software emulation. It replaces the earlier blanket unmeasured-performance
status for that configuration only. Physical ARM64, current-target-API runtime,
battery/thermal behavior and production performance remain unverified.

## API 35 runtime qualification

[API 35 qualification evidence](ANDROID_API35.md) records the selected image,
existing APK identities, readiness checks and exact launch/test outcomes. It
keeps framework startup failures separate from app results; the SDK target or
completed package installation alone is not runtime verification. Physical ARM64
acceptance remains separate.
