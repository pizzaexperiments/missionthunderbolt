#include "engine/a5_initialization_model.hpp"
#include <cassert>
using M=mt::A5InitializationModel;
int main() {
    const std::vector<uint8_t> data{0x12,0x34,0,0,0xab,0xcd,0,0,0xde,0xad},zero{0,4,0,0,0xa5,0xa5};
    auto result=M::expand(data,zero,12);
    assert((result.bytes==std::vector<uint8_t>{0x12,0x34,0,0,0,0,0,0,0xab,0xcd,0,0}));
    assert(result.data_used==8 && result.zero_used==4);
    result=M::expand({}, {},0);assert(result.bytes.empty() && result.data_used==0 && result.zero_used==0);
    auto rejects=[](const std::vector<uint8_t>& a,const std::vector<uint8_t>& b,size_t size) {
        bool rejected=false;try {M::expand(a,b,size);}catch(const std::exception&){rejected=true;}assert(rejected);
    };
    rejects({0}, {},2);rejects({0,0}, {},2);rejects({0,0},{0,4},4);rejects({0,0},{0,3},6);rejects({}, {},1);rejects({}, {},16*1024*1024+2);
    std::vector<uint8_t> image(20,0);image[4]=image[5]=image[6]=255;image[7]=240;
    image[8]=image[9]=image[10]=255;image[11]=254;
    M::relocate(image,12,{0xff,0xf8,0xff,0xfd,0xff,0xf8,0,1},32,3);
    assert(image[4]==0 && image[5]==0 && image[6]==0 && image[7]==48);
    assert(image[8]==0 && image[9]==0 && image[10]==0 && image[11]==1 && image[15]==3);
    bool rejected=false;try {M::relocate(image,12,{0x80,0},0,0);}catch(const std::out_of_range&){rejected=true;}assert(rejected);
    rejected=false;try {M::relocate(image,12,{0},0,0);}catch(const std::invalid_argument&){rejected=true;}assert(rejected);
    image.assign(3000,0);
    const std::array<int,8> rows{127,-128,5,-7,0,1,2,3},columns{-128,127,-9,11,3,2,1,0};
    for(unsigned i=0;i<8;++i){image[3000-2534+i+1]=static_cast<uint8_t>(rows[i]);image[3000-2522+i+1]=static_cast<uint8_t>(columns[i]);}
    const auto directions=M::directions(image,3000);
    for(unsigned i=0;i<8;++i)assert(directions[i].row==rows[i] && directions[i].column==columns[i]);
    rejected=false;try {M::directions({},0);}catch(const std::out_of_range&){rejected=true;}assert(rejected);
}
