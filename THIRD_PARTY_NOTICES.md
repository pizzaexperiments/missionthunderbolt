# License boundaries and third-party notices

The maintainer selected MIT for this project's newly written code and
accompanying original documentation. See LICENSE. This grant does not apply to
the historical Mission: Thunderbolt executable, art, audio, fonts, manual,
screenshots or derived original assets. Those remain restricted pending a
separate rights determination; see docs/RIGHTS_AND_PROVENANCE.md.

SDL2 is separately licensed under the zlib license. Desktop distributions must
include its upstream copyright/license notice from the exact built version
(vcpkg `share/sdl2/copyright` or the distro/upstream license file). Preserve any
additional dependency notices identified by the build. System libraries and
platform SDKs retain their own terms; the MIT file does not relicense them.

Android native libraries statically incorporate NDK runtime code (libc++,
libc++abi, libunwind and compiler-rt in the measured release build). Preserve
the exact NDK `NOTICE` and `NOTICE.toolchain` files with review packages. The
dependency evidence tool records NDK/LLVM versions and archive hashes per ABI;
composite notices contain multiple licenses, so do not apply the project MIT
license to these archives or assume every notice applies to the final binary.
Individual component attribution still requires review before distribution.

Java, Gradle, Android SDK/NDK/CMake, Ghidra and The Unarchiver are development/
research tools with separate licenses. They are not bundled with the demo.
Record the tool versions used for each build. Do not include local SDKs,
research archives or extracted originals in source/package artifacts.
