#pragma once
#include "rng.hpp"
#include <stdexcept>
#include <string>
#include <vector>
namespace mt {
class DemoMap {
public:
    static constexpr int max_dimension = 512;
    DemoMap(int width, int height, uint32_t seed) : width_(width), height_(height), rng_(seed) {
        if (width < 5 || height < 5 || width > max_dimension || height > max_dimension)
            throw std::invalid_argument("map dimensions must be between 5 and 512");
        cells_.assign(static_cast<size_t>(height), std::string(static_cast<size_t>(width), '.'));
        for (int y = 0; y < height; ++y)
            for (int x = 0; x < width; ++x)
                if (x == 0 || y == 0 || x == width - 1 || y == height - 1) cells_[y][x] = '#';
        for (int i = 0; i < width * height / 30; ++i) {
            const int x = 2 + static_cast<int>(rng_.next() % static_cast<uint32_t>(width - 3));
            const int y = 2 + static_cast<int>(rng_.next() % static_cast<uint32_t>(height - 3));
            cells_[y][x] = '#';
        }
    }
    bool walkable(int x, int y) const {
        return x >= 0 && x < width_ && y >= 0 && y < height_ && cells_[y][x] != '#';
    }
    int width() const { return width_; }
    int height() const { return height_; }
    uint32_t rngState() const { return rng_.state(); }
    const std::vector<std::string>& cells() const { return cells_; }
private:
    int width_, height_;
    DemoRng rng_;
    std::vector<std::string> cells_;
};
}
