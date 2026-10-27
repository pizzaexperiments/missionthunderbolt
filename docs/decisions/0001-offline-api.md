# ADR 0001: retain the in-process C API; defer HTTP — issue #24

Status: accepted for this restoration workstream under the maintainer's closeout instruction, 2026-10-27. Issue #24 is closed; implementation is in
[draft PR #26](https://github.com/pizzaexperiments/missionthunderbolt/pull/26), which remains unmerged.

## Context and consumers

The portable engine already exposes a versioned C ABI. Android uses JNI, the
native desktop host links the same C++ state, and local tests/research tools use
files or direct function calls. There is no demonstrated deployed client that
requires a network game service. Offline single-player is an explicit project
goal; original game reconstruction does not require an HTTP backend.

Potential future uses include remote replay/test orchestration or an isolated
modding tool. Today deterministic traces and versioned save files can be passed
to a local harness without changing the game's runtime architecture.

## Decision

Keep simulation in-process and fully offline. Do not add a listener, account,
remote dependency, credentials or OpenAPI surface at this stage. Evolve the
versioned C ABI, ownership/error contract and file-based replay interfaces as
needed by actual local consumers. No HTTP implementation is approved by this ADR,
so an OpenAPI spec and server tests would describe an unneeded service.

## Consequences and revisit criteria

Builds, gameplay and saves remain available without network access. Tooling gets
one portable deterministic engine instead of a second service implementation.
Untrusted native plugins are not automatically safe merely because an ABI exists;
plugin isolation is a separate design question.

Revisit only for a concrete consumer with deployment, concurrency and security
requirements that the local ABI/files cannot meet. A future proposal must define
engine-session ownership, authentication/authorization, binding/exposure, input
limits, lifecycle, API versioning, replay determinism and a threat model, with
implementation/contract tests. Even then the native game must work offline.

## Offline implementation evidence

The accessibility-enabled debug APK was inspected with SDK 35 `aapt2 dump
permissions`: it lists the application package and no requested permissions,
including no INTERNET permission. Current Android/native sources contain no
HTTP client or listener. Emulator movement, WAIT, save restoration and lifecycle
checks passed with the in-process engine. This supports the current offline
prototype decision; full original gameplay remains a separate workstream.
