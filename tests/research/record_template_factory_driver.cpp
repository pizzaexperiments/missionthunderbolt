#include "engine/record_template_factory_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::RecordTemplateFactoryModel;
int main(int argc,char** argv) {
    if(argc==2 && std::string(argv[1])=="--supported") {
        for(int i=0;i<89;++i)if(M::supported(i))std::cout<<i<<' ';
        std::cout<<'\n';return 0;
    }
    if(argc==2 && std::string(argv[1])=="--copy") {
        M::Templates table;for(unsigned i=0;i<76;++i)for(unsigned j=0;j<112;++j)table[i][j]=static_cast<uint8_t>(i*17+j*31);
        int variant;while(std::cin>>variant) {
            const auto index=M::templateIndex(variant);std::cout<<std::dec<<index<<' '<<std::hex<<std::setfill('0');
            for(auto b:table[index])std::cout<<std::setw(2)<<unsigned(b);
            std::cout<<'\n';
        }
        return std::cin.eof()?0:2;
    }
    if(argc!=1)return 2;
    unsigned mode,fallback,global,warmup,variant,word,flag39;uint32_t seed,last;std::string hex,table_hex;

    while(std::cin>>mode>>seed>>fallback>>last>>global>>warmup>>variant>>word>>flag39>>hex>>table_hex) {
        if(mode>2 || fallback>65535 || global>255 || warmup>128 || variant>32767 || word>65535 || flag39>255 || hex.size()!=224 || table_hex.size()!=76*224)return 2;
        auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("hex");};
        M::Record record;for(unsigned i=0;i<112;++i)record[i]=static_cast<uint8_t>((nibble(hex[2*i])<<4)|nibble(hex[2*i+1]));
        M::Templates templates;M::DescriptorFlags descriptors{};
        for(unsigned i=0;i<76*112;++i)templates[i/112][i%112]=static_cast<uint8_t>((nibble(table_hex[2*i])<<4)|nibble(table_hex[2*i+1]));
        mt::ShuffledLcgModel::State state;state.local_seed=seed;state.selector_seed=fallback;state.last_result=last;
        if(mode)state.table.fill(mode-1);
        auto rng=mode?mt::ShuffledLcgModel(state):mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        for(unsigned i=0;i<warmup;++i)rng.zeroBased(1);
        const auto result=M::prepare(record,templates,descriptors,{int(variant),word<32768?int(word):int(word)-65536,static_cast<uint8_t>(flag39),static_cast<uint8_t>(global)},rng);
        std::cout<<std::hex<<std::setfill('0');for(auto b:record)std::cout<<std::setw(2)<<unsigned(b);
        const auto& s=rng.state();std::cout<<std::dec<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto v:s.table)std::cout<<' '<<v;
        std::cout<<' '<<result.tail.took_zero_path<<' '<<(result.variant_draws.size()+result.tail.draws.size());for(const auto& d:result.variant_draws)for(auto v:d)std::cout<<' '<<v;for(const auto& d:result.tail.draws)for(auto v:d)std::cout<<' '<<v;
        std::cout<<' '<<result.selected_template<<' '<<result.requires_followup<<'\n';
    }
    return std::cin.eof()?0:2;
}
