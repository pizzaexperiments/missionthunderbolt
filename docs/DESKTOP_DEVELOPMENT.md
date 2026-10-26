# Native desktop synthetic demo — issues #19 and #20

The optional SDL2 renderer uses the same portable C++ state/saves as Android.
It draws synthetic tiles only; no Mac emulator, historical art or network service
is bundled. The terminal host remains available without SDL2.

## Controls and storage

WASD/arrows or controller D-pad move. Left stick has a dead zone and one action
per direction change. Tab/controller Back switches skin without resetting state;
R/controller Start restarts; Ctrl-S saves and Ctrl-L loads; Escape/Q quits.
Controller hotplug is supported. The host redraws on input/window events rather
than running a busy simulation loop. It stays silent (no-audio fallback).

The default save directory comes from `SDL_GetPrefPath`: typically AppData on
Windows and Application Support on macOS. Override with `--save-dir PATH` for
isolated tests. Saves use a temporary file then atomic replacement (MoveFileExW
on Windows, rename on POSIX). Invalid saves leave gameplay available and emit a
warning. Use the synthetic save format documented in SAVE_FORMAT.md.

## Windows x64

Install Visual Studio's C++ toolchain, CMake >=3.22.1, Ninja and a checked-out
vcpkg at the baseline pinned in `vcpkg.json`. In a developer shell set `VCPKG_ROOT`
to that checkout, bootstrap it, then run:

```sh
cmake --preset desktop-windows
cmake --build dist/windows --parallel 4
ctest --test-dir dist/windows --output-on-failure
cmake --install dist/windows --prefix dist/packages/windows-x64
```

The x64-windows-static triplet and static MSVC runtime avoid relying on a loose
SDL DLL. Include the vcpkg SDL2 copyright notice with the executable. The
manual-only desktop workflow prepares a portable research ZIP. It has **not**
been executed on Windows in this task; Windows launch/controller/package
acceptance remains pending. No public signed release is claimed.

## Linux local validation

With SDL2 development packages installed:

```sh
cmake -S . -B dist/sdl -DMT_BUILD_SDL_HOST=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build dist/sdl --parallel 4
ctest --test-dir dist/sdl --output-on-failure
./dist/sdl/mission-thunderbolt-demo
```

An extracted Debian SDL2 2.32.4 installation was used locally, with its
multiarch include directory supplied as a machine-only CMake flag. The dummy
video-driver smoke test checks queued keyboard/controller actions, unchanged
state when switching modes, nonblank rendered pixels and an on-disk save/load
round-trip. It does not prove physical controller behavior or native Windows/
macOS launch. The root native tests also run through CTest.

## macOS Intel and Apple Silicon

On matching Mac hosts with Xcode command-line tools, CMake, Ninja and the pinned
vcpkg checkout (`VCPKG_ROOT`), use `desktop-macos-arm64` or `desktop-macos-x64`:

```sh
cmake --preset desktop-macos-arm64
cmake --build dist/macos-arm64 --parallel 4
ctest --test-dir dist/macos-arm64 --output-on-failure
cmake --install dist/macos-arm64 --prefix dist/packages/macos-arm64
open dist/packages/macos-arm64/mission-thunderbolt-demo.app
```

The presets select the matching vcpkg triplet/architecture and macOS 11 minimum.
CMake creates a native `.app` with bundle identity/version metadata. Static SDL2
plus system frameworks avoids bundling an emulator or proprietary original
content. Copy the vcpkg SDL2 copyright notice alongside the app. A manual matrix
prepares separate ARM64/Intel tarballs preserving executable modes. These jobs
have **not** run in this Linux task. Native launch, platform save paths, physical
input and both architecture packages still require Mac verification.

Unsigned local research bundles are not notarized public releases. For a reviewed
release, decide the project license and asset rights, obtain a Developer ID
certificate, sign the final bundle with the hardened runtime, inspect its linked
libraries (`otool -L`) and entitlements, submit a distribution archive with
`xcrun notarytool` using a private keychain profile, staple and validate the ticket,
and test on a clean Mac. Keep certificates/passwords out of Git and logs; do not
auto-publish or weaken Gatekeeper to label an unsigned app verified.
