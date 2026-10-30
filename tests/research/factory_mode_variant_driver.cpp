#include "engine/finalized_template_factory_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::FinalizedTemplateFactoryModel;
int main(int argc,char**) {
    if(argc!=1)return 2;
    unsigned mode,fallback,global,warmup,variant,word,flag39,mode_word;uint32_t seed,last;std::string hex,table_hex,threshold_hex;unsigned child_count;

    while(std::cin>>mode>>seed>>fallback>>last>>global>>warmup>>variant>>word>>flag39>>mode_word>>hex>>table_hex>>threshold_hex>>child_count) {
        if(mode>2 || fallback>65535 || global>255 || warmup>128 || variant>32767 || word>65535 || flag39>255 || mode_word>65535 || hex.size()!=224 || table_hex.size()!=76*224 || threshold_hex.size()!=1024 || child_count>13)return 2;
        auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("hex");};
        M::Record record;for(unsigned i=0;i<112;++i)record[i]=static_cast<uint8_t>((nibble(hex[2*i])<<4)|nibble(hex[2*i+1]));
        M::Templates templates;M::DescriptorFlags descriptors{};
        for(unsigned i=0;i<76*112;++i)templates[i/112][i%112]=static_cast<uint8_t>((nibble(table_hex[2*i])<<4)|nibble(table_hex[2*i+1]));
        M::Thresholds thresholds;
        for(unsigned i=0;i<256;++i) {const unsigned p=i*4;unsigned w=(nibble(threshold_hex[p])<<12)|(nibble(threshold_hex[p+1])<<8)|(nibble(threshold_hex[p+2])<<4)|nibble(threshold_hex[p+3]);thresholds[i]=static_cast<int16_t>(w<32768?int(w):int(w)-65536);}
        M::Children children;
        for(unsigned i=0;i<child_count;++i) {uint32_t id;std::string text;if(!(std::cin>>id>>text) || text.size()!=64)return 2;
            mt::RecordFollowupModel::Child child;for(unsigned j=0;j<32;++j)child[j]=static_cast<uint8_t>((nibble(text[2*j])<<4)|nibble(text[2*j+1]));children.emplace(id,child);}
        mt::ShuffledLcgModel::State state;state.local_seed=seed;state.selector_seed=fallback;state.last_result=last;
        if(mode)state.table.fill(mode-1);
        auto rng=mode?mt::ShuffledLcgModel(state):mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        for(unsigned i=0;i<warmup;++i)rng.zeroBased(1);
        const auto result=M::prepare(record,templates,descriptors,{int(variant),word<32768?int(word):int(word)-65536,static_cast<uint8_t>(flag39),static_cast<uint8_t>(global),mode_word<32768?int(mode_word):int(mode_word)-65536},rng,children,thresholds);
        std::cout<<std::hex<<std::setfill('0');for(auto b:record)std::cout<<std::setw(2)<<unsigned(b);
        const auto& s=rng.state();std::cout<<std::dec<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto v:s.table)std::cout<<' '<<v;
        std::cout<<' '<<result.tail.took_zero_path<<' '<<result.tail.draws.size();for(const auto& d:result.tail.draws)for(auto v:d)std::cout<<' '<<v;
        std::cout<<' '<<result.selected_template<<' '<<result.requires_followup<<'\n';
    }
    return std::cin.eof()?0:2;
}
