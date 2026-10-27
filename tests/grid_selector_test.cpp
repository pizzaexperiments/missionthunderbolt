#include "engine/grid_candidate_selector.hpp"
#include <cassert>

using Selector=mt::GridCandidateSelector;
// Authored ordering supplied explicitly; historical direction data remains unresolved.
static const Selector::Directions directions{{{-1,0},{-1,1},{0,1},{1,1},{1,0},{1,-1},{0,-1},{-1,-1}}};
static uint32_t tableHash(const mt::ShuffledLcgModel& rng) {
    uint32_t value=2166136261u;
    for(auto entry:rng.state().table)
        for(int shift : {24,16,8,0})value=(value^((entry>>shift)&255u))*16777619u;
    return value;
}
int main() {
    // Frozen synthetic-input traces independently executed against original instructions.
    Selector::Grid grid{};
    auto empty_rng=mt::ShuffledLcgModel::initialized(42,42,123);
    auto result=Selector::select(grid,directions,empty_rng);
    assert(result.outcome==Selector::Outcome::direct && result.iterations==1);
    assert(result.coordinate.row==16 && result.coordinate.column==3);
    assert(empty_rng.state().last_result==3 && empty_rng.state().local_seed==601077795u && empty_rng.state().selector_seed==3263785912u);
    assert(tableHash(empty_rng)==0xe60f9b09u);
    for(auto& cell:grid)cell.kind=1;
    auto blocked_rng=mt::ShuffledLcgModel::initialized(42,42,123);
    result=Selector::select(grid,directions,blocked_rng);
    assert(result.outcome==Selector::Outcome::needs_fallback && result.iterations==200);
    assert(result.coordinate.row==17 && result.coordinate.column==9);
    assert(blocked_rng.state().last_result==1 && blocked_rng.state().local_seed==2836888651u && blocked_rng.state().selector_seed==1125943744u);
    assert(tableHash(blocked_rng)==0x0a102507u);
    for(int y=0;y<19;++y)for(int x=0;x<67;++x)grid[y*67+x].kind=static_cast<uint8_t>((x+y)%2);
    auto neighbor_rng=mt::ShuffledLcgModel::initialized(42,42,123);
    result=Selector::select(grid,directions,neighbor_rng);
    assert(result.outcome==Selector::Outcome::neighbor && result.iterations==1);
    assert(result.coordinate.row==16 && result.coordinate.column==4);
    assert(neighbor_rng.state().last_result==3 && neighbor_rng.state().local_seed==290603296u && neighbor_rng.state().selector_seed==3148160401u);
    assert(tableHash(neighbor_rng)==0xba90e463u);
    auto invalid=directions;invalid[0].row=128;
    auto unchanged=mt::ShuffledLcgModel::initialized(42,42,123);const auto before=unchanged.state();
    bool rejected=false;try {Selector::select(grid,invalid,unchanged);} catch(const std::out_of_range&) {rejected=true;}
    assert(rejected && unchanged.state().table==before.table && unchanged.state().last_result==before.last_result);
    assert(unchanged.state().local_seed==before.local_seed && unchanged.state().selector_seed==before.selector_seed);
}
