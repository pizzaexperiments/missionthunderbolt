#include "engine/record_followup_model.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using M=mt::RecordFollowupModel;
static std::string decode(const std::string& h) {
    auto n=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("hex");};
    if(h.size()%2)throw std::invalid_argument("hex size");
    std::string b;for(unsigned i=0;i<h.size();i+=2)b.push_back(static_cast<char>((n(h[i])<<4)|n(h[i+1])));return b;
}
int main() {
    std::string parent,flags,thresholds;unsigned count;
    while(std::cin>>parent>>flags>>thresholds>>count) {
        auto p=decode(parent),f=decode(flags),t=decode(thresholds);
        if(p.size()!=112 || f.size()!=76 || t.size()!=512 || count>13)return 2;
        M::Record record;M::Context c;
        for(unsigned i=0;i<112;++i)record[i]=static_cast<uint8_t>(p[i]);
        for(unsigned i=0;i<76;++i)c.template_flags[i]=static_cast<uint8_t>(f[i]);
        for(unsigned i=0;i<256;++i) {unsigned w=(uint8_t(t[2*i])<<8)|uint8_t(t[2*i+1]);c.thresholds[i]=static_cast<int16_t>(w<32768?int(w):int(w)-65536);}
        M::Children children;
        for(unsigned i=0;i<count;++i) {uint32_t id;std::string text;if(!(std::cin>>id>>text))return 2;const auto b=decode(text);if(b.size()!=32)return 2;
            M::Child child;for(unsigned j=0;j<32;++j)child[j]=static_cast<uint8_t>(b[j]);children.emplace(id,child);}
        const auto before=children;M::apply(record,children,c);if(children!=before)return 3;
        std::cout<<std::hex<<std::setfill('0');for(auto b:record)std::cout<<std::setw(2)<<unsigned(b);std::cout<<std::dec<<'\n';
    }
    return std::cin.eof()?0:2;
}
