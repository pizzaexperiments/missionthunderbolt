# 68000 CODE/CREL analysis protocol — issue #7

Status: manual protocol prepared; original segments and an annotated original
call graph are **not available**. No disassembly results or addresses are claimed.

## Reproducible import protocol

1. Use the local extractor (RESOURCE_EXTRACTION.md). Preserve its manifest and
   payload hashes. Record Ghidra release/build, analysis options, game version
   and source SHA256 in ignored `local-generated/analysis/session.json`.
2. In a local Ghidra project outside public source, import each CODE resource
   separately as a **raw binary**, language **68000:BE:32:default** and default
   compiler specification. Verify that language ID exists in the installed
   release. Choose a temporary base of zero only as a file-offset coordinate;
   name the program `CODE_<signed-resource-id>`. Record that this is *not* a
   verified runtime load address. Do not combine segments at invented addresses.
3. Preserve resource ID 0 and any jump-table/header data for separate analysis.
   Do not disassemble all bytes indiscriminately: identify headers/data and
   justify candidate entrypoints from independently documented Macintosh loader
   structures or observed execution. Record segment-relative offsets alongside
   any eventual relocated runtime address.
4. Inventory CREL records as opaque data first. Determine endianness, record
   boundaries, relocation types/targets and patch arithmetic from evidence.
   Test each hypothesis on synthetic bytes and cross-check loader behavior before
   applying relocations. The name CREL alone does not establish a standard format.
5. Run analysis with recorded options. Inspect A-line Macintosh traps and their
   OS/version-specific definitions against authoritative Toolbox documentation.
   Label potential routines with confidence/evidence, not authoritative names
   inferred solely from decompiler output. Preserve ambiguous instructions/data.
6. Export a metadata-only symbol/call table: segment resource ID, file offset,
   confirmed load address if known, symbol hypothesis, call target/trap, evidence
   reference and confidence (`observed`, `corroborated`, `hypothesis`, `unknown`).
   Unresolved indirect/cross-segment calls remain unresolved. Keep bytes,
   decompiler listings and projects private until redistribution is authorized.
7. Corroborate candidate state transitions with original input traces from #6.
   Export public notes only after checking they contain no proprietary bytes.

## Completion gate

Before #7 can be closed, a supplied archive must yield verified segments; a
repeatable Ghidra session must import them; segmentation/relocation assumptions
must be documented; and actual annotated call graph/evidence notes must exist.
This protocol does not substitute for those results. The source archive, licensed
reference environment and original-specific analysis are external prerequisites.

## Supplied-source import verification (2026-10-26)

The source later became available and yielded 15 CODE / 13 CREL resources.
`scripts/prepare_ghidra_segments.py` validates extraction hashes and prepares
separate private binary files plus segment-ID provenance. It supplies **no**
guessed runtime addresses. Ghidra **12.2 PUBLIC (2026-10-16)**, distribution SHA256
`2c2cd776db3c1f6a097ba418922378ac3649cadd5e844a6f5f088ae628a7be67`, was run with
Temurin JDK **25.0.1+8** (Ghidra 12.2 requires JDK 25).

```sh
python3 scripts/prepare_ghidra_segments.py local-generated/original-resources/manifest.json --output local-generated/analysis/segments
# GHIDRA_HOME is your verified installation; use its required JDK.
"$GHIDRA_HOME/support/analyzeHeadless" local-generated/analysis/ghidra-project mt-code-segments \
  -import local-generated/analysis/segments/*.bin -loader BinaryLoader \
  -processor 68000:BE:32:default -noanalysis -max-cpu 2 \
  -scriptPath scripts/ghidra -postScript RecordImport.java local-generated/analysis/verified-imports
```

All **28 raw imports succeeded**, and program language, byte length and SHA256
matched the prepared segments. `RecordImport.java` emits metadata only. Files,
projects and reports remain ignored/local. Base zero is an offset coordinate,
not a discovered runtime load address. CREL is imported as opaque data; no
relocations are applied. Automatic analysis is deliberately disabled until valid
entrypoints/segment layout are established. **No annotated gameplay call graph,
original rule reconstruction or faithful behavior is claimed.** Those remain
substantial #7 acceptance criteria, now unblocked for source-level research.
