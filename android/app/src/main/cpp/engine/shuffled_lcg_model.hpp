#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
namespace mt {
// Instruction-corroborated research model, not a claim about original initialization/gameplay.
class ShuffledLcgModel {
public:
    struct State {
        uint32_t local_seed=0, selector_seed=0, last_result=0;
        std::array<uint32_t,100> table{};
    };
    explicit ShuffledLcgModel(State state) : state_(state) {
        for (uint32_t value : state_.table)
            if (value>32767u) throw std::invalid_argument("model requires a 15-bit shuffle table");
    }
    // The original initializer takes a 32-bit argument but seeds the selector
    // from its low word; a zero argument reads the supplied fallback word.
    // The existing stored result survives initialization.
    static ShuffledLcgModel initialized(uint32_t argument, uint16_t fallback,
                                        uint32_t previous_result=0) {
        State initial;
        initial.local_seed=1;
        initial.selector_seed=argument ? (argument & 65535u) : fallback;
        initial.last_result=previous_result;
        for (auto& value : initial.table) value=advance(initial.local_seed);
        return ShuffledLcgModel(initial);
    }
    const State& state() const { return state_; }
    uint32_t zeroBased(int bound) { return draw(bound,false); }
    uint32_t oneBased(int bound) { return draw(bound,true); }
private:
    static uint32_t advance(uint32_t& seed) {
        seed=seed*1103515245u+12345u;
        return (seed>>16)&32767u;
    }
    uint32_t draw(int bound,bool one_based) {
        if (bound < -32768 || bound > 32767) throw std::invalid_argument("bound must fit signed 16-bit input");
        if (bound<=0) { state_.last_result=one_based ? 1u : 0u; return state_.last_result; }
        const auto index=advance(state_.selector_seed)%100u;
        const auto previous=state_.table[index];
        state_.table[index]=advance(state_.local_seed);
        state_.last_result=previous%static_cast<uint32_t>(bound)+(one_based ? 1u : 0u);
        return state_.last_result;
    }
    State state_;
};
}
