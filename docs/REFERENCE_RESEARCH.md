# Reference capture and evidence — issue #6

Status: tooling/protocol prepared; **no original-game capture has been made**.
Neither the historical application/archive nor a licensed reference machine/ROM
has been supplied to this task. An Android synthetic-demo emulator is not an
original-game reference. Do not derive historical rules from its behavior.

## Capture protocol

1. Record acquisition/provenance locally, input SHA256, exact game version,
   reference OS, emulator/hardware version, ROM provenance if applicable and clock.
   Use a lawfully supplied reference environment; do not ship it with the port.
2. Start from a reproducible state (new game, known save or recorded input).
   Capture the initial screen, menus, preferences, controls and help.
3. Record one action at a time with before/after state, timing and screen/video
   reference. Separate observed movement, blocked movement, diagonals, waiting,
   turns, inventory, combat, saves, transitions, victory and defeat. Repeat with
   controlled input; mark nondeterministic/unknown seed conditions explicitly.
4. Link each claimed rule to exact capture filenames/timestamps or annotated
   code references. Compare version differences independently. Unobserved behavior
   is `unknown`; plausible explanations remain `hypothesis` until corroborated.
5. Keep inputs/captures under ignored `local-original/` / `local-generated/`.
   Review rights before sharing screenshots, videos, manuals or derivatives.

## Local trace interchange

Write JSON with `schema: 1`, nonempty `run_id`, `game_version`, `environment`,
`source_sha256` (64 lowercase hex digits), and a nonempty `events` list. Each event
has `step` (contiguous from 0), `action`, `state` (observed fields only),
`confidence` (`observed`, `hypothesis`, `unknown`) and `evidence` (reference strings).
Observed events must have evidence; the validator cannot establish its truth.

```sh
python3 scripts/check_reference_trace.py local-generated/reference/run.json
```

No original trace fixture is invented for public tests. Synthetic schema tests
verify the interchange constraints only. Original-vs-port differential tests
must wait for original observations with known inputs and comparable state.
