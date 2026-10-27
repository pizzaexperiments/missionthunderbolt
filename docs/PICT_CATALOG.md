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
resource-ID mapping. The supplied original picture payloads have now passed
the supported subset as recorded below. Independent decoder comparison is recorded below. Original-runtime visual
comparison and semantic attribution remain pending; decoding is not proof of faithful
original presentation.

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

## Independent decoder comparison — 2026-10-27

ImageMagick **7.1.1-43 Q16 x86_64** was used as a second PICT implementation:

```sh
python3 scripts/verify_pict_independently.py \
  --manifest local-generated/original-resources/manifest.json \
  --output local-generated/independent-pict-resources.json
python3 scripts/verify_pict_independently.py --standalone /path/to/Slides/INTRO* /path/to/Slides/END* \
  --output local-generated/independent-pict-slides.json
```

The first command returned **exit 2**, retaining the disagreement: **907 exact,
1 pixel mismatch, 0 dimension mismatches, 0 failures** among 908 resource pictures.
All **26 standalone slides** matched exactly (exit 0). Thus **933/934** supplied
pictures agree with the independent decoder. Actual original images and detailed
reports remain ignored. No mismatch is accepted using a tolerance.

Both decoders are compared at the same explicitly defined channel projection:
ImageMagick emits big-endian 16-bit RGB, then its high bytes are compared to this
decoder's high-byte QuickDraw RGB output. Its default conversion directly to 8-bit
normalizes/rounds 16-bit values and can differ by one channel value; that is a
different quantization rule. This comparison does not establish which projection
an original runtime display used. Dimensions, different-pixel count, maximum
channel delta, first differing coordinate and both RGB hashes are recorded.

The unresolved original case is PICT **361** in **Black & White**, **30×65** pixels:
**355** pixels differ, maximum channel delta **255**, first difference **(0,1)**.
There is no change to its decoding. An independently authored 30×4 BitMap with
one known black pixel per row and two nonzero padding bits also disagrees with
this ImageMagick version (**116/120** pixels). The native regression checks its
exact known black-pixel positions and verifies padding is not painted. This
reproduces a limitation of the reference path for monochrome BitMaps, but is not
a proof of the original picture's appearance. Original-runtime evidence or a
third suitable decoder is needed before resolving that case.

The checker verifies extraction hashes, forces the PICT reader, applies reference
process time/cache limits, refuses existing reports and keeps in-repository output
under `local-generated/`. Synthetic tests exercise real independent 1/4/8-bit
indexed decoding when ImageMagick is installed; absence skips that optional test
explicitly. Dimension/pixel mismatches and timeouts have deterministic regressions.
ImageMagick is a development-only comparison dependency and is not packaged.

At this checkpoint #5 remained open for the discrepancy and semantic role
attribution. The follow-up below resolves the decoder/catalog scope; runtime
presentation remains #16.

## Third-decoder follow-up and catalog closeout — 2026-10-27

[PR #28](https://github.com/pizzaexperiments/missionthunderbolt/pull/28) merged
as `b1388131976492c6ce978fc48d920bb2afaea9e4`. GraphicsMagick from Debian's signed
package index (`1.4+really1.3.45+hg17696-1`, runtime reports
**1.4 snapshot-20250331 Q16**) was extracted locally as a research tool. It is
not a new runtime/package dependency of the game. Its PICT implementation shares
historical ancestry with ImageMagick, so these are not wholly unrelated oracles.

```sh
python3 scripts/verify_pict_independently.py --backend graphicsmagick --tool /path/to/gm \
  --manifest local-generated/original-resources/manifest.json \
  --output local-generated/graphicsmagick-pict-resources.json
python3 scripts/verify_pict_independently.py --backend graphicsmagick --tool /path/to/gm \
  --standalone /path/to/Slides/INTRO* /path/to/Slides/END* \
  --output local-generated/graphicsmagick-pict-slides.json
```

Use the normal vendor installation or supply its required library search path
for a privately extracted binary. GraphicsMagick uses separate bounded convert/
identify commands; both have a 20-second process timeout and cache limits. The
ImageMagick command and old `--imagemagick` option remain supported. Reports name
the backend as well as its version.

| Input group | ImageMagick | GraphicsMagick | Exact with at least one external decoder |
| --- | --- | --- | --- |
| 908 resource pictures | 907 exact, 1 pixel mismatch | 808 exact, 100 failed | 908 |
| 26 standalone slides | 26 exact | 26 exact | 26 |

Reports were joined by **fork, resource ID and source SHA256**, checking identical
resource sets. There are 807 resource pictures matching both external decoders;
100 match only ImageMagick and one only GraphicsMagick. GraphicsMagick's resource
command deliberately exits **2** because of the 100 failures. An inspected failed
sample reports `Scanline length too small`; failed samples are not counted as
successful or assigned tolerance. No production decoder code changed.

The disputed **Black & White / PICT 361** matches GraphicsMagick exactly at 30×65
pixels, with RGB SHA256
`67d5f3326f08a78b612bc1bd53529e26886142ebea5fc6811049fe915e424c42`.
Closer inspection identifies it as an **indexed one-bit PixMap**, rather than
a plain BitMap. The earlier plain-BitMap fixture did not reproduce that exact
format. A new authored 30×4 indexed PixMap, with one known black pixel per row
and two nonzero padding bits, matches GraphicsMagick exactly and differs from
ImageMagick by **6/120** pixels. Its expected pixels also match the authored
BitMap's native output. This corroborates the native result for the disputed
format without changing either the output or tolerance. The original
ImageMagick mismatch report and earlier BitMap evidence remain preserved.

### Visually attributed catalog entries

These labels follow inspection of the private contact sheet and full-size
previews, with resource identities read from the catalog report. They describe
visible graphics, not recovered event handlers or game rules.

| Resource fork / ID | Dimensions | Observed role | Private preview / sheet cell |
| --- | --- | --- | --- |
| 16 Colors / 934 | 167×177 | Legend for selection, wielded/reserved weapons, worn and activated items | `0080_PICT_934.png`, sheet 0 cell 80 |
| 16 Colors / 964 | 343×227 | Game title and credits panel | `0083_PICT_964.png`, sheet 0 cell 83 |
| 16 Colors / 984 | 328×289 | Display/sound options, gender and difficulty panel | `0085_PICT_984.png`, sheet 0 cell 85 |
| 16 Colors / 994 | 328×289 | Character creation panel with attributes, hit points and difficulty | `0086_PICT_994.png`, sheet 0 cell 86 |

Other tile/item/entity strips retain neutral resource-ID names until supported
by further visual or executable evidence. The complete catalog already maps all
908 resources and 26 slides, with paginated contact sheets and explicit source
IDs/hashes. Newly identified panels do not establish that their depicted controls
work, nor do they establish the runtime layout.

Issue #5's stated decoder/catalog acceptance is satisfied: authored 1/4/8-bit
fixtures, externally corroborated pixels/dimensions for every supplied picture,
conversion success/unsupported reports, contact sheets/resource-ID mappings and
ignored original outputs. Broader Classic runtime screenshot/menu/layout
verification belongs to #16; asset redistribution permission remains #3.
