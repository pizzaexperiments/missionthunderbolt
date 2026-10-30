# Android synthetic-demo performance measurements — issue #18

This is an observational baseline for the installed synthetic debug application,
not a production performance qualification or original-game benchmark. The tool
does not build or install an APK, clear user data, drop OS caches, change system
settings or assign performance pass/fail thresholds. It force-stops this app and
sends Space/WAIT keys, so it changes synthetic turn state. Use a test device/save.

## Reproduce

Select a device explicitly and supply the existing APK whose installed bytes are
to be measured:

```sh
python3 scripts/android_performance.py --serial DEVICE_SERIAL \
  --apk android/app/build/outputs/apk/debug/app-debug.apk \
  --output dist/verification/android-performance
```

The tool pulls the installed APK and requires an exact SHA-256 match before
launching it. A missing package, mismatched APK, surviving process after
force-stop, incomplete launch timing or unexpected Activity is an error. It never
auto-selects a device. For a deliberately selected local emulator whose host adb
server cannot start, install `adb-shell==0.4.4` in a private Python environment and
replace `--serial DEVICE_SERIAL` with `--direct-emulator LOCAL_ADBD_PORT`. This
fallback connects only to `127.0.0.1`; it does not start an emulator.

Defaults are five process-cold starts and 24 WAIT key events, with a requested
0.1-second delay after each synchronous input command. Input transport time adds
to this delay; this is not a 10 Hz simulation benchmark. Counts and interval can
be set with `--launches`, `--actions` and `--interval`.

`android-performance.json` records device model, API, ABI, fingerprint, installed
SDK/version/debug flags, APK hash/size, display/font setting and host platform.
Raw launch, graphics and memory outputs remain alongside it under ignored
`dist/verification/`. Keep device-specific raw reports local; publish reviewed
summary measurements in a PR.

## What is measured

- `am start -W` reports ThisTime, TotalTime and WaitTime after `am force-stop`;
  absence of the app process is checked before each start. These are **process
  cold**, with OS/filesystem caches retained, not cache-cold, first-install or
  first-ever launches. Host command round-trip time is reported separately.
- `dumpsys gfxinfo ... reset` precedes the WAIT sequence. `framestats` durations
  use `FrameCompleted - IntendedVsync` for zero-flag, valid timestamp rows.
  Flagged/uninitialized rows are counted separately. Multiple window sections
  are included. Framework frame/jank summaries are also recorded when present.
  Missing valid rows are explicitly unmeasured, never treated as zero time.
- `dumpsys meminfo` total proportional set size (PSS), in KiB, is captured before
  and after actions. These snapshots do not establish peak usage or a leak rate.
- Summaries use median and nearest-rank p95. Five launches give an exploratory
  p95 equal to the maximum, not a statistically stable tail estimate. Frame data
  measures the Android view pipeline, not sustained FPS or original gameplay.

Space events use the same stable WAIT binding as the existing lifecycle/UI
implementation. The tool records command delivery, not an asserted gameplay turn
count or a mechanics correctness result. Existing instrumented tests address
that separate behavior. No battery, audio routing, thermal or real-memory-pressure
measurement is performed here.

## Local measurement, 2026-10-30

The selected private `mt-api23` AVD ran on a shared Linux x86_64 cloud host using
Android emulator **37.2.12.0**, `-accel off`, SwiftShader, no window and no host
audio. This is software CPU/GPU emulation, not physical ARM64 hardware. Other
research/test work shared the host; concurrent load was not controlled. These
conditions and emulator overhead confound comparisons with physical devices,
release builds or other machines.

The existing **2026-10-27** debug APK was used without rebuilding or installing a
new artifact. SHA-256:
`a5eb61453e883bfd76a5dff016973c8d3b58781019ea49b103bf9e1a0139f3ef`.
Installed bytes must match this hash for the recorded run. The host adb command
failed because its default `/home/agent/.android` directory is read-only; the
explicit local-adbd fallback was used instead.

The measurement command is:

```sh
/workspace/.cloud-setup/qa-python/bin/python scripts/android_performance.py \
  --direct-emulator 5557 \
  --apk android/app/build/outputs/apk/debug/app-debug.apk \
  --output dist/verification/android-performance-2026-10-30
```

The run began at **11:30:41 America/New_York (15:30:41 UTC)** on Android **6.0 / API 23**, x86_64
(`x86_64,x86` ABI list), model `Android SDK built for x86_64`, display 320×640.
The font-scale setting reported 1.0; this is a Settings value, not a measured
in-Activity font-scale assertion. Installed version was `0.1-research` / code 1,
**debuggable**, target SDK **35**. This API's package dump did not report minSdk;
the tool records that value as unavailable rather than inferring it. The APK was
4,156,433 bytes and the pulled installed APK had the same SHA-256.

| Metric | Observed result |
| --- | --- |
| Five process-cold `TotalTime` samples | 1820, 1222, 1411, 1279, 1740 ms |
| `TotalTime` / `ThisTime` median; min; p95/max | 1411; 1222; 1820 ms |
| `WaitTime` median; min; p95/max | 1479; 1265; 2011 ms |
| Host command round trip median | 3416.875 ms |
| Valid recorded frame rows | 26; zero flagged/invalid rows |
| Frame duration median; p95; max | 64.445; 160.080; 409.856 ms |
| Framework total / janky frames | 28 / 26 (92.86%) |
| PSS before / after 24 WAIT commands | 9797 / 10736 KiB |

Framework aggregate counters and available per-frame rows have different counts;
the report preserves both and does not equate 24 input commands with 24 frames.
The high jank percentage is an observed software-emulation baseline, not a
physical-device acceptance verdict. PSS growth between two snapshots is not
proof of a leak. Raw reports are under the ignored command output directory.
The owned emulator was stopped after collection; no device settings were changed.

These measurements complement [lifecycle evidence](ANDROID_RUNTIME.md). The
four written #18 checklist items should be assessed separately from its wider
objective: crash-free current-target-API and physical ARM64 execution remain
unverified. No Actions workflow, signed release or original gameplay claim is
implied.

Parser and authored collection validation:

```sh
python3 -m unittest discover -s tests -p test_android_performance.py -v
```

Nine authored tests cover launch identity/freshness, PSS formats, reordered frame
columns/multiple windows, flagged/invalid frame timestamps, unavailable/malformed
data, summary statistics and installed metadata. The collection checks preserve
raw evidence and reject mismatched artifacts or surviving processes before
recording a purported cold launch. Their fixtures are authored, not device data;
the actual emulator measurement above is separate evidence.
