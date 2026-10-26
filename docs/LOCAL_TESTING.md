# Local validation and resource research

This repository contains a **synthetic demo**, not recovered original gameplay.

With Python 3, C++17 compiler and POSIX shell run:
```sh
sh scripts/test_local.sh
./dist/mt_desktop_demo
```
The script performs four synthetic resource-parser unit tests, core/API C++ tests, and a terminal-host smoke test.

To audit game resources you legitimately possess, put extracted `.rsrc` forks locally under `local-generated/resource_forks/` (ignored by Git), then:
```sh
python3 scripts/audit_resources.py local-generated/resource_forks --output local-generated/resource_manifest.csv
```
The report contains type/ID/size/PICT dimensions/SHA256 metadata only. It **does not decode PICT pixels** and does not disassemble CODE.

**APK status:** Android SDK/NDK and Gradle were unavailable in the local test environment. No installable Android APK has been verified. CI is manual-only to conserve Actions credits.

Never publish original game archives, code segments, art, audio, or derivatives without confirming redistribution permission.
