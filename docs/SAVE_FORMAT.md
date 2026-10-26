# Portable demo save format — issue #15

This format stores the **synthetic demo**, not historical Mission Thunderbolt
save files. It currently has no inventory, enemies or recovered mission state.
Do not silently fabricate absent fields as if those systems were implemented.

Version 1 is UTF-8/ASCII text: `MTDEMO 1`, then width/height, initial seed, current
portable RNG state, turn count, player position and presentation flag; complete
map rows; and an eight-hex-digit CRC32 of the preceding bytes. Saving the grid
avoids depending on future map-generation code to recover a player's world.
Limits (1 MiB input, 5–512 dimensions), cell/boundary validation, player collision,
unsigned seed/RNG range, nonnegative turns and supported version are checked.
CRC32 detects accidental corruption, not malicious tampering or authenticity.

`PrototypeGame::load` constructs and validates a candidate before replacement.
The C ABI adds `mt_game_save` (same required-capacity contract as map output) and
`mt_game_load` (explicit byte count excluding NUL, returns 1 on success). An invalid
load returns 0, sets an error and leaves current state unchanged. ABI version 1
and existing ownership conventions remain intact.

Version 0 is a deliberately synthetic migration fixture: it lacks RNG/presentation
fields, derives the initial RNG from the saved seed/dimensions and defaults to
Classic presentation. It was not a released historical format. Loading then
saving upgrades to version 1. Unknown versions fail rather than being guessed.
Future state extensions require versioned migration tests and a documented policy;
there is no promise to read proprietary original saves.

Android restores from saved-instance state or app-private `demo-state.mt`, using
`AtomicFile` for crash-safe replacement and bounded reads. State is saved on
pause; corrupt data is ignored with a warning and does not overwrite live state.
Mode, player, turns, map and RNG round-trip. No public/shared storage permission
is needed. Android's atomic helper manages backup/rollback; core serialization
itself performs no filesystem writes.

Validation: native round-trip, continued deterministic actions, independent CRC32
legacy/semantic-invalid fixtures, corrupted bytes and atomic failed C-API load
passed; Android APK rebuilt successfully. Runtime rotation/process-death checks
are tracked under #18 and remain distinct from compilation.
