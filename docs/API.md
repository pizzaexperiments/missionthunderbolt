# Portable engine C API (research demonstration)

Header: `android/app/src/main/cpp/api.h`. ABI version: `mt_api_version() == 1`.

- `mt_game_create(width,height,seed)` returns an opaque owned instance or NULL on failure.
- `mt_game_move(game,dx,dy)` returns 1 on successful movement, else 0.
- `mt_game_turns(game)` returns the turn count, -1 for invalid instance.
- `mt_game_map(game,output,capacity)` returns required buffer bytes including NUL; pass NULL and 0 to query size. Buffer is written only when capacity is sufficient.
- `mt_game_set_modern` and `mt_game_is_modern` expose presentation mode.
- `mt_game_destroy` releases an instance.

**Important:** these functions model a tiny synthetic prototype, not authentic Mission Thunderbolt mechanics. This is an in-process library API (not an HTTP service). No Macintosh emulator is involved.

## Portable core and error contract (#14)

The existing ABI version remains 1; additions preserve the existing function
signatures. `mt_game_last_error()` returns a per-thread enum for the most recent
game operation; `mt_error_message(code)` returns a static string that callers
must not free. Invalid arguments, allocation failure, insufficient buffers and
internal exceptions are distinguished. Blocked demo movement is a normal result,
not an error. No C++ exception crosses the C boundary. Null destruction is safe.
All game instances are caller-owned and require `mt_game_destroy`; callers must
serialize concurrent access to an individual instance. Error state is thread-local.
The buffer sizing call allocates no caller buffer: a NULL output queries bytes;
a short non-NULL buffer is left unchanged and the required length is returned.

Demo map dimensions are bounded to 5–512 per axis, preventing unbounded allocation
and signed multiplication overflow. The map and explicitly seeded portable demo
RNG are separate modules with no Android includes. Items, AI and original game
rules are not fabricated merely to populate the architecture.

```sh
cmake -S . -B dist/cmake -DCMAKE_BUILD_TYPE=Debug
cmake --build dist/cmake --parallel 4
ctest --test-dir dist/cmake --output-on-failure
```

Linux CMake, core/API tests and a real C translation-unit ABI test passed locally.
A manual-only Windows/macOS/Linux matrix is provided; remote platform runs remain
unexecuted. The Android JNI shared library continues to compile the portable
sources alongside its host bridge.


`mt_game_wait(game)` is an additive version-1 entry point: returns 1 when one
prototype time unit was consumed in place, 0 for a null handle or saturated
counter. Null sets INVALID_ARGUMENT; saturation is a normal rejected action.
It implements the manual-1.0 WAIT model documented in MANUAL_RULES.md, without
claiming original 2.0.g scheduler/RNG/actor behavior.

## Playable research mission additions

`mt_game_create_research(seed)` creates an owned 67×19 authored mission using
recovered RNG, conversion and record routines. `mt_game_is_research(game)` reports
the mode. `mt_game_pickup(game)` returns 1 only when a floor sample is collected
at the player's location; a rejected action returns 0 without advancing turns.
`mt_game_inventory_count(game)` returns 0 or 1, or -1 for a null handle.
The same error/ownership and serialization contracts apply. ABI version stays 1;
`mt_game_create` retains the legacy demo. See [integration scope and saves](PLAYABLE_RESEARCH_MISSION.md).
