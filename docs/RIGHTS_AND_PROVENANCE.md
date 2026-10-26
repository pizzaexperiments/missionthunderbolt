# Rights and provenance — issue #3

## Confirmed repository facts and unknown rights

The checked-in engine calls itself a synthetic demonstration. No historical
archive is supplied to this checkout. The current task cannot confirm the
original game's authorship, copyright owner, distribution license, manual rights,
font/art/audio permissions, or the provenance of earlier reported extractions.
The issue's reference to `tb2.zip` is a lead, not possession or a license.

| Material | Evidence available here | Distribution decision |
| --- | --- | --- |
| Original executable, CODE/CREL and resource forks | No source archive or rights document available | Local research only when lawfully supplied; no public redistribution |
| PICT, sound, fonts, manual, captures/derivatives | No rights grant available | Do not include in public packages or upload to CI |
| Synthetic C++/Java/Python code and generated test fixtures | Source and synthetic fixture generators in Git | Authored for this prototype; repository-wide license selection remains a maintainer decision |
| Android/Gradle/NDK and any desktop dependency | Installed build tools, separate upstream licenses | Retain upstream notices; packaging requires dependency/license review |

This records what is known; it does not establish legal permission or silently
apply an open-source license to someone else's work.

## Local import and provenance record

Use an archive you legitimately possess. No download of historical content is
required for builds/tests. Never supply account credentials or signing keys in
Git or issue text.

```sh
python3 scripts/import_original.py /path/to/your/archive.zip
```

The importer copies to ignored `local-original/`, refuses overwrites and prints
size/SHA256. Record acquisition source/date, game version, source filename,
SHA256, rights holder/contact evidence, permission scope and limitations in an
untracked local provenance note beside the archive. A hash proves identity,
not ownership or a redistribution grant. Store extractions and previews under
ignored `local-generated/` and keep proprietary material out of public logs.

Before committing, inspect staged paths and run:

```sh
python3 scripts/check_public_inputs.py --staged
python3 scripts/check_public_inputs.py
```

The checker rejects private output directories, AppleDouble sidecars and common
historical-resource/archive/package extensions in the index, including forced
adds that `.gitignore` alone cannot prevent. It does not inspect content or
recognize every copyrighted file: human review remains necessary. Public parser
tests construct synthetic data in code. Local test execution also runs this guard.

## APK and desktop asset policy

Ship only synthetic content until an explicit rights record authorizes each
historical input and its derivatives. Future permission must identify the
material, allowed distribution channels and attribution/license obligations.
Rights to analyze a private copy do not imply rights to publish it or to bundle
it in an APK. Any change to this boundary requires maintainer review. No original
assets were imported, extracted or published by this issue's implementation.

Rights verification against an owner/source and permission for original content
remain **unresolved**, so #3 is not represented as fully complete.
