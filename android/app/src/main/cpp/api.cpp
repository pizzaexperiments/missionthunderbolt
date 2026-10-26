#include "api.h"
#include "game.hpp"
#include <cstring>
#include <new>
#include <stdexcept>
struct mt_game { mt::PrototypeGame instance; mt_game(int w,int h,uint32_t seed):instance(w,h,seed){} };
namespace {
thread_local int last_error = MT_ERROR_NONE;
template<typename F, typename R> R protect(F fn, R failure) noexcept {
    last_error = MT_ERROR_NONE;
    try { return fn(); }
    catch (const std::invalid_argument&) { last_error = MT_ERROR_INVALID_ARGUMENT; }
    catch (const std::bad_alloc&) { last_error = MT_ERROR_OUT_OF_MEMORY; }
    catch (...) { last_error = MT_ERROR_INTERNAL; }
    return failure;
}
void require(const mt_game* game) { if (!game) throw std::invalid_argument("null game"); }
}
extern "C" {
mt_game* mt_game_create(int w,int h,uint32_t seed) {
    return protect([&] { return new mt_game(w,h,seed); }, static_cast<mt_game*>(nullptr));
}
void mt_game_destroy(mt_game* game) { delete game; last_error=MT_ERROR_NONE; }
int mt_game_move(mt_game* game,int dx,int dy) {
    return protect([&] { require(game); return game->instance.move(dx,dy) ? 1 : 0; },0);
}
int mt_game_wait(mt_game* game) {
    return protect([&] { require(game); return game->instance.wait() ? 1 : 0; },0);
}
int mt_game_turns(const mt_game* game) {
    return protect([&] { require(game); return game->instance.turns(); },-1);
}
int mt_game_map(const mt_game* game,char* output,int capacity) {
    return protect([&] {
        require(game);
        if (capacity<0) throw std::invalid_argument("negative capacity");
        const auto map=game->instance.asciiMap();
        const int required=static_cast<int>(map.size()+1);
        if (output && capacity>=required) std::memcpy(output,map.c_str(),static_cast<size_t>(required));
        else if (output) last_error=MT_ERROR_BUFFER_TOO_SMALL;
        return required;
    },0);
}
void mt_game_set_modern(mt_game* game,int enabled) {
    protect([&] { require(game); game->instance.setPresentation(enabled?mt::Presentation::Modern:mt::Presentation::Classic); return 0; },0);
}
int mt_game_is_modern(const mt_game* game) {
    return protect([&] { require(game); return game->instance.presentation()==mt::Presentation::Modern ? 1 : 0; },0);
}
int mt_game_save(const mt_game* game,char* output,int capacity) {
    return protect([&] {
        require(game);
        if (capacity<0) throw std::invalid_argument("negative capacity");
        const auto saved=game->instance.save(); const int required=static_cast<int>(saved.size()+1);
        if (output && capacity>=required) std::memcpy(output,saved.c_str(),static_cast<size_t>(required));
        else if (output) last_error=MT_ERROR_BUFFER_TOO_SMALL;
        return required;
    },0);
}
int mt_game_load(mt_game* game,const char* input,int length) {
    return protect([&] {
        require(game);
        if (!input || length<=0 || length>1024*1024) throw std::invalid_argument("invalid save input");
        auto restored=mt::PrototypeGame::load(std::string(input,static_cast<size_t>(length)));
        game->instance=std::move(restored); return 1;
    },0);
}
int mt_api_version(void) { return MT_API_VERSION; }
int mt_game_last_error(void) { return last_error; }
const char* mt_error_message(int error) {
    switch(error) {
    case MT_ERROR_NONE: return "no error";
    case MT_ERROR_INVALID_ARGUMENT: return "invalid argument";
    case MT_ERROR_OUT_OF_MEMORY: return "out of memory";
    case MT_ERROR_BUFFER_TOO_SMALL: return "buffer too small";
    default: return "internal error";
    }
}
}
