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
