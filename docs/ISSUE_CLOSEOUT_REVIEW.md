# Issue closeout review

## Current review — 2026-10-30

The 16 remaining live issue bodies and their available comments were refreshed
against integrated `develop` **`a24fc2c`**, including merged PR #58. **No further
issue is ready to close as completed.** The following are outstanding parts of
the written scope, not new requirements inferred from future project goals.
Unmerged work is excluded from this assessment.

| Issue | Specific remaining scope |
| --- | --- |
| [#1](https://github.com/pizzaexperiments/missionthunderbolt/issues/1) | Successful clean-checkout core/Android CI, CI `assembleDebug`, uploaded APK and linked successful run/artifact remain absent. Local builds do not fulfill those explicit checks; [Actions stays paused](../.github/ACTIONS_PAUSED.md). |
| [#6](https://github.com/pizzaexperiments/missionthunderbolt/issues/6) | Representative original play screenshots/video or reproducible written traces, observed controls/states and observation-linked tests remain unavailable. The [capture protocol](REFERENCE_RESEARCH.md) and manual are not recorded play. |
| [#7](https://github.com/pizzaexperiments/missionthunderbolt/issues/7) | [Ghidra imports, offsets and confidence-labeled call notes exist](68K_ANALYSIS.md), but CREL/resource-loader relocation semantics and runtime addressing remain unresolved. Completing combat/inventory/gameplay is not itself a prerequisite for this disassembly scope. |
| [#8](https://github.com/pizzaexperiments/missionthunderbolt/issues/8) | Original generator construction/population, topology and mission/level/win/lose progression still lack a complete evidence-linked specification and native regression coverage. [Recovered preparation/conversion stages](LEVEL_GRID_CONVERSION.md) do not complete generation/progression. |
| [#9](https://github.com/pizzaexperiments/missionthunderbolt/issues/9) | Original movement/collision/turn/FOV rules, boundary/diagonal/turn-cost cases and original-versus-port action traces remain incomplete. [Manual-backed WAIT](MANUAL_RULES.md) and coordinate helpers are narrower results. |
| [#10](https://github.com/pizzaexperiments/missionthunderbolt/issues/10) | Cited weapon/damage tables, implemented attack/damage events, deterministic combat/RNG tests and original golden traces remain missing; [manual evidence](MANUAL_EVIDENCE.md) alone does not fulfill them. |
| [#11](https://github.com/pizzaexperiments/missionthunderbolt/issues/11) | Inventory schemas, data-driven definitions, pickup/drop/equip/use tests and reference-validated transitions remain unfinished. [Child-record copy](CHILD_RECORD_COPY.md), factory and list routines retain raw-field names; they are not verified inventory behavior. |
| [#12](https://github.com/pizzaexperiments/missionthunderbolt/issues/12) | Entity behavior tables, deterministic AI/event logs, verified ally/enemy targeting/collision and original comparisons remain absent; see [gameplay evidence gaps](GAMEPLAY_EVIDENCE_GAPS.md). |
| [#13](https://github.com/pizzaexperiments/missionthunderbolt/issues/13) | Historical sequence/loop playback and representative auditory equivalence remain unverified. [Timing plans](SOUND_SEQUENCE.md) do not render audio; the [authored Android cue](NATIVE_AUDIO.md) proves output-stack consumption, not converted-original playback or audible hardware output. |
| [#15](https://github.com/pizzaexperiments/missionthunderbolt/issues/15) | The four synthetic save checklist checks pass, but the objective's entity, mission-progress and inventory state does not yet exist in the [save format](SAVE_FORMAT.md). Reading proprietary original saves is not an added requirement. |
| [#16](https://github.com/pizzaexperiments/missionthunderbolt/issues/16) | Original screenshot comparisons, faithful typography/layout, functional original menus and runtime resource attribution/fallback remain unverified. [Current skins](MODERN_CONTROLS.md) are synthetic. |
| [#18](https://github.com/pizzaexperiments/missionthunderbolt/issues/18) | All four written checklist items have evidence, but the objective still includes reliable current-API and ARM64-device execution. [API35 launch qualification failed](ANDROID_API35.md); API23's two passing 19-test runs and [performance baseline](ANDROID_PERFORMANCE.md) do not substitute for those checks. |
| [#19](https://github.com/pizzaexperiments/missionthunderbolt/issues/19) | Actual Windows x64 launch/play/input verification and a CI-produced downloadable portable package remain absent. [Linux SDL checks and Windows configuration](DESKTOP_DEVELOPMENT.md) are insufficient; demo gameplay is explicitly allowed. |
| [#20](https://github.com/pizzaexperiments/missionthunderbolt/issues/20) | Both native Mac architectures, launch/input/save and CI artifacts remain untested. [Packaging/signing/notarization plans](DESKTOP_DEVELOPMENT.md) exist; completed notarization is not an extra acceptance requirement. |
| [#22](https://github.com/pizzaexperiments/missionthunderbolt/issues/22) | Original-reference replay/screenshot/action-log and differential fixture scope remains incomplete. [Synthetic regressions, fuzzing, coverage and a defined ASan/UBSan job](QUALITY.md) exist. Scheduled fuzzing and a green hosted run are not additional written requirements for this issue. |
| [#23](https://github.com/pizzaexperiments/missionthunderbolt/issues/23) | End-to-end signed tagged-release preparation, desktop artifacts/inventories and complete dependency/license review remain unverified. [Unsigned artifact metadata, checksums and signing instructions](RELEASE_PREPARATION.md) exist; public release publication is not required for closeout. |

This review performed no new native/coverage runs, GitHub writes, issue closures,
Actions runs, merges or release publication. Earlier closures below remain
valid; this table supersedes their older remaining-work summaries.

## Historical access and closeout — 2026-10-27

Live GitHub access was verified on **2026-10-27** through the existing authenticated
API connection. A repository request returned HTTP 200 and issue/PR writes
succeeded. The earlier network-policy snapshot was stale; it no longer establishes
an API access blocker. No new credential was requested or copied into source.

The live issue bodies and comments were refreshed before closeout. Under the
maintainer's instruction to close completed issues, **#4, #24 and #25 were closed
with reason `completed`**, acceptance checklists and evidence comments. The work is
integrated through [PR #26](https://github.com/pizzaexperiments/missionthunderbolt/pull/26),
`feature/offline-research-tooling` → `develop`. Its merge was verified through the
live API after the maintainer reported it: commit
`a851a724e7d371d4e8307982b70202549502d50b`, 2026-10-27. Follow-up work uses the
same feature branch synchronized to that merged develop head.
No Actions run, tag or release publication was performed.

## Completed implementation scopes

| Issue | Acceptance evidence | Verified GitHub state |
| --- | --- | --- |
| [#4 — resource extraction](https://github.com/pizzaexperiments/missionthunderbolt/issues/4) | Deterministic file/fork/type/ID/size/SHA manifest; strict malformed-input rejection; synthetic tests; CODE/CREL semantics left explicit. Actual supplied replacement archive yielded 15 CODE/13 CREL. See [extraction](RESOURCE_EXTRACTION.md). The earlier unsupplied ZIP is not asserted byte-identical. | Closed as completed; [evidence comment](https://github.com/pizzaexperiments/missionthunderbolt/issues/4#issuecomment-6431089813). |
| [#24 — HTTP API decision](https://github.com/pizzaexperiments/missionthunderbolt/issues/24) | [ADR 0001](decisions/0001-offline-api.md) retains the offline C ABI and defers HTTP with consumer/security/revisit criteria. Conditional server/OpenAPI acceptance is not applicable. Offline prototype operation is verified; full original gameplay is separate. | Closed as completed; [evidence comment](https://github.com/pizzaexperiments/missionthunderbolt/issues/24#issuecomment-6431090491). |
| [#25 — execution playbook](https://github.com/pizzaexperiments/missionthunderbolt/issues/25) | Root [AGENTS.md](../AGENTS.md), [roadmap](ROADMAP.md), [local checks](LOCAL_TESTING.md) and evidence/PR definition of done cover each workstream while preserving prototype/fidelity boundaries. | Closed as completed; [evidence comment](https://github.com/pizzaexperiments/missionthunderbolt/issues/25#issuecomment-6431091117). |

The verified merge does not grant historical redistribution rights or establish
original-game fidelity or completion of other issues.

## Keep open

- #1 needs the requested CI artifact evidence; all Actions workflows stay disabled.
- #19/#20 need their actual native OS builds and requested CI artifacts.
- #2 was subsequently closed against its stated one-machine acceptance; see below.
- Historical redistribution permission remains unknown; the completed #3 workflow records that restriction.
- #6/#16 need original reference evidence and faithful runtime resource/layout mapping.
- #5 was subsequently closed against its decoder/catalog criteria; see below.
- #7–#12 have research progress, including instruction-corroborated RNG routines,
  but full state/relocation, map/progression, scheduling, combat, inventory and AI
  acceptance remains incomplete. Standalone routine checks are not game traces.
- #13 now has an opt-in authored Android PCM path; historical/timed-sequence
  rendering, auditory equivalence and physical-device output remain open.
- #15 covers current synthetic state and migration/corruption/storage tests; original
  entity/inventory/mission state does not yet exist and must not be called complete.
- #18 has an API 23 performance baseline; API 35 launch qualification and physical ARM64 remain unresolved. Physical accessibility/input testing remains a documented limitation of #17.
- #22 now has a bounded 1.72M-execution coverage-guided parser campaign; original
  differential and screenshot fixtures remain; scheduled campaigns are useful follow-up.
- #23 needs signing/review/dependency inventory and target platform artifacts.

#21 was also confirmed closed in the refreshed live issue list; it is tracked
as a duplicate of #1. The follow-up reviews below supersede earlier closure assessments. Recheck live acceptance
and comments before subsequent closures.

## Follow-up closeout — Android development instructions

PR #27 was verified merged as `f693dfd511ea5e7d18653a92f4dc9ab426626c3d`
on 2026-10-27. The feature branch was fast-forwarded to that develop head.
Issue [#2](https://github.com/pizzaexperiments/missionthunderbolt/issues/2) was
closed as completed after refreshing its live acceptance and comments. Its four
criteria require one verified clean-clone host, documented install/launch, no
user-specific paths/secrets, and versions matching CI. The remote clean-clone
Linux build in [build evidence](verification/android-build.md), portable
[setup guide](ANDROID_DEVELOPMENT.md), and recorded API 23 install/launch fulfill
that scope. Download caches were reused. Windows/macOS execution and physical
device breadth were previously treated as extra blockers for #2; those belong
to #18–#20 and do not change its one-machine requirement.

[Closeout evidence](https://github.com/pizzaexperiments/missionthunderbolt/issues/2#issuecomment-6431707124).
No CI run, merge, tag, production signing or release publication was performed
by this increment.

## Follow-up closeout — PICT decoder/catalog

Issue [#5](https://github.com/pizzaexperiments/missionthunderbolt/issues/5) was
closed as completed after checking its live criteria and corroborating the
previously disputed original picture through GraphicsMagick.
[PR #29](https://github.com/pizzaexperiments/missionthunderbolt/pull/29) contains
the comparison adapter, authored indexed-row-padding regression and detailed
[graphics evidence](PICT_CATALOG.md). Every supplied picture (934 total) matches
at least one external decoder. GraphicsMagick's 100 resource failures remain
visible; original-runtime verification is not inferred from decoder agreement.
Four panel roles have direct visual attribution, while other sprites retain
neutral resource-ID names. The five stated decoder/catalog criteria are met;
faithful runtime screenshots, menu interaction and exhaustive role mapping remain
#16 work. Historical redistribution permission remains unresolved under the policy recorded by #3.

[Closeout evidence](https://github.com/pizzaexperiments/missionthunderbolt/issues/5#issuecomment-6431905666).
The live API confirmed `closed` with reason `completed`. This does not claim
that PR #29 is merged or that the original game has been booted.

## Follow-up review — provenance, portable core and modern controls

On 2026-10-30, live issues and all merged implementation through PR #48 were
reviewed against their written objectives and acceptance criteria. Three scopes
were closed as completed with live evidence comments, without treating unrelated future fidelity work as a new
acceptance requirement:

- **#3:** [rights and provenance](RIGHTS_AND_PROVENANCE.md) records confirmed/unknown
  rights, private import/index guards and a synthetic-only distribution decision.
  Unknown historical rights remain unknown; closure does not authorize publication.
- **#14:** the portable CMake library, seeded deterministic core, Android-independent
  modules and [documented C ABI](API.md) satisfy the prototype refactor scope.
  Native Windows/macOS execution remains unverified under #19/#20. The criterion
  says CI on those hosts “where available”; Actions remains disabled.
- **#17:** shared-state synthetic skins, labeled 48 dp controls, measured 1.3× font
  scaling, keyboard/joystick coverage and emulator instrumentation satisfy its
  controls checks. See [controls](MODERN_CONTROLS.md) and [runtime evidence](ANDROID_RUNTIME.md).
  Faithful Classic rendering remains #16; physical TalkBack/gamepad usability
  and broader device coverage remain unverified.

#15 remains open: its current synthetic save checks pass, but the objective also
requires entity, mission-progress and inventory state that does not yet exist.
#1 still explicitly requires CI artifacts; pausing Actions does not fulfill it.
#6–#13, #16, #18–#20, #22 and #23 retain specific unfinished acceptance in the
[roadmap](ROADMAP.md). No merge, Actions run or release is authorized by this review.

A separate source-history audit examined 103 commits and 529 blobs across public
branches and advertised PR heads. It found no matching credential patterns,
original binary/resource hashes or raw disassembly dumps. This bounded scan
does not prove legal clearance or inspect the five historical APK Actions artifacts.
