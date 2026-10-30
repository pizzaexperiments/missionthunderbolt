#include "engine/supplied_record_placement_model.hpp"
#include <cassert>
using M=mt::SuppliedRecordPlacementModel;
int main() {
    M::Factory::Templates templates{};M::Factory::DescriptorFlags descriptors{};M::Factory::Thresholds thresholds{};
    templates[1][1]=1;templates[1][20]=32;templates[1][51]=1;templates[1][63]=100;
    M::Factory::Children children{{100,{}}};children[100][17]=5;
    M::Factory::Record record{};mt::LinkedRecordModel::Header header{65535,0x2000};
    mt::GridFallbackSelector::Grid grid{};grid.back().setLong(12,0xdeadbeef);
    mt::LinkedRecordModel::Nodes nodes{{0x1000,{}},{0x2000,{1,2,3}}};
    mt::ShuffledLcgModel::State state;state.table.fill(1);auto rng=mt::ShuffledLcgModel(state);
    const auto result=M::place(record,header,grid,nodes,0x1000,18,66,templates,descriptors,{1,0,0,0},rng,children,thresholds);
    assert(result.requires_followup && (record[20]&32) && record[22]==0);
    assert(header.count18==0 && header.head20==0x1000 && grid.back().longAt(12)==0x1000);
    assert(record[48]==18 && record[49]==66 && record[56]==0 && record[57]==0 && record[58]==32 && record[59]==0);
    assert(nodes.at(0x1000).next56==0x2000 && nodes.at(0x2000).next56==3);
    const auto before=record;const auto prior=rng.state();const auto cell=grid.back().bytes;
    for(int row:{-1,19}) {
        bool rejected=false;try {M::place(record,header,grid,nodes,0x1000,row,66,templates,descriptors,{1,0,0,0},rng,children,thresholds);}catch(const std::out_of_range&){rejected=true;}
        assert(rejected && record==before && header.count18==0 && header.head20==0x1000 && grid.back().bytes==cell && rng.state().table==prior.table);
    }
    bool rejected=false;
    try {M::place(record,header,grid,nodes,0x1000,0,0,templates,descriptors,{1,0,0,0},rng,{},thresholds);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && record==before && header.count18==0 && header.head20==0x1000 && grid.back().bytes==cell && rng.state().table==prior.table && rng.state().local_seed==prior.local_seed && rng.state().selector_seed==prior.selector_seed && rng.state().last_result==prior.last_result);
}
