#include "engine/supplied_record_placement_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::FinalizedTemplateFactoryModel;
int main(int argc,char**) {
    if(argc!=1)return 2;
    unsigned mode,fallback,global,warmup,variant,word,flag39;uint32_t seed,last;std::string hex,table_hex,threshold_hex;unsigned child_count,world_count,row,column;uint32_t head,oldlink;

    while(std::cin>>mode>>seed>>fallback>>last>>global>>warmup>>variant>>word>>flag39>>hex>>table_hex>>threshold_hex>>child_count>>world_count>>head>>row>>column>>oldlink) {
        if(mode>2 || fallback>65535 || global>255 || warmup>128 || variant>32767 || word>65535 || flag39>255 || hex.size()!=224 || table_hex.size()!=76*224 || threshold_hex.size()!=1024 || child_count>13 || world_count>65535 || row>=19 || column>=67)return 2;
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
        mt::LinkedRecordModel::Header header{static_cast<uint16_t>(world_count),head};mt::GridFallbackSelector::Grid grid;
        for(auto& cell:grid)cell.bytes.fill(0x5a);
        grid[row*67+column].setLong(12,oldlink);const auto before=grid;
        mt::LinkedRecordModel::Nodes nodes{{0xb0000,{}}};
        const auto result=mt::SuppliedRecordPlacementModel::place(record,header,grid,nodes,0xb0000,static_cast<int>(row),static_cast<int>(column),templates,descriptors,{int(variant),word<32768?int(word):int(word)-65536,static_cast<uint8_t>(flag39),static_cast<uint8_t>(global)},rng,children,thresholds);
        std::cout<<std::hex<<std::setfill('0');for(auto b:record)std::cout<<std::setw(2)<<unsigned(b);
        const auto& s=rng.state();std::cout<<std::dec<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto v:s.table)std::cout<<' '<<v;
        std::cout<<' '<<result.tail.took_zero_path<<' '<<(result.variant_draws.size()+result.tail.draws.size());for(const auto& d:result.variant_draws)for(auto v:d)std::cout<<' '<<v;for(const auto& d:result.tail.draws)for(auto v:d)std::cout<<' '<<v;
        for(unsigned i=0;i<grid.size();++i)for(unsigned j=0;j<20;++j)if((i!=row*67+column || j<12 || j>=16) && grid[i].bytes[j]!=before[i].bytes[j])return 3;
        std::cout<<' '<<result.selected_template<<' '<<result.requires_followup<<' '<<header.count18<<' '<<header.head20<<' '<<grid[row*67+column].longAt(12)<<'\n';
    }
    return std::cin.eof()?0:2;
}
