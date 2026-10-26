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
    initial.table[0]=32768; bool rejected=false;
    try {mt::ShuffledLcgModel model(initial);} catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected);
}
