# API 35 synthetic Android runtime qualification — issue #18

This check runs the existing synthetic debug app on Android API 35; compile and
target SDK settings alone do not establish runtime compatibility. It does not
test original Mission Thunderbolt behavior, production signing or physical ARM64
hardware. GitHub Actions remains disabled.

## Artifact and environment

The **existing 2026-10-27 artifacts** were selected without a new build:

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| `app-debug.apk` | 4,156,433 | `a5eb61453e883bfd76a5dff016973c8d3b58781019ea49b103bf9e1a0139f3ef` |
| `app-debug-androidTest.apk` | 35,126 | `292a3d1ce4e72047fa56ef1df5864fb255a0fb86c6f003b36f20200352f0308e` |

The app contains native libraries for arm64-v8a, armeabi-v7a, x86 and x86_64;
their presence does not demonstrate ARM64 execution. The active application code
retains `7f97c50`'s audio memory-pressure handling; later research headers are
outside the active application. The original APK pair predates the subsequent
test-only changes below. Artifact hashes identify actual tested bytes
independently of the current branch.

A new private AVD, `mt-api35-qualification`, uses the installed
`system-images;android-35;default;x86_64` image. Configuration: 320×640, density
160, 3072 MiB RAM and two virtual CPUs. Android emulator 37.2.12.0 runs with:

```sh
emulator -avd mt-api35-qualification -port 5558 \
  -no-window -no-audio -no-boot-anim -no-snapshot -no-metrics \
  -accel off -gpu swiftshader_indirect -feature -Vulkan
```

There is no usable KVM; `emulator -accel-check` reports that VMX/SVM is unavailable.
The shared Linux x86_64 cloud host has a four-CPU cgroup quota. Other research
and test workloads run concurrently. CPU/GPU software emulation and uncontrolled
host load confound timings and responsiveness; no physical-device performance
claim follows from this environment. Host audio is disabled.

The previously used API35 AVD had framework-service failures. This attempt uses
fresh userdata and requires repeated healthy package/activity services as well
as `sys.boot_completed=1`, followed by a successful framework package query.
A boot-completed flag by itself is insufficient.

## Reproduce on a healthy selected runtime

Use the existing APK paths above, with explicit device selection:

```sh
adb -s emulator-5558 install -r android/app/build/outputs/apk/debug/app-debug.apk
adb -s emulator-5558 install -r android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb -s emulator-5558 shell am start -W -n org.missionthunderbolt.prototype/.MainActivity
adb -s emulator-5558 shell am instrument -w \
  org.missionthunderbolt.prototype.test/android.test.InstrumentationTestRunner
python3 tests/android_lifecycle_smoke.py --serial emulator-5558 \
  --check-control-placement --send-memory-trim \
  --output dist/verification/api35-lifecycle
python3 scripts/android_performance.py --serial emulator-5558 \
  --apk android/app/build/outputs/apk/debug/app-debug.apk \
  --output dist/verification/api35-performance
```

The private cloud host's default adb-server home is read-only. Its local-adbd
fallback uses `adb-shell==0.4.4`, connects only to `127.0.0.1:5559`, pushes the two
explicit artifacts and runs the same package install/launch/instrumentation
commands. The public lifecycle/performance helpers support
`--direct-emulator 5559` in place of `--serial emulator-5558`.

## Outcome

The fresh-runtime attempt reached package/activity services at **12:17:52
America/New_York (16:17:52 UTC), 2026-10-30**, but never established completed
boot during its initial approximately ten-minute readiness window.

At **12:22:48 (16:22:48 UTC)** Android's Watchdog killed `system_server` PID 612:

```text
WATCHDOG KILLING SYSTEM PROCESS: Blocked in handler on main thread (main) for 60s
android.os.SystemProperties.native_set
android.app.PropertyInvalidatedCache.invalidateCache
com.android.server.accounts.AccountManagerService ... onPermissionsChanged
```

This is the observed stalled stack; it does not by itself establish why the
property write blocked. `com.android.phone` and `com.android.systemui` then
reported `DeadSystemException` at **12:22:53 (16:22:53 UTC)**. A Bluetooth-process
native SIGABRT was also recorded earlier at **12:22:36 (16:22:36 UTC)**; its
causal relationship to the Watchdog event is not established.

A diagnostic install of the exact app APK failed with
`cmd: Can't find service: package`. User-unlock inspection similarly reported
`cmd: Can't find service: user`; the credential-encrypted-availability property
was empty and window-policy state was unavailable. The boot-animation service
reported `stopped`, which did not establish healthy framework services or a
fully booted device. No application had been installed or launched at this
failure checkpoint, so these framework failures are not app crash evidence.

Android automatically restarted zygote/system services. One additional
five-minute readiness window used the cached first-boot work, without changing
boot properties, disabling Watchdog or weakening the readiness checks. Normal
WAKEUP/Menu input and `wm dismiss-keyguard` were accepted during recovery.
Window policy reported awake/system-ready, while user 0 was still
`RUNNING_UNLOCKING` at a transition checkpoint; those observations alone were
not treated as full readiness.

At approximately **12:26:12 (16:26:12 UTC)** three observations of
`sys.boot_completed=1`, healthy package/activity services and a successful
`pm path android` query established readiness. The image reports **Android 15,
API 35, x86_64**, fingerprint
`Android/sdk_phone64_x86_64/emu64x:15/AE3A.240806.019/12368160:userdebug/test-keys`.
Both selected APK installs returned `Success`. The installed package independently
reports version `0.1-research` / code 1, minSdk **23**, targetSdk **35** and
`DEBUGGABLE`; display size is **320×640** and the font-scale setting is **1.0**.

The first `am start -W` returned **`Status: timeout`**, `LaunchState: UNKNOWN
(-1)`, `WaitTime: 22129` ms. Instrumentation was not started on that result.
Subsequent state inspection found user 0 `RUNNING_UNLOCKED` and app process 3058
with a resumed, visible, focused `MainActivity` and a window surface. A surface
alone does not prove timely first-frame presentation. The crash buffer contained
no app crash at this checkpoint; system logs concurrently recorded ANRs in the
media provider, phone and calendar processes and repeated Bluetooth aborts.
Those observations do not establish which factor caused the launch timeout.

One ordinary force-stop/retry after the cached initial launch also returned
**`Status: timeout`**, `LaunchState: UNKNOWN (-1)`, `WaitTime: 28772` ms. Neither
Activity Manager timeout nor test assertions were changed. **Launch qualification
failed**; neither timeout is discarded or converted into a successful timing.

The retry eventually produced a framework `Displayed` event for `MainActivity`
at **12:30:37 (16:30:37 UTC)** with elapsed **+33s522ms**. App graphics diagnostics
contained nine rendered frames, all counted as janky. This establishes delayed
rendering beyond a mere surface allocation, but not timely launch or performance
acceptance. Logs include multi-second HWUI frames and surface synchronization
timeouts. A later focus snapshot showed an ANR dialog for `com.android.launcher3`
over the resumed app. These system-wide conditions prevent attributing the
timeout exclusively to application code or exclusively to host emulation.

One independent **diagnostic** instrumentation attempt was started separately
from the failed launch qualification, with unchanged assertions. Before starting,
package/activity services were present and the app process was alive. Normal UI
input selected an ANR dialog's **Wait** button. The subsequent screenshot showed
the rendered synthetic board/status/controls behind a **System UI isn't
responding** dialog; this was not an unobscured usability acceptance screenshot.

The private streaming-adbd harness had a **30-second transport read timeout**
despite a 90-second stream read setting and an external 230-second wrapper
(five-second termination grace). The transport timeout fired before receiving a
terminal instrumentation result. **The 230-second budget was not exhausted**;
this host-side transport failure is not an app failure. Closing that stream did
not stop the device-side runner.

Filtered device `TestRunner` logs then showed individual passing events for
accessible direction targets, shared map actions, zoom clipping and memory
callbacks. They also recorded this assertion failure:

```text
testAudioControlsDoNotAdvanceTurns
junit.framework.AssertionFailedError
DemoActivityTest.java:360
```

That assertion requires the volume SeekBar's progress to exceed 30 after an
injected Right key. Focus was affected by system ANR overlays in this run; the
available evidence does not isolate a new app/API defect from those conditions.
The next test had started when collection ended. These are **partial diagnostic
events**, not a completed test count or a pass/fail result for the 19-test suite.
No terminal `OK (19 tests)` result was obtained. No assertions were changed.

The owned emulator was terminated after the partial diagnostic was collected;
this was not a recorded 230-second deadline expiry. Its launcher exited 139
during shutdown; that is an emulator-process exit, not an Android app crash. No
active QEMU process remained. **Lifecycle and performance acceptance were not
run** on this runtime. No app crash was observed in the collected crash buffers;
this does not establish crash-free launch qualification.

For future diagnostic reproduction on a healthy runtime, keep the direct
transport/read timeouts at least as long as the independent overall deadline;
the private harness was corrected to 230/230 seconds after this attempt but not
rerun. Alternatively, bound the explicitly selected native-adb command with a
host process deadline. At expiry, stop the instrumented test app or the owned
emulator: closing a local transport alone does not bound device-side execution.
Use a stable accelerated API35 emulator or a physical device to rerun valid
launch, all 19 tests, lifecycle and performance checks. Do not suppress the
framework watchdog, alter boot-completion properties or weaken test assertions.

Raw readiness, install, launch, window/activity, graphics, screenshot and partial
diagnostic evidence remains under ignored `dist/verification/api35-2026-10-30/`.
The pre-app Watchdog/system logs and emulator logs remain in private cloud setup
storage. No Actions workflow, new app build, production source change or release
was triggered for this attempt.

Existing API23 evidence is documented separately in `ANDROID_RUNTIME.md` and
`ANDROID_PERFORMANCE.md`. Issue #18 remains open for reliable current-API
runtime qualification and its physical ARM64 objective.

## Subsequent input-recipient diagnostic guard

After collecting the API35 result, the audio-controls test was strengthened to
assert both `Activity.hasWindowFocus()` and the SeekBar's `hasFocus()` on the UI
thread immediately before and after the injected Right key. The existing
progress-above-30 and unchanged-turn assertions remain. There are no retries,
skips or relaxed assertions. This checks the intended input recipient in future
runs; it does not retroactively prove the cause of the API35 failure or change
application behavior. The line-360 stack above belongs to the **old** test APK;
the new assertions shift source line numbers.

Local `gradle --no-daemon assembleDebug assembleDebugAndroidTest` completed
successfully in 12 seconds. The application APK retained exactly the original
hash/4,156,433-byte identity above. The test APK changed from the original
35,126-byte `292a3d1ce4e72047fa56ef1df5864fb255a0fb86c6f003b36f20200352f0308e`
artifact to a **23,634-byte** artifact with SHA-256:
`62e4ed8cf5bf2ef547ac31d1ba775906b93743c34ee42da2f9fb60167361bb45`.

The guarded APK pair was installed on the cached private **API23 / Android6.0
x86_64** AVD, using transport/read/overall command timeouts of 200 seconds.
Both installed APKs were pulled back and their SHA-256 hashes matched the selected
files. Launch returned `Status: ok`, ThisTime/TotalTime **1573 ms**, WaitTime
**1699 ms**. The full suite reported measured font scale **1.0**, portrait,
target SDK **35**, and completed **19 tests: 17 passed, two failed, zero errors**
in 68.554 runner seconds. It was **not** a passing full-suite run.

The failures were `testAudioPreferencesSurviveRecreation` and
`testStateSurvivesRecreation`: both failed the existing `awaitRecreated` check,
`A distinct live activity was not recreated`. Those assertions were retained;
this focused diagnostic change does not resolve or classify those failures.
The changed audio-controls case was not among the full-suite failures.

A separate focused invocation then explicitly verified the changed case:

```sh
adb -s emulator-5556 shell am instrument -w \
  -e class org.missionthunderbolt.prototype.DemoActivityTest#testAudioControlsDoNotAdvanceTurns \
  org.missionthunderbolt.prototype.test/android.test.InstrumentationTestRunner
```

The cloud run used the equivalent explicitly selected local-adbd port **5557**.
It returned **`OK (1 test)`**, 2.726 runner seconds, with all four new focus
assertions and existing progress/turn checks intact. This proves the new guard
can pass with a valid input recipient on that tested API23 runtime. It does not
convert the failed 19-test run into a pass. The owned API23 emulator was stopped
afterward; raw identities, launch, full-suite and focused results remain under
ignored `dist/verification/audio-focus-guard-api23/`.

The guarded test APK was **not** installed or run on API35; the API35
observations above all used the original APK pair. No production application
source change or API35 fix is claimed.

### Recreation fixture ownership

The same two recreation cases were subsequently run once each in isolation on
the restarted cached API23 AVD, with unchanged 20-second/liveness/state checks.
Both returned **`OK (1 test)`**: audio preferences in **10.098** runner seconds,
state restore in **3.125** seconds. Event logs recorded initial and subsequent
resume callbacks and task destruction. This shows the failures were not
consistent in isolation; it does not establish the cause of the failed full run.
Raw focused results and lifecycle/window snapshots remain under
`dist/verification/audio-focus-guard-api23/recreation-isolated/`.

Review of Android 6's
[ActivityInstrumentationTestCase2](https://android.googlesource.com/platform/frameworks/base/+/android-6.0.1_r81/test-runner/src/android/test/ActivityInstrumentationTestCase2.java)
and [ActivityTestCase](https://android.googlesource.com/platform/frameworks/base/+/android-6.0.1_r81/test-runner/src/android/test/ActivityTestCase.java)
shows that the fixture caches the launched Activity and teardown finishes that
cached instance. `awaitRecreated` therefore now calls `setActivity(candidate)`
only after its existing distinct/live checks succeed, keeping the test fixture
aligned with the replacement Activity. The timeout, monitor matching, liveness
criteria and state assertions are unchanged.

This is a test-fixture ownership correction, **not proof of a leaked Activity or
the cause of the two failures**. Android's destroyed original Activity can still
request finish using its token, which the replacement reuses; cached-object
identity alone is insufficient to prove that cleanup failed.

The ownership-corrected debug test build completed in **11 seconds**. Its
**22,593-byte** APK has SHA-256
`021e1cf650b903903cb232f5a4b800df22cb17e3f60c4c111efdfe60ddd7aa04`;
the application APK remains byte-for-byte unchanged. This is a third test-artifact
identity, distinct from both the original API35 APK and the focus-only APK above.
Its full run completed **19 tests: 16 passed, three failed, zero errors**, in
**87.26** runner seconds; all three recreation cases failed the unchanged
distinct/live check. No second full run was attempted on that failed build.
The ownership correction alone did not resolve the observation problem.

Diagnostic-only UI-thread identity/liveness/focus logs were then added. That
23,601-byte test APK, SHA-256
`96fe11b084a49ba0582c6d25f3df7b4e5cb26b6235a1c4a266114f68581ade6f`,
completed **19 tests: 17 passed, two failed, zero errors**, in **71.525** runner
seconds. Audio/state requests began with live, focused, attached Activities.
The monitor returned a destroyed original followed by a distinct already
destroyed/finishing object, then timed out; placement instead received a live
candidate. Event logs showed the current tasks remained alive until failed-test
teardown, while preceding tests' tasks were destroyed around recreation. The
app crash buffer was empty. These observations ruled out an unready original
window as the missing condition, without proving a production app failure.

Android 6's
[Instrumentation implementation](https://android.googlesource.com/platform/frameworks/base/+/android-6.0.1_r81/core/java/android/app/Instrumentation.java)
also matches Activity monitors during destruction, and each monitor holds a
single last-Activity slot. A delayed destruction can therefore overwrite the
replacement observation. A short task-ID-logging two-case probe passed, so it
did not directly reproduce the stale-object/task correlation; the original
full-run failures and logs remain recorded rather than being replaced by that
pass.

### Bounded observation of the replacement

The recreation helper now registers `Application.ActivityLifecycleCallbacks`
**before** its single `recreate()` request and queues only resumed, distinct
`MainActivity` instances in the original task. A 16-entry queue fails explicitly
on overflow. It consumes events outside the UI thread within the same
**20-second** deadline, waits for UI idle, rechecks distinct/live/not-finishing
and task identity on the UI thread, and updates the cached fixture only on
success. It unregisters callbacks in `finally`. Destruction notifications cannot
overwrite this queue. All original state assertions and the new volume-focus
assertions remain; there are no sleeps, repeated recreation requests or timeout
increases. This changes test observation and fixture ownership, not the app.

The final local build completed in **10 seconds**. Its **25,082-byte** test APK
has SHA-256
`6463f05eacdc6f5cd81c2a4d33fdbeb56161f5e130b9225786d52a2f09183f64`.
The app APK retains the original hash. Both installed APKs were pulled and their
hashes matched the selected final artifacts. **Two consecutive full 19-test runs
passed** on API23 x86_64: **31.978** and **31.941** runner seconds. Each reported
measured font scale **1.0**, **portrait**, target SDK **35**, and **528 consumed
authored PCM frames**. All three recreation/state checks and the strengthened
volume-focus/progress/turn checks passed in both runs. These results validate
the bounded observation change in that configuration; the earlier failed runs
remain documented, and no broader device/font/orientation coverage is implied.

The final full-suite command was equivalent to:

```sh
adb -s emulator-5556 shell am instrument -w \
  org.missionthunderbolt.prototype.test/android.test.InstrumentationTestRunner
```

The cloud run used explicitly selected local-adbd port **5557**, with transport,
read and overall command deadlines of **200 seconds**. Final identities, both
complete terminal results and lifecycle/TestRunner logs remain under
`dist/verification/audio-focus-guard-api23/resumed-observer/`.
The owned API23 emulator was stopped after review of the two passing runs.
No API35 rerun was performed. Its original launch failures and incomplete
diagnostic suite remain unqualified; the new API23 results are not substituted
for them.
