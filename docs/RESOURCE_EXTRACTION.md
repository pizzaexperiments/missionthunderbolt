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
