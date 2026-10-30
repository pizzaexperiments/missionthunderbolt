#include "engine/finalized_template_factory_model.hpp"
#include <cassert>
using M=mt::FinalizedTemplateFactoryModel;
int main() {
    M::Templates t{};M::DescriptorFlags d{};M::Thresholds thresholds{};M::Record out;
    t[7][1]=7;t[7][2]=250;t[7][4]=t[7][5]=t[7][6]=t[7][7]=255;t[7][8]=60;t[7][14]=255;t[7][15]=255;
    for(int mode:{-32768,-1,0,1,2,3,4,32767}) {
        mt::ShuffledLcgModel::State s;s.table.fill(1);auto rng=mt::ShuffledLcgModel(s);
        const auto result=M::prepare(out,t,d,{7,0,0,0,mode},rng,{},thresholds);
        assert(result.selected_template==7 && !result.requires_followup && result.tail.draws.size()==1 && (out[21]&8));
        if(mode<=2)assert(out[2]==250 && out[8]==60 && out[14]==255 && out[15]==255 && out[7]==255);
        else assert(out[2]==27 && out[8]==249 && out[14]==255 && out[15]==176 && out[4]==255 && out[5]==255 && out[6]==251 && out[7]==30);
        assert(out[16]==out[14] && out[17]==out[15]);
    }
    auto rng=mt::ShuffledLcgModel::initialized(42,42);const auto prior=rng.state();const auto before=out;bool rejected=false;
    try {M::prepare(out,t,d,{7,0,0,0,32768},rng,{},thresholds);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && out==before && rng.state().table==prior.table && rng.state().selector_seed==prior.selector_seed && rng.state().local_seed==prior.local_seed && rng.state().last_result==prior.last_result);
}
