# Issue closeout review

Live GitHub access was verified on **2026-10-27** through the existing authenticated
API connection. A repository request returned HTTP 200 and issue/PR writes
succeeded. The earlier network-policy snapshot was stale; it no longer establishes
an API access blocker. No new credential was requested or copied into source.

The live issue bodies and comments were refreshed before closeout. Under the
maintainer's instruction to close completed issues, **#4, #24 and #25 were closed
with reason `completed`**, acceptance checklists and evidence comments. The work is
available in [draft PR #26](https://github.com/pizzaexperiments/missionthunderbolt/pull/26),
`feature/offline-research-tooling` → `develop`. The PR remains **unmerged**.
No Actions run, tag or release publication was performed.

## Completed implementation scopes

| Issue | Acceptance evidence | Verified GitHub state |
| --- | --- | --- |
| [#4 — resource extraction](https://github.com/pizzaexperiments/missionthunderbolt/issues/4) | Deterministic file/fork/type/ID/size/SHA manifest; strict malformed-input rejection; synthetic tests; CODE/CREL semantics left explicit. Actual supplied replacement archive yielded 15 CODE/13 CREL. See [extraction](RESOURCE_EXTRACTION.md). The earlier unsupplied ZIP is not asserted byte-identical. | Closed as completed; [evidence comment](https://github.com/pizzaexperiments/missionthunderbolt/issues/4#issuecomment-6431089813). |
| [#24 — HTTP API decision](https://github.com/pizzaexperiments/missionthunderbolt/issues/24) | [ADR 0001](decisions/0001-offline-api.md) retains the offline C ABI and defers HTTP with consumer/security/revisit criteria. Conditional server/OpenAPI acceptance is not applicable. Offline prototype operation is verified; full original gameplay is separate. | Closed as completed; [evidence comment](https://github.com/pizzaexperiments/missionthunderbolt/issues/24#issuecomment-6431090491). |
| [#25 — execution playbook](https://github.com/pizzaexperiments/missionthunderbolt/issues/25) | Root [AGENTS.md](../AGENTS.md), [roadmap](ROADMAP.md), [local checks](LOCAL_TESTING.md) and evidence/PR definition of done cover each workstream while preserving prototype/fidelity boundaries. | Closed as completed; [evidence comment](https://github.com/pizzaexperiments/missionthunderbolt/issues/25#issuecomment-6431091117). |

Closing these implementation issues does not claim PR approval/merge, historical
redistribution rights, original-game fidelity or completion of other issues.

## Keep open

- #1 needs the requested CI artifact evidence; Actions stays manual-only.
- #2 and #14 need native platform verification; #19/#20 need their actual OS builds.
- #3 still lacks historical redistribution permission.
- #5/#6/#16 need original reference evidence and faithful resource/layout mapping.
- #7–#12 have research progress, including instruction-corroborated RNG routines,
  but full state/relocation, map/progression, scheduling, combat, inventory and AI
  acceptance remains incomplete. Standalone routine checks are not game traces.
- #13 lacks complete timed-sequence rendering, native audio and auditory/device proof.
- #15 covers current synthetic state and migration/corruption/storage tests; original
  entity/inventory/mission state does not yet exist and must not be called complete.
- #17/#18 need physical accessibility/input and broader lifecycle/performance evidence.
- #22 now has a bounded 1.72M-execution coverage-guided parser campaign; original
  differential fixtures and longer-running/scheduled campaigns remain.
- #23 needs signing/review/dependency inventory and target platform artifacts.

#21 was also confirmed closed in the refreshed live issue list; it is tracked
as a duplicate of #1. All other issues above remain open. Recheck live acceptance
and comments before subsequent closures.
