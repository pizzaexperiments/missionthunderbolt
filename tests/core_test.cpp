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
    std::cout << "core smoke tests passed\n";
}
