#ifndef MT_ENGINE_API_H
#define MT_ENGINE_API_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Versioned C API for research demo, NOT recovered game logic. */
#define MT_API_VERSION 1
typedef struct mt_game mt_game;
mt_game* mt_game_create(int width, int height, uint32_t seed);
void mt_game_destroy(mt_game* game);
int mt_game_move(mt_game* game, int dx, int dy);
int mt_game_turns(const mt_game* game);
/* Required bytes including NUL; if output is non-null, writes only if capacity suffices. */
int mt_game_map(const mt_game* game, char* output, int capacity);
void mt_game_set_modern(mt_game* game, int enabled);
int mt_game_is_modern(const mt_game* game);
int mt_api_version(void);
#ifdef __cplusplus
}
#endif
#endif
