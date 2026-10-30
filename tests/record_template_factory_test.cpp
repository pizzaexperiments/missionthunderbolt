#include "engine/record_template_factory_model.hpp"
#include <cassert>
using M=mt::RecordTemplateFactoryModel;
static bool same(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
int main() {
    assert(M::templateIndex(75)==75 && M::templateIndex(76)==0 && M::templateIndex(32767)==0);
    M::Templates templates{};M::DescriptorFlags descriptors{};
    for(unsigned i=0;i<76;++i) {templates[i].fill(static_cast<uint8_t>(i));templates[i][0]=0;templates[i][1]=static_cast<uint8_t>(i);}
    templates[0][1]=3;templates[0][20]=32;templates[3][20]=32;
    mt::ShuffledLcgModel::State state;state.table.fill(1);
    auto rng=mt::ShuffledLcgModel(state);M::Record output;
    auto result=M::prepare(output,templates,descriptors,{79,0,0,255},rng);
    assert(result.selected_template==0 && result.requires_followup && output[0]==0 && output[1]==3);
    assert(output[20]==0 && output[21]==8); // Follow-up flag is read from source template 3, not cleared output.
    result=M::prepare(output,templates,descriptors,{89,0,0,255},rng);assert(result.selected_template==0 && output[21]==0);
    for(auto& t:templates) {t.fill(0);t[1]=0;}
    result=M::prepare(output,templates,descriptors,{65,32767,0,0},rng);
    assert(output[4]==255 && output[5]==255 && output[6]==255 && output[7]==156); // sign-extended low word of 100*32767 = -100.
    assert(output[2]==255 && output[8]==1 && output[9]==255 && output[14]==255 && output[15]==236);
    result=M::prepare(output,templates,descriptors,{38,-3,0,0},rng);assert(output[14]==255 && output[15]==254);
    result=M::prepare(output,templates,descriptors,{35,-3,0,0},rng);assert(output[8]==0 && output[21]==16); // DIVS truncates toward zero.
    result=M::prepare(output,templates,descriptors,{39,0,255,0},rng);assert(output[21]==128);
    const auto before=output;const auto prior=rng.state();
    for(int variant:{-1,6,8,32768}) {
        bool rejected=false;try {M::prepare(output,templates,descriptors,{variant,0,0,0},rng);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && output==before && same(prior,rng.state()));
    }
    bool rejected=false;
    try {M::prepare(output,templates,descriptors,{1,32768,0,0},rng);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && output==before && same(prior,rng.state()));
    descriptors[0]=1;rejected=false;
    try {M::prepare(output,templates,descriptors,{1,0,0,0},rng);}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && output==before && same(prior,rng.state()));
    descriptors[0]=0;templates[1][0]=128;rejected=false;
    try {M::prepare(output,templates,descriptors,{1,0,0,0},rng);}catch(const std::out_of_range&){rejected=true;}
    assert(rejected && output==before && same(prior,rng.state()));
}
