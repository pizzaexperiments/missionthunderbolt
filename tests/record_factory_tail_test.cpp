#include "engine/record_factory_tail_model.hpp"
#include <cassert>
using M=mt::RecordFactoryTailModel;
int main() {
    // Authored shuffle tables make the zero/nonzero branch deterministic.
    mt::ShuffledLcgModel::State state;state.table.fill(1);
    mt::ShuffledLcgModel normal(state);M::Record record;record.fill(0xa5);record[14]=0x80;record[15]=0;
    const auto before=record;auto result=M::apply(record,255,normal);
    assert(!result.took_zero_path && result.draws.size()==1 && result.draws[0][0]==100 && result.draws[0][2]==1);
    assert(record[16]==0x80 && record[17]==0);
    for(unsigned i=0;i<112;++i)if(i!=16 && i!=17)assert(record[i]==before[i]);
    state.table.fill(0);mt::ShuffledLcgModel rare(state);record.fill(0);
    record[2]=255;record[8]=0;record[9]=255;record[4]=record[5]=record[6]=record[7]=255;
    result=M::apply(record,255,rare);
    assert(result.took_zero_path && result.draws.size()==8);
    const std::vector<M::Draw> expected_draws{{100,0,0},{0,1,1},{0,1,1},{0,1,1},{10,1,1},{10,1,1},{10,1,1},{0,1,1}};
    assert(result.draws==expected_draws);
    assert(record[2]==0 && record[8]==255 && record[9]==0);
    assert(record[14]==0 && record[15]==1 && record[16]==0 && record[17]==1);
    assert(record[4]==255 && record[5]==255 && record[6]==255 && record[7]==254); // -1 + arithmetic-half(-1) = -2.
    assert(result.draws[1][0]==0 && result.draws[2][0]==0 && result.draws[3][0]==0 && result.draws[7][0]==0);
    assert(record[10]==1 && record[11]==1 && record[13]==1);
    for(uint32_t bits:{0u,1u,3u,0x7fffffffu,0x80000000u,0xfffffffdu}) {
        state.table.fill(0);mt::ShuffledLcgModel rng(state);record.fill(0);
        for(unsigned n=0;n<4;++n)record[4+n]=static_cast<uint8_t>(bits>>(24-8*n));
        M::apply(record,128,rng);
        const uint32_t expected=bits==0?0:bits==1?1:bits==3?4:bits==0x7fffffffu?0xbffffffeu:bits==0x80000000u?0x40000000u:0xfffffffbu;
        const uint32_t actual=(uint32_t(record[4])<<24)|(uint32_t(record[5])<<16)|(uint32_t(record[6])<<8)|record[7];assert(actual==expected);
    }
}
