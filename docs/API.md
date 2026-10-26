# Portable engine C API (research demonstration)

Header: `android/app/src/main/cpp/api.h`. ABI version: `mt_api_version() == 1`.

- `mt_game_create(width,height,seed)` returns an opaque owned instance or NULL on failure.
- `mt_game_move(game,dx,dy)` returns 1 on successful movement, else 0.
- `mt_game_turns(game)` returns the turn count, -1 for invalid instance.
- `mt_game_map(game,output,capacity)` returns required buffer bytes including NUL; pass NULL and 0 to query size. Buffer is written only when capacity is sufficient.
- `mt_game_set_modern` and `mt_game_is_modern` expose presentation mode.
- `mt_game_destroy` releases an instance.

**Important:** these functions model a tiny synthetic prototype, not authentic Mission Thunderbolt mechanics. This is an in-process library API (not an HTTP service). No Macintosh emulator is involved.
