#include "engine/basic_cell_conversion_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::BasicCellConversionModel;
static M::Cell decode(const std::string& hex) {
    if(hex.size()!=40)throw std::invalid_argument("cell hex size");
    auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("bad hex");};
    M::Cell result;for(unsigned i=0;i<20;++i)result[i]=static_cast<uint8_t>((nibble(hex[2*i])<<4)|nibble(hex[2*i+1]));return result;
}
static void emit(const M::Cell& cell) {for(auto b:cell)std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);std::cout<<std::dec<<'\n';}
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    const std::string mode=argv[1];
    if(mode=="--supported") {for(unsigned i=0;i<256;++i)if(M::supported(static_cast<uint8_t>(i)))std::cout<<i<<' ';std::cout<<'\n';return 0;}
    std::string hex;unsigned glyph,flags,byte8,level,a,b,c;
    if(mode=="--adjust") {while(std::cin>>hex){auto cell=decode(hex);M::adjustSubtype(cell);emit(cell);}}
    else if(mode=="--convert")while(std::cin>>glyph>>flags>>byte8>>level>>a>>b>>c>>hex) {
        if(glyph>255 || flags>255 || byte8>255 || level>65535 || a>65535 || b>65535 || c>65535)return 2;
        auto cell=decode(hex);M::convert(static_cast<uint8_t>(glyph),cell,{static_cast<uint8_t>(flags),static_cast<uint8_t>(byte8),level<32768?int(level):int(level)-65536,{static_cast<uint16_t>(a),static_cast<uint16_t>(b),static_cast<uint16_t>(c)}});emit(cell);
    }
    else return 2;
    return std::cin.eof()?0:2;
}
