#ifndef MT_ENGINE_API_H
#define MT_ENGINE_API_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Versioned C API for research demo, NOT recovered game logic. */
#define MT_API_VERSION 1
typedef struct mt_game mt_game;
enum mt_error {
    MT_ERROR_NONE = 0,
    MT_ERROR_INVALID_ARGUMENT = 1,
    MT_ERROR_OUT_OF_MEMORY = 2,
    MT_ERROR_BUFFER_TOO_SMALL = 3,
    MT_ERROR_INTERNAL = 4
};
/* Per-thread last operation error; message strings are static and not owned. */
int mt_game_last_error(void);
const char* mt_error_message(int error);
mt_game* mt_game_create(int width, int height, uint32_t seed);
void mt_game_destroy(mt_game* game);
int mt_game_move(mt_game* game, int dx, int dy);
/* Explicit one-time-unit wait, not a zero-displacement move. */
int mt_game_wait(mt_game* game);
int mt_game_turns(const mt_game* game);
/* Required bytes including NUL; if output is non-null, writes only if capacity suffices. */
int mt_game_map(const mt_game* game, char* output, int capacity);
void mt_game_set_modern(mt_game* game, int enabled);
int mt_game_is_modern(const mt_game* game);
/* Versioned synthetic save text, same buffer contract as mt_game_map. */
int mt_game_save(const mt_game* game, char* output, int capacity);
/* Atomic in-memory replacement: invalid data leaves the game unchanged. */
int mt_game_load(mt_game* game, const char* input, int length);
int mt_api_version(void);
#ifdef __cplusplus
}
#endif
#endif
