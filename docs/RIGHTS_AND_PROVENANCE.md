# Rights and provenance — issue #3

## Confirmed repository facts and unknown rights

The checked-in engine calls itself a synthetic demonstration. The user later supplied a conversion handoff containing the historical
StuffIt archive and a manual; they remain in ignored local-original/. The manual credits Dave Scheifler (copyright 1987–1992) and John Calhoun
(creature closeup art), and identifies MegaCorp International. Its restrictive
notice does not grant public redistribution. Present ownership, any later
license grants, font/art/audio permissions and earlier extraction provenance
remain unverified.
The issue's reference to `tb2.zip` is a lead, not possession or a license.

| Material | Evidence available here | Distribution decision |
| --- | --- | --- |
| Original executable, CODE/CREL and resource forks | User-supplied archive and restrictive manual notice | Local research only when lawfully supplied; no public redistribution |
| PICT, sound, fonts, manual, captures/derivatives | Manual and reference images supplied; no redistribution grant | Do not include in public packages or upload to CI |
| Synthetic C++/Java/Python code and generated test fixtures | Source and synthetic fixture generators in Git | MIT selected by the maintainer for newly written code; see LICENSE and THIRD_PARTY_NOTICES.md |
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
it in an APK. Any change to this boundary requires maintainer review. Original inputs were later imported and extracted locally for research; none
were added to public Git history or packages.

Issue #3's workflow criteria are complete: confirmed and unknown rights are
recorded, private import is guarded, and distribution is synthetic-only.
Rights-holder verification and permission for historical content remain
**unresolved**. Closing the workflow issue grants no redistribution permission;
any future inclusion must pass the release review in #23.
