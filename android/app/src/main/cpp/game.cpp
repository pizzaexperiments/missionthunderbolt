#include "game.hpp"
#include <stdexcept>
namespace mt {
PrototypeGame::PrototypeGame(int w, int h, uint32_t seed) : width_(w), height_(h) {
    if (w < 5 || h < 5) throw std::invalid_argument("map too small");
    grid_.assign(h, std::string(w, '.'));
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x)
            if (x == 0 || y == 0 || x == w - 1 || y == h - 1) grid_[y][x] = '#';
    // Deterministic DEMO obstacles, not recovered Mission Thunderbolt rules.
    for (int i = 0; i < w * h / 30; ++i) {
        seed = seed * 1664525u + 1013904223u;
        int x = 2 + static_cast<int>(seed % static_cast<uint32_t>(w - 3));
        seed = seed * 1664525u + 1013904223u;
        int y = 2 + static_cast<int>(seed % static_cast<uint32_t>(h - 3));
        grid_[y][x] = '#';
    }
}
bool PrototypeGame::move(int dx, int dy) {
    if (dx < -1 || dx > 1 || dy < -1 || dy > 1 || (dx == 0 && dy == 0)) return false;
    int x = player_.x + dx, y = player_.y + dy;
    if (x < 0 || x >= width_ || y < 0 || y >= height_ || grid_[y][x] == '#') return false;
    player_ = {x, y};
    ++turns_;
    return true;
}
std::string PrototypeGame::asciiMap() const {
    auto g = grid_;
    g[player_.y][player_.x] = '@';
    std::string out;
    for (const auto& line : g) {
        out += line;
        out += '\n';
    }
    return out;
}
}
