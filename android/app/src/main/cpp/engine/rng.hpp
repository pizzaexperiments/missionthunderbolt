#pragma once
#include <cstdint>
namespace mt {
// Explicit, portable demo RNG; not an assertion about the original game.
class DemoRng {
public:
    explicit DemoRng(uint32_t seed) : state_(seed) {}
    uint32_t next() { state_ = state_ * 1664525u + 1013904223u; return state_; }
    uint32_t state() const { return state_; }
private:
    uint32_t state_;
};
}
