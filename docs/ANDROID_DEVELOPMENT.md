# Android development — synthetic research demo

## Toolchain

Use Java **17**, Gradle **8.7**, Android Gradle Plugin **8.6.1**, SDK platform
**35**, build-tools **35.0.0**, NDK **27.2.12479018**, and CMake **3.22.1**.
Android SDK command-line tools **19.0** are the tested SDK installer. The build
selects these component versions explicitly. There is no Gradle wrapper yet;
install Gradle 8.7 or select it as the local Gradle distribution in Android Studio.

Linux x86_64 is locally verified. Windows requires Git, Java 17, Gradle and the
Android SDK (use PowerShell equivalents for the POSIX examples below). On macOS,
install the matching Android Studio/command-line tools host distribution and
Java 17; Apple Silicon NDK tools may require Rosetta. Windows/macOS commands have
not been executed in this Linux environment. Use official vendor distributions
and verify their published checksums; do not disable TLS or SDK verification.

## Build a fresh checkout

Clone the repository and select the desired reviewed branch. `develop` is the
integration branch; implementation work belongs on feature branches.

```sh
git clone --branch develop https://github.com/pizzaexperiments/missionthunderbolt.git
cd missionthunderbolt
# Set JAVA_HOME to your JDK 17 and ANDROID_HOME to your installed Android SDK.
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/19.0/bin:$ANDROID_HOME/platform-tools:$PATH"
java -version
gradle --version
sdkmanager --licenses
sdkmanager 'platforms;android-35' 'build-tools;35.0.0' 'ndk;27.2.12479018' 'cmake;3.22.1' 'platform-tools'
sh scripts/test_local.sh
cd android
gradle --no-daemon assembleDebug
"$ANDROID_HOME/build-tools/35.0.0/apksigner" verify app/build/outputs/apk/debug/app-debug.apk
```

Android Studio can open `android/` and run the `app` debug configuration with the
same SDK/NDK selections. SDK Manager installs additional components as needed.
There are no original game assets, signing credentials or server dependencies
required for the synthetic demo. Minimum runtime is **Android 6 / API 23**;
compile API 35 does not imply a minimum of 35. Target API is **35** after the release-lint fix. This alone does not establish
Play Store eligibility, signed-release readiness or behavior on every API level.

## Install, launch and inspect

Enable developer options/USB debugging on a device and approve the computer.
Check that `adb devices` lists exactly the intended device as `device`; use
`adb -s SERIAL` for every command when more than one device is connected.

```sh
adb devices
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -W -n org.missionthunderbolt.prototype/.MainActivity
adb logcat -d -b crash
# Example keyboard movement and reset verification through the UI:
adb shell input keyevent KEYCODE_DPAD_RIGHT
adb shell input keyevent KEYCODE_DPAD_LEFT
```

The app must show a RESEARCH DEMO label and an ASCII-derived synthetic board.
Movement, mode switch and restart are demo controls; no historical fidelity is
claimed. `adb install` success alone does not prove launch or gameplay.

To create a disposable emulator (x86_64 Linux example):

```sh
sdkmanager 'emulator' 'system-images;android-35;default;x86_64'
printf 'no\n' | avdmanager create avd --name mt-api35 --package 'system-images;android-35;default;x86_64'
"$ANDROID_HOME/emulator/emulator" -avd mt-api35 -no-snapshot -no-audio
```

Use a host-compatible system image on macOS/Windows. Linux hardware acceleration
requires accessible KVM. Software emulation (`-accel off -gpu swiftshader`) can
be slow and is not a substitute for measuring real ARM64 device performance.
Do not start/stop an emulator or clear app data belonging to someone else.

## Troubleshooting

- JDK/Gradle errors: check `java -version`, `JAVA_HOME` and `gradle --version` in
  the same shell. Java 21 is not the documented JDK for this workflow.
- SDK not found: set `ANDROID_HOME` or put `sdk.dir` in ignored
  `android/local.properties`; do not commit an absolute SDK path.
- NDK/CMake missing: install the exact pinned versions above. Do not edit
  tracked build files merely to match an accidental local tool installation.
- Read-only home: set `ANDROID_USER_HOME` and `GRADLE_USER_HOME` to writable
  local directories. Avoid conflicting deprecated Android preference variables.
- Corporate/cloud proxies: retain supplied proxy/CA trust; Java/Gradle may need
  explicit proxy system properties and a trust store containing that CA. Never
  disable certificate verification. Keep machine-specific settings outside Git.
- SDK command changes: `cmdline-tools/latest` is a moving target; use 19.0 for
  the documented `sdkmanager` interface.
- `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: another build may have a different debug
  key. Uninstall only after preserving any app data you need.
- `INSTALL_FAILED_NO_MATCHING_ABIS`: check the APK's packaged native ABIs.

See [local build evidence](verification/android-build.md) and
[local testing](LOCAL_TESTING.md). GitHub Actions is paused, including manual dispatch. Run local checks and post
exact commands, results and limitations in the PR. See [the pause policy](../.github/ACTIONS_PAUSED.md).
