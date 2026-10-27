#include "engine/glyph_preparation_model.hpp"
#include <cassert>
using M=mt::GlyphPreparationModel;
static uint32_t hash(const M::Map& map) {uint32_t value=2166136261u;for(auto b:map)value=(value^b)*16777619u;return value;}
int main() {
    // Frozen original-instruction results on authored all-space maps.
    M::Map map;map.fill(32);auto rng=mt::ShuffledLcgModel::initialized(42,42,123);
    auto result=M::prepare(map,0,1,0,rng);
    assert((result.attempts==std::array<uint32_t,3>{32,32,2}));
    assert(result.draws.size()==166 && result.writes.size()==61 && hash(map)==3271752835u);
    assert(rng.state().last_result==1 && rng.state().local_seed==3735676127u && rng.state().selector_seed==2734910788u);
    assert((result.draws[0]==std::array<uint32_t,3>{19,0,4}));
    assert((result.draws[1]==std::array<uint32_t,3>{67,0,59}));
    assert((result.draws[2]==std::array<uint32_t,3>{32,0,26}));
    assert((result.draws.back()==std::array<uint32_t,3>{3,1,1}));
    for(const auto& write:result.writes)assert(write[3]==32);
    map.fill(32);rng=mt::ShuffledLcgModel::initialized(42,42,123);result=M::prepare(map,4,1,0,rng);
    assert((result.attempts==std::array<uint32_t,3>{0,16,3}));
    assert(result.draws.size()==42 && result.writes.size()==19 && hash(map)==1666682687u);
    assert(rng.state().last_result==3 && rng.state().local_seed==2965106811u && rng.state().selector_seed==2072944688u);
    assert((result.draws.back()==std::array<uint32_t,3>{3,1,3})); // final condition fails with counter 4
    for(int level:{46,69}) {
        map.fill(32);rng=mt::ShuffledLcgModel::initialized(42,42,123);const auto before=rng.state();
        result=M::prepare(map,4,level,0,rng);
        assert((result.attempts==std::array<uint32_t,3>{0,0,0}) && result.draws.empty() && result.writes.empty());
        assert(rng.state().table==before.table && rng.state().last_result==before.last_result && rng.state().selector_seed==before.selector_seed);
        for(auto value:map)assert(value==32);
    }
    for(unsigned value=0;value<256;++value)if(value!=32) {
        map.fill(static_cast<uint8_t>(value));rng=mt::ShuffledLcgModel::initialized(42,42,123);
        result=M::prepare(map,0,1,0,rng);assert(result.writes.empty());for(auto b:map)assert(b==value);
    }
    map.fill(32);rng=mt::ShuffledLcgModel::initialized(42,42,123);const auto before=rng.state();
    bool rejected=false;try {M::prepare(map,0,32768,0,rng);}catch(const std::invalid_argument&){rejected=true;}assert(rejected);
    assert(rng.state().table==before.table && rng.state().last_result==before.last_result);for(auto b:map)assert(b==32);
}
