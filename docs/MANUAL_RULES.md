# Manual-backed prototype rules

The newly supplied 43-page reference PDF is kept privately under
`local-original/reference-manual/`. SHA256:
`a23265a09d414c51056a623b7c43bf2269d077cf63427a9424a1a0436aadf013`.
Its extracted text matches the earlier handoff manual exactly in this environment.
Both identify **version 1.0**; the executable resources identify **2.0.g**.
The user confirmed no original runtime/reference recordings are available.

These rules are documented/manual-backed. They are not presented as runtime-
corroborated 2.0.g behavior. Unknown formulas, AI and generation are not guessed.

## M1-WAIT — issue #9

Source: printed page **28** (PDF page 30), WAIT command; the keyboard table on
printed page 12 lists Space/keypad 5. The documented action remains in the current
location and consumes one time unit.

The prototype now has an explicit `PrototypeGame::wait()` and additive C ABI
`mt_game_wait()`. Android provides WAIT plus Space/keypad-5; SDL and the terminal
host accept Space (SDL also keypad-5). Invalid `move(0,0)` stays invalid and does
not become an implicit wait, preserving the existing movement API contract.

Tests check one increment, unchanged player position/map in the empty synthetic
world, presentation independence, isolated instances, save/load continuation,
null-handle errors and integer saturation. The saturation rule is a native safety
limit, not a claimed historical game limit. The actual C translation-unit test
also calls the new ABI function. SDL's queued-input/render/save smoke includes WAIT.
Android instrumentation checks the button, Space and a mode switch afterward.

The current world has no actors. Advancing its counter does not implement the
original scheduler, enemy actions, RNG consumption, status effects or FOV. Those
remain #8–#12 work and need separate evidence/tests. The API remains version 1
with an additive entry point and unchanged existing signatures.

## Next documented behavior to specify

The manual distinguishes time-consuming actions from information commands
(printed p.10), melee/wield/exchange (p.13), quantity/container interactions
(pp.13–14) and the original directional/running controls (pp.10–12).
MANUAL_EVIDENCE.md records those leads. Exact original algorithms and version
correspondence remain open; a manual citation is not a fabricated golden trace.
