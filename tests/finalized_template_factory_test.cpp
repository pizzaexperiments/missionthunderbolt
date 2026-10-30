#include "engine/finalized_template_factory_model.hpp"
#include <cassert>
using M=mt::FinalizedTemplateFactoryModel;
int main() {
    M::Templates tables{};M::DescriptorFlags descriptors{};M::Thresholds thresholds{};
    tables[1][1]=1;tables[1][20]=32;tables[1][22]=99;tables[1][51]=1;
    tables[1][63]=100;M::Children children{{100,{}}};children[100][17]=5;
    mt::ShuffledLcgModel::State state;state.table.fill(1);auto rng=mt::ShuffledLcgModel(state);
    M::Record out{};auto result=M::prepare(out,tables,descriptors,{1,0,0,0},rng,children,thresholds);
    assert(result.requires_followup && out[22]==0 && (out[20]&32)); // Slot zero selected.
    children[100][24]=2;M::prepare(out,tables,descriptors,{1,0,0,0},rng,children,thresholds);
    assert(out[22]==0 && !(out[20]&32));
    tables[1][20]=0;M::prepare(out,tables,descriptors,{1,0,0,0},rng,{},thresholds);assert(out[22]==99);
    tables[1][20]=32;const auto before=out;const auto prior=rng.state();bool rejected=false;
    try {M::prepare(out,tables,descriptors,{1,0,0,0},rng,{},thresholds);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && out==before && rng.state().table==prior.table && rng.state().local_seed==prior.local_seed && rng.state().selector_seed==prior.selector_seed && rng.state().last_result==prior.last_result);
}
