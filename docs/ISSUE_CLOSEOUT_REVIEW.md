# Issue closeout review

This review uses the saved issue descriptions from this workstream, not a fresh
GitHub issue query. The current session exposes no GitHub connector, and the
configured network destinations exclude `api.github.com`. HTTPS Git pushes work;
issue edits/closures and PR creation have not been performed. No issue is closed
by this document. The user authorized closing issues whose criteria are met.
Root AGENTS.md still requires reviewable feature-to-develop PRs and approval to
merge; no merge or automatic Actions run is authorized here.

## Candidates with implementation evidence ready for review

| Issue | Acceptance evidence | Remaining closeout step |
| --- | --- | --- |
| #4 — resource extraction | Deterministic file/fork/type/ID/size/SHA manifest; strict malformed-input rejection; synthetic tests; CODE/CREL semantics left explicit. Actual supplied archive yielded 15 CODE/13 CREL. See [extraction](RESOURCE_EXTRACTION.md). | Review the feature PR and record closure through GitHub. The user-supplied replacement archive was used; the unsupplied earlier ZIP is not asserted byte-identical. |
| #24 — HTTP API decision | [ADR 0001](decisions/0001-offline-api.md) documents current/future consumers, security/offline implications and the decision to retain the C ABI. An HTTP implementation was not selected, so conditional OpenAPI/server acceptance does not apply. Local native/Android checks exercise offline operation. | Maintainer review of the decision in the feature PR; then record the decision and close the issue through GitHub. |
| #25 — execution playbook | Root [AGENTS.md](../AGENTS.md), [roadmap](ROADMAP.md), [local checks](LOCAL_TESTING.md) and evidence/PR definition of done exist. The roadmap links every workstream and distinguishes synthetic demos, original inputs and runtime claims. | Review the documentation in the feature PR, then close through GitHub. |

These are review candidates, not statements that review occurred. A concrete PR
body is prepared locally under ignored `dist/review/PR_DESCRIPTION.md`.

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

#21 was already recorded closed as a duplicate of #1 in the saved issue snapshot.
Refresh issue state through an authorized GitHub connection before applying any
closure, so changed requirements, comments or existing closures are respected.
