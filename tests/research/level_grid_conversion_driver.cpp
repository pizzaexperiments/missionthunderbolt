#include "engine/level_grid_conversion_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::LevelGridConversionModel;
static unsigned nibble(char c) {
    if(c>='0' && c<='9')return c-'0';
    if(c>='a' && c<='f')return c-'a'+10;
    throw std::invalid_argument("bad hex");
}
static std::string decode(const std::string& text) {
    if(text.size()%2)throw std::invalid_argument("odd hex");
    std::string out;for(unsigned i=0;i<text.size();i+=2)out.push_back(static_cast<char>((nibble(text[i])<<4)|nibble(text[i+1])));return out;
}
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    const std::string mode=argv[1];
    if(mode=="--grid") {
        unsigned flags,byte8,word,a,b,c,t31,t32,t34,fallback;uint32_t seed,last;std::string glyph_hex,record_hex;
        while(std::cin>>flags>>byte8>>word>>a>>b>>c>>t31>>t32>>t34>>seed>>fallback>>last>>glyph_hex>>record_hex) {
            if(flags>255 || byte8>255 || word>65535 || a>65535 || b>65535 || c>65535 || t31>65535 || t32>65535 || t34>65535 || fallback>65535)return 2;
            const auto glyph_bytes=decode(glyph_hex),record_bytes=decode(record_hex);
            if(glyph_bytes.size()!=mt::DirectGridConversionModel::count || record_bytes.size()!=mt::DirectGridConversionModel::count*20)return 2;
            M::Glyphs glyphs;M::Records records;
            for(unsigned i=0;i<mt::DirectGridConversionModel::count;++i) {glyphs[i]=static_cast<uint8_t>(glyph_bytes[i]);
                for(unsigned j=0;j<20;++j)records[i][j]=static_cast<uint8_t>(record_bytes[i*20+j]);}
            auto rng=mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
            const auto draws=M::convert(glyphs,records,{{static_cast<uint8_t>(flags),static_cast<uint8_t>(byte8),word<32768?int(word):int(word)-65536,{static_cast<uint16_t>(a),static_cast<uint16_t>(b),static_cast<uint16_t>(c)}},static_cast<uint16_t>(t31),static_cast<uint16_t>(t32),static_cast<uint16_t>(t34)},rng);
            const auto& state=rng.state();std::cout<<state.last_result<<' '<<state.local_seed<<' '<<state.selector_seed;
            for(auto value:state.table)std::cout<<' '<<value;
            std::cout<<' ';
            for(const auto& cell:records)for(auto value:cell)std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(value);
            std::cout<<std::dec<<' '<<draws.size();for(const auto& draw:draws)for(auto value:draw)std::cout<<' '<<value;
            std::cout<<'\n';
        }
    } else return 2;
    return std::cin.eof()?0:2;
}
