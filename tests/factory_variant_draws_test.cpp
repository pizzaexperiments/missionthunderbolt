#include "engine/finalized_template_factory_model.hpp"
#include <cassert>
using M=mt::FinalizedTemplateFactoryModel;
static uint32_t field(const M::Record& r,unsigned p) {return (uint32_t(r[p])<<24)|(uint32_t(r[p+1])<<16)|(uint32_t(r[p+2])<<8)|r[p+3];}
int main() {
    M::Templates t{};M::DescriptorFlags d{};M::Thresholds thresholds{};M::Record out{};
    mt::ShuffledLcgModel::State s;s.table.fill(1);
    for(int mode:{-32768,-1,0,1,2,3,4,32767}) {
        t[60][2]=250;t[60][8]=10;t[60][14]=255;t[60][15]=255;t[60][18]=99;
        auto rng=mt::ShuffledLcgModel(s);
        const auto result=M::prepare(out,t,d,{60,0,0,0,mode},rng,{},thresholds);
        assert(result.variant_draws.size()==1 && result.variant_draws[0][0]==4 && result.variant_draws[0][1]==1 && result.variant_draws[0][2]==2);
        assert(out[23]==2 && (out[21]&1) && out[18]==(mode==1?0:mode==2?16:mode==3?117:99));
        if(mode==3)assert(out[2]==14 && out[8]==206 && out[14]==255 && out[15]==251);
        else assert(out[2]==250 && out[8]==10 && out[14]==255 && out[15]==255);
    }
    for(int level:{-32768,-3277,-3,-1,0,1,32767}) {
        t[36][11]=255;t[36][14]=255;t[36][15]=255;auto rng=mt::ShuffledLcgModel(s);
        const auto result=M::prepare(out,t,d,{36,level,0,0},rng,{},thresholds);
        const unsigned expected=static_cast<uint16_t>(65535+10*level);
        assert(result.variant_draws.size()==1 && result.variant_draws[0][0]==20 && result.variant_draws[0][2]==2);
        assert(out[11]==2 && (out[26]&1) && (out[21]&128) && ((out[14]<<8)|out[15])==int(expected));
        assert(out[16]==out[14] && out[17]==out[15]);
    }
    for(uint32_t base:{0u,1u,0xfffffff8u,0xffffffffu}) {
        auto rng=mt::ShuffledLcgModel(s);const auto result=M::prepare(out,t,d,{67,0,0,0,0,base},rng,{},thresholds);
        assert(result.variant_draws.size()==1 && result.variant_draws[0][0]==10 && result.variant_draws[0][2]==2);
        assert(field(out,44)==base+2u && field(out,28)==base+15u && (out[20]&1) && (out[21]&16));
        assert(result.tail.draws[0][0]==100); // Prefix draw is separate from common-tail trace.
    }
}
