#include "engine/child_record_factory_model.hpp"
#include <iomanip>
#include <iostream>
#include <string>
using M=mt::ChildRecordFactoryModel;
static unsigned nibble(char c) {
    if(c>='0' && c<='9')return static_cast<unsigned>(c-'0');
    if(c>='a' && c<='f')return static_cast<unsigned>(c-'a'+10);
    throw std::invalid_argument("hex");
}
static void decode(const std::string& hex,uint8_t* out,unsigned size) {
    if(hex.size()!=size*2u)throw std::invalid_argument("hex size");
    for(unsigned i=0;i<size;++i)out[i]=static_cast<uint8_t>((nibble(hex[i*2])<<4)|nibble(hex[i*2+1]));
}
int main() {
    unsigned mode,fallback,warmup,variant,factor;int level;uint32_t seed,last;std::string initial_hex,template_hex;
    while(std::cin>>mode>>seed>>fallback>>last>>warmup>>variant>>level>>factor>>initial_hex>>template_hex) {
        if(mode>1 || fallback>65535 || warmup>128 || variant>32767 || factor>65535 || level < -32768 || level>32767)return 2;
        M::Templates templates{};
        for(unsigned i=0;i<templates.size();++i)
            for(unsigned j=0;j<templates[i].size();++j)templates[i][j]=static_cast<uint8_t>(i*17u+j*31u);
        const unsigned selected=variant<=136?variant:0;
        templates[42][14]=static_cast<uint8_t>(factor>>8);templates[42][15]=static_cast<uint8_t>(factor);
        decode(template_hex,templates[selected].data(),56);
        M::Record record{};decode(initial_hex,record.data(),56);
        mt::ShuffledLcgModel::State state;state.local_seed=seed;state.selector_seed=fallback;state.last_result=last;
        if(mode)for(auto& value:state.table)if(!(std::cin>>value))return 2;
        auto rng=mode?mt::ShuffledLcgModel(state):mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        for(unsigned i=0;i<warmup;++i)rng.zeroBased(1);
        const auto result=M::prepare(record,templates,static_cast<int>(variant),level,rng);
        std::cout<<std::hex<<std::setfill('0');for(auto b:record)std::cout<<std::setw(2)<<unsigned(b);
        const auto& s=rng.state();std::cout<<std::dec<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto value:s.table)std::cout<<' '<<value;
        std::cout<<' '<<result.selected_template<<' '<<result.draws.size();
        for(const auto& d:result.draws)for(auto value:d)std::cout<<' '<<value;
        std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
