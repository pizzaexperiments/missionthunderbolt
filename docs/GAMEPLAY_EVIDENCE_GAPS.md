# Historical gameplay work — issues #8 through #12 and #16

These issues require original behavior evidence from #6/#7. The source archive, manual and extracted assets are now available locally, and
validated jump-table-guided static call candidates have been generated. No original
runtime captures are available. Isolated RNG arithmetic, initialization and
continued draws have now been corroborated against original 68000 instructions;
see [RNG research](RNG_RESEARCH.md). Grid record addressing, coordinate clipping
and selector/fallback control flow with explicit linked-record service shims
have also been checked against original instructions; see [grid research](GRID_RESEARCH.md). Full gameplay
semantics remain incomplete. The
synthetic engine is useful for integration tests, not a source of historical
rules. No guessed combat, inventory, AI, generation or UI has been added as if it
were recovered behavior.

| Issue | Missing evidence and next executable research step | Current result |
| --- | --- | --- |
| #8 generation/progression | New-game/seed traces, map/resource interpretation, mission transitions and win/lose observations; correlate with generator/control-flow candidates | Blocked on #6/#7; no recovered algorithm or golden cases |
| #9 movement/turns/FOV | Before/after movement traces covering walls, diagonals, waiting, line of sight and turn cost; identify scheduler and collision routines | Blocked on #6/#7; movement stays synthetic, with separately labeled manual-1.0 WAIT |
| #10 combat | Weapon/item evidence, controlled attack traces, RNG/armor/range observations and combat routine cross-references | Blocked on #6–#9; no invented weapon/damage tables |
| #11 inventory | Original item/menu captures, pickup/drop/equip/use transitions, constraints, storage data and timing evidence | Blocked on #6/#7; no inferred item schema presented as historical |
| #12 AI/spawning | Controlled sensing/pathfinding/spawn/ally traces, entity data, turn-order and targeting evidence | Blocked on #8–#10; no fabricated original AI |
| #16 faithful Classic UI | Verified PICT catalog, screenshot dimensions/palettes/fonts, menu/shortcut observations and permitted asset attribution | Blocked on original #5/#6 evidence; demo skins are not an authentic Classic renderer |

## Definition of a usable research increment

Record source version/hash, reproducible actions, observed state, exact evidence
references and uncertainty. A deterministic native regression must correspond to
an observation, not an invented expected result. Compare original/port traces
under controlled inputs and label modernization options separately. See
REFERENCE_RESEARCH.md and 68K_ANALYSIS.md. These issues remain open until their
original-specific acceptance criteria can be exercised.

See [manual-backed research notes](MANUAL_EVIDENCE.md) for specific evidence and
the important manual-1.0 / executable-2.0.g mismatch. The blocker is no longer
absence of an archive; original execution traces and substantial semantic analysis
remain outstanding.
