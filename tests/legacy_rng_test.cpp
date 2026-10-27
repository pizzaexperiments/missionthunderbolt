#include "engine/shuffled_lcg_model.hpp"
#include <cassert>
#include <climits>
int main() {
    mt::ShuffledLcgModel::State initial;
    initial.local_seed=1; initial.selector_seed=42;
    for (unsigned i=0;i<100;++i) initial.table[i]=31*i+7;
    mt::ShuffledLcgModel zero(initial),one(initial);
    // Frozen synthetic-input result, cross-checked against isolated 68000 instructions.
    assert(zero.zeroBased(100)==18); assert(one.oneBased(100)==19);
    const auto& after=zero.state();
    assert(after.local_seed==1103527590u && after.selector_seed==3397979675u);
    assert(after.last_result==18);
    for(unsigned i=0;i<100;++i) assert(after.table[i]==(i==81 ? 16838u : initial.table[i]));
    for(int bound : {-32768,-1,0}) {
        mt::ShuffledLcgModel a(initial),b(initial);
        assert(a.zeroBased(bound)==0 && b.oneBased(bound)==1);
        assert(a.state().local_seed==1 && a.state().selector_seed==42);
        assert(a.state().table==initial.table && b.state().table==initial.table);
    }
    for(int bound : {INT_MIN,-32769,32768,INT_MAX}) {
        mt::ShuffledLcgModel model(initial); bool rejected=false;
        try {model.zeroBased(bound);} catch(const std::invalid_argument&) {rejected=true;}
        assert(rejected && model.state().table==initial.table && model.state().local_seed==1);
    }
    auto seeded=mt::ShuffledLcgModel::initialized(0,42,123);
    assert(seeded.state().local_seed==3885567453u);
    assert(seeded.state().selector_seed==42 && seeded.state().last_result==123);
    uint32_t table_hash=2166136261u;
    for(auto value:seeded.state().table)
        for(int shift : {24,16,8,0}) table_hash=(table_hash^((value>>shift)&255u))*16777619u;
    assert(table_hash==0xc9f69394u);
    const std::array<uint32_t,12> expected{{22,3,6,84,22,45,25,39,59,55,38,26}};
    for(unsigned i=0;i<expected.size();++i)
        assert((i%2 ? seeded.oneBased(100) : seeded.zeroBased(100))==expected[i]);
    auto explicit_seed=mt::ShuffledLcgModel::initialized(42,65535,123);
    auto fallback_seed=mt::ShuffledLcgModel::initialized(0,42,123);
    assert(explicit_seed.state().table==fallback_seed.state().table);
    assert(explicit_seed.state().selector_seed==fallback_seed.state().selector_seed);
    // Nonzero full-width argument uses its low word even when that word is zero.
    assert(mt::ShuffledLcgModel::initialized(65536,42).state().selector_seed==0);
    assert(mt::ShuffledLcgModel::initialized(0xffffffffu,0).state().selector_seed==65535);
    initial.table[0]=32768; bool rejected=false;
    try {mt::ShuffledLcgModel model(initial);} catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected);
}
