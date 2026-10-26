#include "game.hpp"
#include <limits>
namespace mt {
PrototypeGame::PrototypeGame(int w, int h, uint32_t seed) : map_(w, h, seed), seed_(seed) {}
bool PrototypeGame::move(int dx, int dy) {
    if (dx < -1 || dx > 1 || dy < -1 || dy > 1 || (dx == 0 && dy == 0)) return false;
    if (turns_ == std::numeric_limits<int>::max()) return false;
    const int x = player_.x + dx, y = player_.y + dy;
    if (!map_.walkable(x, y)) return false;
    player_ = {x, y};
    ++turns_;
    return true;
}
std::string PrototypeGame::asciiMap() const {
    auto grid = map_.cells();
    grid[player_.y][player_.x] = '@';
    std::string out;
    out.reserve(static_cast<size_t>((width()+1)*height()));
    for (const auto& line : grid) { out += line; out += '\n'; }
    return out;
}
}
