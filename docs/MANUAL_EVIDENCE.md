# Manual-backed research notes — issues #6 and #8–#12

These are paraphrased documentation facts, **not executable traces or recovered
algorithms**. The supplied manual identifies version **1.0**. The supplied
application's two `vers` resources identify **2.0.g**. That mismatch must be
resolved before treating documentation as a specification of this binary.

Manual SHA256: `19711685c91c22d0c8bf5628ffb7a7ace6bf449786fbd79da57cf303885a9e69`.
Citations below use printed page numbers (PDF page index is two pages later).
The copyrighted manual and reference images stay in ignored local-original/.
No original gameplay was executed by the native-demo tests.

| Issue | Documentation evidence | What remains unknown |
| --- | --- | --- |
| #8 generation/progression | p.2 describes new-game topology/population variation; p.31 starts its tutorial in Region 1 | Generator, RNG, distributions, topology constraints, version differences, transitions and victory/defeat implementation |
| #9 movement/turns/FOV | p.10 distinguishes actions from free informational commands, assigns one time unit per step, and describes eight compass directions plus vertical travel; pp.10–12 distinguish running from rapid stepping and describe known-corner/path behavior | Scheduler ordering, blocked-move cost, exact visibility algorithm, corner-collision conditions, RNG and version-specific execution |
| #10 combat | p.13 documents moving into an occupied adjacent cell as melee, wielded-weapon/barehanded selection, a time cost for WIELD and a free EXCHANGE | Hit/damage/armor/range formulas, numeric weapon tables, RNG consumption, entity-death event ordering and original traces |
| #11 inventory | pp.13–14 describe quantity selection, ordering, wielded/reserved/worn status, per-retrieval time and container interaction; INSPECT is an action | Runtime data structures, stack limits, weight/item constraints, effect timing and controlled transition comparisons |
| #12 AI/spawning | The manual's tutorial/tips provide scenarios that can guide captures | No universal sensing/pathfinding/spawn/ally algorithm follows from an anecdotal scenario; controlled observations and code identification are needed |

The key map on p.12 uses the historical eight-direction letter/keypad scheme;
arrow keys are described separately as map scrolling on p.18. The demo's WASD/
arrow controls are modernization/prototype choices, **not** faithful historical
shortcut claims. A tutorial's single successful attack does not define a universal
damage result. No numbers, AI behaviors or combat/item mechanics were invented to
turn these research notes into passing but unsupported fidelity tests.

Next research steps: annotate jump-table-resolved routines/call candidates from
#7 with corroborating resource/trap/state evidence; obtain a lawful version-2.0.g
reference environment; capture known inputs; identify exact version differences;
then add native regression cases tied to those observations. Manual hypotheses
must retain their confidence labels until corroborated.


The user subsequently supplied a second PDF whose SHA256 is
`a23265a09d414c51056a623b7c43bf2269d077cf63427a9424a1a0436aadf013`.
It has the same extracted 43-page text, including the version 1.0 identification.
[Manual-backed prototype rules](MANUAL_RULES.md) records the first implemented
rule (M1-WAIT) with its page citation and explicit verification boundary.
