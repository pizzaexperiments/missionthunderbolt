#include "engine/child_record_word_selector_model.hpp"
#include <iostream>
using M=mt::ChildRecordWordSelectorModel;
template<std::size_t N> static void put(std::array<uint8_t,N>& r,unsigned p,unsigned n) {
    r[p]=static_cast<uint8_t>(n>>8);r[p+1]=static_cast<uint8_t>(n);
}
int main() {
    unsigned seed,type,index,flags24,flags25,own,template_count,descriptor_count;
    while(std::cin>>seed>>type>>index>>flags24>>flags25>>own>>template_count>>descriptor_count) {
        if(seed>65535 || type>65535 || index>65535 || flags24>255 || flags25>255 || own>65535 || template_count>256 || descriptor_count>256)return 2;
        M::Record record{};for(unsigned j=0;j<record.size();++j)record[j]=static_cast<uint8_t>(j*31u+17u);
        put(record,0,type);put(record,8,index);put(record,14,own);record[24]=static_cast<uint8_t>(flags24);record[25]=static_cast<uint8_t>(flags25);
        M::Templates templates(template_count);M::Descriptors descriptors(descriptor_count);
        for(unsigned i=0;i<templates.size();++i) {
            for(unsigned j=0;j<templates[i].size();++j)templates[i][j]=static_cast<uint8_t>(i*17u+j*31u);
            put(templates[i],14,i*307u+seed);
        }
        for(unsigned i=0;i<descriptors.size();++i) {
            for(unsigned j=0;j<descriptors[i].size();++j)descriptors[i][j]=static_cast<uint8_t>(i*13u+j*29u);
            put(descriptors[i],10,i*127u+seed*3u);
        }
        std::cout<<M::select(record,templates,descriptors)<<'\n';
    }
    return std::cin.eof()?0:2;
}
