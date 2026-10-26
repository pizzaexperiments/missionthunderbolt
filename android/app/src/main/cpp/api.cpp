#include "api.h"
#include "game.hpp"
#include <cstring>
#include <exception>
struct mt_game { mt::PrototypeGame instance; mt_game(int w,int h,uint32_t seed):instance(w,h,seed){} };
extern "C" {
mt_game* mt_game_create(int width,int height,uint32_t seed) {
    try { return new mt_game(width,height,seed); }
    catch (const std::exception&) { return nullptr; }
    catch (...) { return nullptr; }
}
void mt_game_destroy(mt_game* game) { delete game; }
int mt_game_move(mt_game* game,int dx,int dy) {
    return game && game->instance.move(dx,dy) ? 1 : 0;
}
int mt_game_turns(const mt_game* game) { return game ? game->instance.turns() : -1; }
int mt_game_map(const mt_game* game,char* output,int capacity) {
    if(!game || capacity<0) return 0;
    const auto map=game->instance.asciiMap();
    const int required=static_cast<int>(map.size()+1);
    if(output && capacity>=required) std::memcpy(output,map.c_str(),static_cast<size_t>(required));
    return required;
}
void mt_game_set_modern(mt_game* game,int enabled) {
    if(game) game->instance.setPresentation(enabled?mt::Presentation::Modern:mt::Presentation::Classic);
}
int mt_game_is_modern(const mt_game* game) {
    return game && game->instance.presentation()==mt::Presentation::Modern ? 1 : 0;
}
int mt_api_version(void) { return MT_API_VERSION; }
}
