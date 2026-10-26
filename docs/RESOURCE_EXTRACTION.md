# Local resource extraction — issue #4

Only analyze inputs you legitimately possess; see RIGHTS_AND_PROVENANCE.md.
No `tb2.zip` or historical resource fork is available in this task, so the issue's
reported **15 CODE / 13 CREL** counts remain unverified.

```sh
python3 scripts/extract_resources.py /path/to/tb2.zip --output local-generated/extracted
```

Accepted inputs are ZIPs containing AppleDouble `._` members or `.rsrc` forks,
raw resource forks, AppleDouble and AppleSingle version 2 files. The tool reads
entry ID 2 as the resource fork; it never treats data forks as executable source.
StuffIt/BinHex decoding is not implemented: first decode locally with a trusted
appropriate tool, preserving resource forks and provenance. No Internet upload
or public artifact is required.

The deterministic JSON manifest records source basename, fork/member path,
four-character resource type, signed ID, payload size, SHA256 and output path.
Payload names use hexadecimal type bytes and a signed ID, avoiding unsafe names.
CODE/CREL bytes are extracted without assuming segmentation, relocation semantics
or entry addresses. Do not interpret an extracted segment as recovered game rules.

Malformed sections/references, duplicate resource IDs, truncated payloads,
invalid/overlapping AppleDouble entries, traversal/symlink ZIP members, duplicate
ZIP names and archive/member size limits fail explicitly. Entire input validation
precedes writing outputs. Existing output directories are never overwritten;
inside the checkout outputs must stay under ignored `local-generated/`.
Use a new directory for another extraction. Keep manifests private too: they may
identify user filenames and research metadata.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Synthetic tests cover extraction, exact bytes/hash metadata, signed IDs, empty
forks, deterministic manifests, malformed inputs, traversal and failure cleanup.
Original archive validation remains pending until supplied locally. The metadata
CSV auditor remains available for already-decoded `.rsrc` directories.

## Validation against the supplied archive (2026-10-26)

The later user-supplied handoff contains `mission_thunderbolt.sit`, 5,937,491 bytes,
SHA256 `733c6e31e44c354f2bfee00d549505700e6efe0f985cc35fb1642be6305ad443`.
The Unarchiver CLI 1.10.8, installed from Debian's signed package metadata,
successfully decoded StuffIt method 13 with per-member checksum checks intact:

```sh
unar -nr -s -k hidden -o local-generated/unpacked-source local-original/conversion-handoff/00_Source_Archive/mission_thunderbolt.sit
python3 scripts/extract_resources.py local-generated/unpacked-source --output local-generated/original-resources
```

The extractor now accepts a directory of AppleDouble sidecars/raw `.rsrc` files
as well as the previously documented inputs. It produced 1,571 resource entries,
including **15 CODE, 13 CREL, 908 PICT and 138 snd** resources. The full manifest,
input paths and proprietary payloads remain ignored/local. The counts are verified
for this `.sit`; the earlier issue's differently named `tb2.zip` is not assumed
byte-identical. No original code was executed or publicly redistributed.
