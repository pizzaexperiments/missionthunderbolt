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
