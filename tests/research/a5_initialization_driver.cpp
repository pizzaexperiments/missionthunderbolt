#include "engine/a5_initialization_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::A5InitializationModel;
static std::vector<uint8_t> bytes(const std::string& text) {
    if(text=="-")return {};
    if(text.size()%2)throw std::invalid_argument("odd hex input");
    std::vector<uint8_t> result;
    auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("invalid hex");};
    for(size_t i=0;i<text.size();i+=2)result.push_back(static_cast<uint8_t>((nibble(text[i])<<4)|nibble(text[i+1])));
    return result;
}
static void output(const std::vector<uint8_t>& data) {if(data.empty())std::cout<<'-';for(auto b:data)std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);std::cout<<std::dec<<'\n';}
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    std::string mode=argv[1],a,b;size_t index;uint32_t base,alternate;
    while(std::cin>>index) {
        if(mode=="--expand") {
            if(!(std::cin>>a>>b))return 2;
            const auto result=M::expand(bytes(a),bytes(b),index);
            std::cout<<result.data_used<<' '<<result.zero_used<<' ';output(result.bytes);
        } else if(mode=="--relocate") {
            if(!(std::cin>>base>>alternate>>a>>b))return 2;
            auto image=bytes(a);M::relocate(image,index,bytes(b),base,alternate);output(image);
        } else return 2;
    }
    return std::cin.eof()?0:2;
}
