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
truncated, oversized or palette-invalid inputs fail. Inputs are resource payloads,
not standalone PICT files with a 512-byte file header. Vector drawing, complex
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
