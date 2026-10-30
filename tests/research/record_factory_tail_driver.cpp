#include "engine/record_factory_tail_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::RecordFactoryTailModel;
int main() {
    unsigned mode,fallback,global,warmup;uint32_t seed,last;std::string hex;
    while(std::cin>>mode>>seed>>fallback>>last>>global>>warmup>>hex) {
        if(mode>2 || fallback>65535 || global>255 || warmup>128 || hex.size()!=224)return 2;
        auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("hex");};
        M::Record record;for(unsigned i=0;i<112;++i)record[i]=static_cast<uint8_t>((nibble(hex[2*i])<<4)|nibble(hex[2*i+1]));
        mt::ShuffledLcgModel::State state;state.local_seed=seed;state.selector_seed=fallback;state.last_result=last;
        if(mode)state.table.fill(mode-1);
        auto rng=mode?mt::ShuffledLcgModel(state):mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        for(unsigned i=0;i<warmup;++i)rng.zeroBased(1);
        const auto result=M::apply(record,static_cast<uint8_t>(global),rng);
        std::cout<<std::hex<<std::setfill('0');for(auto b:record)std::cout<<std::setw(2)<<unsigned(b);
        const auto& s=rng.state();std::cout<<std::dec<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto v:s.table)std::cout<<' '<<v;
        std::cout<<' '<<result.took_zero_path<<' '<<result.draws.size();for(const auto& d:result.draws)for(auto v:d)std::cout<<' '<<v;
        std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
