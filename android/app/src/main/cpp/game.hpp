#pragma once
#include "engine/map.hpp"
#include <cstdint>
#include <string>
namespace mt {
enum class Presentation { Classic, Modern };
struct Position { int x = 0, y = 0; };
class PrototypeGame {
public:
    PrototypeGame(int width = 20, int height = 12, uint32_t seed = 1);
    bool move(int dx, int dy);
    void setPresentation(Presentation p) { presentation_ = p; }
    Presentation presentation() const { return presentation_; }
    Position player() const { return player_; }
    int turns() const { return turns_; }
    int width() const { return map_.width(); }
    int height() const { return map_.height(); }
    uint32_t seed() const { return seed_; }
    uint32_t rngState() const { return map_.rngState(); }
    std::string asciiMap() const;
private:
    DemoMap map_;
    uint32_t seed_;
    int turns_ = 0;
    Position player_{1, 1};
    Presentation presentation_ = Presentation::Classic;
};
}
