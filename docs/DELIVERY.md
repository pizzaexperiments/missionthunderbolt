# Files and distribution

- `local-original/`: ignored local input (e.g., `mission_thunderbolt.sit`). Never commit or upload to public CI without redistribution permission.
- `local-generated/`: ignored extracted resources, disassembly, sprites, converted audio and analysis data.
- `dist/`: ignored local builds. Do not publish builds containing original commercial resources without authorization.
- Native debug APK (synthetic research demo): download from the latest successful [Actions build](https://github.com/pizzaexperiments/missionthunderbolt/actions/workflows/build.yml) under **Artifacts**; log-in may be required. The APK will be produced only if the Android build actually succeeds.
- Source release: standard GitHub checkout/archive includes no original commercial content.

## Import existing original archive (local use only)

```sh
python3 scripts/import_original.py /path/to/mission_thunderbolt.sit
```

Verify the printed SHA256 against your source copy. Conversion scripts will later read `local-original/`. The ZIP supplied in this ChatGPT conversation remains separately available in the chat's files; it is not published by this repository.


## Local feature artifacts

The current local synthetic debug APK is copied to
`dist/mission-thunderbolt-research-debug.apk` with a SHA256 sidecar. Native source
also builds unsigned release APK/AAB outputs. See verification/android-build.md
and ANDROID_RUNTIME.md for exact evidence. These files are local review artifacts,
not a GitHub Actions upload or a signed public release. Original assets stay out
of APKs/public packages; MIT applies only to the new project code.
