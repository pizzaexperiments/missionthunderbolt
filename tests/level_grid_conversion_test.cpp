#include "engine/level_grid_conversion_model.hpp"
#include <cassert>
using M=mt::LevelGridConversionModel;
static bool same(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
int main() {
    M::Glyphs glyphs;glyphs.fill(32);M::Records records{};
    auto rng=mt::ShuffledLcgModel::initialized(42,42,123);const auto initial=rng.state();
    glyphs[0]=215;glyphs[66]=175;glyphs[67]=187;glyphs.back()=171;
    M::Context c{{0,255,255,{11,22,33}},100,200,300};
    assert(M::convert(glyphs,records,c,rng).empty());assert(same(initial,rng.state()));
    assert(records[0][0]==34 && records[0][1]==89 && records[0][2]==5 && records[0][3]==10);
    assert(records[66][0]==34 && records[66][1]==88);
    assert(records[67][0]==32 && records[67][4]==4 && records[67][9]==0);
    assert(records.back()[0]==31 && records.back()[4]==4 && records.back()[9]==254);
    c.direct.flags6=16;M::convert(glyphs,records,c,rng);assert(records[0][1]==87);
    glyphs.fill(32);glyphs[0]=94;glyphs[67]=118;c.direct.level=0;
    for(auto& cell:records)cell.fill(0xa5);
    assert(M::convert(glyphs,records,c,rng).empty());assert(same(initial,rng.state()));
    assert(records[0][0]==0 && records[0][2]==0 && records[0][3]==11 && records[0][9]==0xa5 && records[0][4]==0xa5);
    c.direct.level=1;const auto draws=M::convert(glyphs,records,c,rng);
    assert(draws.size()==2 && draws[0][0]==0 && draws[0][1]==0 && draws[1][0]==1 && draws[1][1]==0);
    assert(draws[0][2]==3 && draws[0][3]==1 && draws[0][4]==1 && draws[1][4]==2);
    assert(rng.state().last_result==2 && rng.state().local_seed==601077795u && rng.state().selector_seed==3263785912u);
    assert(records[0][9]==static_cast<uint8_t>(1-int(draws[0][4])) && records[67][9]==1+draws[1][4]);
    assert(!same(initial,rng.state()));
    const auto before=records;const auto state=rng.state();glyphs.back()=46;
    bool rejected=false;try {M::convert(glyphs,records,c,rng);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && records==before && same(state,rng.state()));
    glyphs.back()=32;c.direct.level=32768;rejected=false;
    try {M::convert(glyphs,records,c,rng);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && records==before && same(state,rng.state()));
}
