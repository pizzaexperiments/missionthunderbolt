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
