#include "engine/child_chain_model.hpp"
#include <iomanip>
#include <iostream>
#include <string>
using M=mt::ChildChainModel;
static unsigned nibble(char c) {
    if(c>='0' && c<='9')return static_cast<unsigned>(c-'0');
    if(c>='a' && c<='f')return static_cast<unsigned>(c-'a'+10);
    throw std::invalid_argument("hex");
}
static void decode(const std::string& hex,uint8_t* out,unsigned size) {
    if(hex.size()!=2u*size)throw std::invalid_argument("hex size");
    for(unsigned i=0;i<size;++i)out[i]=static_cast<uint8_t>((nibble(hex[2*i])<<4)|nibble(hex[2*i+1]));
}
static void print(const M::Record& r) {for(auto b:r)std::cout<<std::setw(2)<<unsigned(b);}
int main() {
    unsigned mode,fallback,warmup,factor,counter,factor42;uint32_t seed,last,parent_handle,base;std::string hex;
    while(std::cin>>mode>>seed>>fallback>>last>>warmup>>parent_handle) {
        if(mode>1 || fallback>65535 || warmup>128)return 2;
        M::Handles handles{};for(auto& h:handles)if(!(std::cin>>h))return 2;
        M::Context context;if(!(std::cin>>hex>>factor>>counter>>base>>factor42))return 2;
        if(factor>65535 || counter>65535 || factor42>65535)return 2;
        decode(hex,context.lookup.data(),50);context.factor_word=static_cast<uint16_t>(factor);
        context.counter=static_cast<uint16_t>(counter);context.address_base=base;const auto before=context;
        M::Record parent{};if(!(std::cin>>hex))return 2;decode(hex,parent.data(),56);
        M::Records children{};for(auto& r:children) {if(!(std::cin>>hex))return 2;decode(hex,r.data(),56);}
        M::Templates templates{};
        for(unsigned i=0;i<templates.size();++i)for(unsigned j=0;j<56;++j)templates[i][j]=static_cast<uint8_t>(i*17u+j*31u);
        templates[42][14]=static_cast<uint8_t>(factor42>>8);templates[42][15]=static_cast<uint8_t>(factor42);
        const unsigned variants[5]={31,27,28,37,72};
        for(unsigned i=0;i<5;++i) {if(!(std::cin>>hex))return 2;decode(hex,templates[variants[i]].data(),56);}
        const auto templates_before=templates;
        mt::ShuffledLcgModel::State state;state.local_seed=seed;state.selector_seed=fallback;state.last_result=last;
        if(mode)for(auto& v:state.table)if(!(std::cin>>v))return 2;
        auto rng=mode?mt::ShuffledLcgModel(state):mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        for(unsigned i=0;i<warmup;++i)rng.zeroBased(1);
        const auto result=M::prepare(parent,parent_handle,children,handles,templates,rng,context);
        if(templates!=templates_before || context.lookup!=before.lookup || context.factor_word!=before.factor_word || context.address_base!=before.address_base)return 3;
        std::cout<<std::hex<<std::setfill('0');print(parent);for(const auto& r:children) {std::cout<<' ';print(r);}
        const auto& s=rng.state();std::cout<<std::dec<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto v:s.table)std::cout<<' '<<v;
        std::cout<<' '<<context.counter<<' '<<result.draws.size();for(const auto& d:result.draws)for(auto v:d)std::cout<<' '<<v;
        for(auto n:result.factory_draw_counts)std::cout<<' '<<n;
        std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
