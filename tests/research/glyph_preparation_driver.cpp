#include "engine/glyph_preparation_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
int main() {
    uint32_t seed,last;unsigned fallback,flags,level,metadata;std::string hex;
    while(std::cin>>seed>>fallback>>last>>flags>>level>>metadata>>hex) {
        if(fallback>65535 || flags>255 || level>65535 || metadata>255 || hex.size()!=1273*2)return 2;
        mt::GlyphPreparationModel::Map map;
        auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("bad hex");};
        for(unsigned i=0;i<1273;++i)map[i]=static_cast<uint8_t>((nibble(hex[i*2])<<4)|nibble(hex[i*2+1]));
        auto rng=mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        const int signed_level=level<32768?static_cast<int>(level):static_cast<int>(level)-65536;
        const auto result=mt::GlyphPreparationModel::prepare(map,static_cast<uint8_t>(flags),signed_level,static_cast<uint8_t>(metadata),rng);
        for(auto count:result.attempts)std::cout<<count<<' ';
        const auto& s=rng.state();std::cout<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto value:s.table)std::cout<<' '<<value;
        std::cout<<' '<<std::hex<<std::setfill('0');for(auto b:map)std::cout<<std::setw(2)<<unsigned(b);
        std::cout<<std::dec<<' '<<result.draws.size();for(const auto& d:result.draws)for(auto value:d)std::cout<<' '<<value;
        std::cout<<' '<<result.writes.size();for(const auto& w:result.writes)for(auto value:w)std::cout<<' '<<value;
        std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
