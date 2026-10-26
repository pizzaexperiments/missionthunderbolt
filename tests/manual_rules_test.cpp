// M1-WAIT: supplied manual version 1.0, printed p.28; executable 2.0.g unverified.
#include "game.hpp"
#include "api.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
int main() {
    mt::PrototypeGame game(20,12,1);
    const auto initialMap=game.asciiMap();const auto initialPlayer=game.player();
    assert(!game.move(0,0) && game.turns()==0); // Existing invalid-move contract stays intact.
    assert(game.wait());assert(game.turns()==1);
    assert(game.asciiMap()==initialMap && game.player().x==initialPlayer.x && game.player().y==initialPlayer.y);
    game.setPresentation(mt::Presentation::Modern);
    assert(game.wait() && game.turns()==2 && game.asciiMap()==initialMap);
    auto restored=mt::PrototypeGame::load(game.save());
    assert(restored.turns()==2 && restored.asciiMap()==initialMap);
    assert(restored.wait() && restored.turns()==3);
    assert(game.turns()==2); // Separate instances do not share time.
    auto saturated=mt::PrototypeGame::load("MTDEMO 0\n5 5 1 2147483647 1 1\n#####\n#...#\n#...#\n#...#\n#####\nCRC32 e2d9cc3f\n");
    const auto full=saturated.save();assert(!saturated.wait() && saturated.save()==full);
    assert(!mt_game_wait(nullptr) && mt_game_last_error()==MT_ERROR_INVALID_ARGUMENT);
    mt_game* handle=mt_game_create(20,12,1);assert(handle);
    const int size=mt_game_map(handle,nullptr,0);std::vector<char> before(static_cast<size_t>(size)),after(static_cast<size_t>(size));
    mt_game_map(handle,before.data(),size);assert(mt_game_wait(handle)==1 && mt_game_turns(handle)==1);
    mt_game_map(handle,after.data(),size);assert(before==after);
    mt_game_destroy(handle);
    std::cout<<"M1-WAIT: one time unit in place, mode independence and save continuation passed\n";
}
