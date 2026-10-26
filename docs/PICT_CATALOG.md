# Indexed PICT catalog — issue #5

```sh
python3 scripts/pict_catalog.py local-generated/extracted/manifest.json --output local-generated/pict-catalog
```

The catalog validates each payload against the extraction manifest's SHA256 and
writes PNG previews, a stable nearest-neighbor contact sheet and a JSON report
mapping resource fork/ID/hash to image filename and contact-sheet cell. Semantic
sprite names are deliberately not guessed. All output stays local/ignored.

Supported subset: PICT v1/v2 rectangular raster drawing, 1-bit BitMaps and indexed
1/4/8-bit PixMaps, color tables, BitsRect/PackBitsRect, srcCopy, rectangular clipping
and nearest-neighbor source/destination scaling. PackBits rows are bounds checked;
truncated, oversized or palette-invalid inputs fail. The manifest route reads resource payloads. Standalone files use the explicit
`--standalone` option, which skips the standard 512-byte file header. Vector drawing, complex
regions, direct-color PixMaps and other transfer modes are explicitly unsupported,
not silently rendered as if accurate. The process exits 2 if any resource is
unsupported/malformed, retaining a per-resource reason and success counts.

Synthetic tests check exact dimensions/pixels/palette values at 1/4/8-bit depth,
PackBits runs and malformed rows, unsupported opcodes, PNG output and catalog
resource-ID mapping. No original PICT is available here. Visual comparison,
full opcode coverage actually encountered in the game and original-asset
attribution remain pending; this is a tested decoder subset, not completion of
original artwork recovery.

## Original-input validation

After recognizing non-drawing QuickDraw comments and DefHilite state, all **908
PICT resources** from the supplied source passed this decoder and generated local
PNG previews. Contact sheets paginate at 128 images per sheet (eight sheets),
avoiding unbounded sheet allocation. Report fields identify `sheet` and `cell`.
One generated sheet was visually inspected: palettes, sprite strips, window art,
text and dialog images are recognizable. This is not an independent pixel-perfect
comparison with original runtime rendering. Full original outputs remain ignored.

Standalone data-fork pictures are also supported:

```sh
python3 scripts/pict_catalog.py --standalone /path/to/picture.pict --output local-generated/file-pict-catalog
```

Foreground/background RGB color state is honored for 1-bit bitmap copies.
All **26 INTRO/END slide data forks** in the supplied archive decoded locally
through this route, in addition to the 908 resource-fork PICTs. Standalone reports
record the source filename/hash and `id: null`; they do not invent resource IDs.
This makes **934 decoded picture payloads**, not 934 distinct semantic sprites.
