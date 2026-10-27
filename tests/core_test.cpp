#include "../android/app/src/main/cpp/game.hpp"
#include <cassert>
#include <iostream>
int main() {
    mt::PrototypeGame game(20, 12, 1);
    assert(game.turns() == 0);
    assert(game.player().x == 1 && game.player().y == 1);
    assert(!game.move(-1, 0));
    assert(!game.move(0, 0));
    assert(!game.move(2, 0));
    assert(game.turns() == 0);
    assert(game.move(1, 0));
    assert(game.turns() == 1);
    assert(game.player().x == 2);
    assert(game.asciiMap().find('@') != std::string::npos);
    game.setPresentation(mt::Presentation::Modern);
    assert(game.presentation() == mt::Presentation::Modern);
    mt::PrototypeGame replay(20, 12, 1);
    assert(replay.asciiMap() != game.asciiMap());
    for (uint32_t seed : {0u, 1u, 42u, 0xffffffffu}) {
        mt::PrototypeGame first(20, 12, seed), second(20, 12, seed);
        assert(first.asciiMap() == second.asciiMap());
        assert(first.rngState() == second.rngState());
        const auto before = first.asciiMap();
        first.setPresentation(mt::Presentation::Modern);
        assert(first.asciiMap() == before && first.turns() == 0);
        for (int i=0; i<10; ++i) {
            assert(first.move(1,0) == second.move(1,0));
            assert(first.asciiMap() == second.asciiMap());
        }
    }
    std::cout << "core smoke tests passed\n";
}
