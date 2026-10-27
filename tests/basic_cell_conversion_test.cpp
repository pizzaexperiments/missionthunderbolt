#include "engine/basic_cell_conversion_model.hpp"
#include <cassert>
using M=mt::BasicCellConversionModel;
int main() {
    unsigned count=0;for(unsigned i=0;i<256;++i)if(M::supported(static_cast<uint8_t>(i)))++count;
    assert(count==43 && !M::supported(46) && !M::supported(59) && !M::supported(36));
    M::Cell cell{};cell[2]=255;cell[3]=240;
    M::convert(32,cell,{0,255,0,{32,0,0}});
    assert(cell[0]==0 && cell[2]==0 && cell[3]==6);
    cell.fill(0xa5);cell[2]=0x12;cell[3]=0x34;cell[4]=0;const auto original=cell;
    M::convert(80,cell,{16,0,0,{0,65535,0}});
    assert(cell[0]==1 && cell[1]==45 && cell[2]==0x12 && cell[3]==0x33 && cell[4]==16);
    for(unsigned i=5;i<20;++i)assert(cell[i]==original[i]);
    cell=original;M::convert(112,cell,{16,0,0,{0,65535,0}});
    assert(cell[0]==1 && cell[1]==45 && cell[4]==0);
    cell.fill(0);M::convert(198,cell,{0,0,0,{0,0,1}});
    assert(cell[0]==2 && cell[1]==62 && cell[4]==64 && cell[3]==1);
    cell.fill(0);M::convert(198,cell,{16,0,0,{0,0,1}});
    assert(cell[0]==2 && cell[1]==86 && cell[4]==64 && cell[3]==1);
    for(int level:{0,1}) {
        cell.fill(0);cell[2]=cell[3]=255;
        M::convert(37,cell,{0,0,level,{0,0,1}});
        assert(cell[0]==2 && cell[2]==0 && cell[3]==2);
        assert(cell[1]==(level?52:0) && cell[5]==(level?128:0));
    }
    cell.fill(0xa5);cell[0]=27;cell[1]=0;cell[4]=cell[5]=0;cell[6]=1;const auto before=cell;
    M::adjustSubtype(cell);assert(cell[1]==77);
    for(unsigned i=0;i<20;++i)if(i!=1)assert(cell[i]==before[i]);
    M::adjustSubtype(cell);assert(cell[1]==77);
    cell[0]=255;cell[1]=0;M::adjustSubtype(cell);assert(cell[1]==0);
    cell=original;
    bool rejected=false;try {M::convert(46,cell,{0,255,0,{1,2,3}});}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && cell==original);
}
