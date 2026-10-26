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
