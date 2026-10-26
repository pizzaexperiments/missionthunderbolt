#include "game.hpp"
#include "api.h"
#include <cassert>
#include <iostream>
#include <vector>
int main() {
    mt::PrototypeGame first(20,12,42);
    first.move(1,0); first.setPresentation(mt::Presentation::Modern);
    const auto saved=first.save(); auto restored=mt::PrototypeGame::load(saved);
    assert(restored.save()==saved);
    for (int i=0;i<20;++i) {
        assert(first.move(0,1)==restored.move(0,1));
        assert(first.save()==restored.save());
    }
    for (size_t i : {size_t(0),saved.size()/2,saved.size()-2}) {
        auto corrupt=saved;corrupt[i]^=1;bool rejected=false;
        try { (void)mt::PrototypeGame::load(corrupt); } catch(const std::invalid_argument&) { rejected=true; }
        assert(rejected);
    }
    mt_game* game=mt_game_create(20,12,1); assert(game);
    const int size=mt_game_save(game,nullptr,0);std::vector<char> buf(static_cast<size_t>(size));
    assert(mt_game_save(game,buf.data(),size)==size);
    const auto before=std::string(buf.data());
    assert(!mt_game_load(game,"bad",3));
    assert(mt_game_last_error()==MT_ERROR_INVALID_ARGUMENT);
    assert(mt_game_save(game,buf.data(),size)==size && before==buf.data());
    assert(mt_game_load(game,saved.data(),static_cast<int>(saved.size())));
    assert(mt_game_turns(game)==1 && mt_game_is_modern(game)==1);
    mt_game_destroy(game);
    const std::string legacy="MTDEMO 0\n5 5 1 0 1 1\n#####\n#...#\n#...#\n#...#\n#####\nCRC32 fd0960e5\n";
    auto migrated=mt::PrototypeGame::load(legacy);
    assert(migrated.width()==5 && migrated.turns()==0 && migrated.seed()==1);
    assert(migrated.save().find("MTDEMO 1\n")==0);
    { bool rejected=false; try { (void)mt::PrototypeGame::load("MTDEMO 9\n5 5 1 0 1 1\n#####\n#...#\n#...#\n#...#\n#####\nCRC32 5d119dd6\n"); } catch(const std::invalid_argument&) { rejected=true; } assert(rejected); }
    { bool rejected=false; try { (void)mt::PrototypeGame::load("MTDEMO 0\n5 5 1 0 0 0\n#####\n#...#\n#...#\n#...#\n#####\nCRC32 28513479\n"); } catch(const std::invalid_argument&) { rejected=true; } assert(rejected); }
    { bool rejected=false; try { (void)mt::PrototypeGame::load("MTDEMO 0\n5 5 1 0 1 1\n#####\n#.X.#\n#...#\n#...#\n#####\nCRC32 64dec120\n"); } catch(const std::invalid_argument&) { rejected=true; } assert(rejected); }

    std::cout << "save/load round-trip, continuation and corruption checks passed\n";
}
