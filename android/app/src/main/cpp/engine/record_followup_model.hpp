#pragma once
#include "record_factory_tail_model.hpp"
#include <map>

namespace mt {
// CODE 7 entry 9972: raw child-record selection, not inventory/equipment semantics.
class RecordFollowupModel {
public:
    using Record=RecordFactoryTailModel::Record;
    using Child=std::array<uint8_t,32>;
    using Children=std::map<uint32_t,Child>;
    struct Context {std::array<uint8_t,76> template_flags;std::array<int16_t,256> thresholds;};
    static unsigned kind(const Record& r) {return (r[0]<<8)|r[1];}
    static uint32_t slot(const Record& r,unsigned i) {
        if(i>=13)throw std::out_of_range("child slot");
        const unsigned p=60+4*i;
        return (uint32_t(r[p])<<24)|(uint32_t(r[p+1])<<16)|(uint32_t(r[p+2])<<8)|r[p+3];
    }
    static void validate(const Record& r,const Children& children,const Context& c) {
        if(kind(r)>=c.template_flags.size())throw std::out_of_range("record type outside supplied table");
        if(r[51]>13)throw std::out_of_range("child count outside supplied record");
        if(kind(r)==72 || (c.template_flags[kind(r)]&32))
            for(unsigned i=0;i<r[51];++i)if(slot(r,i)==0 || children.find(slot(r,i))==children.end())
                throw std::invalid_argument("missing supplied child");
    }
    static void apply(Record& r,const Children& children,const Context& c) {
        validate(r,children,c);
        auto signed_word=[](const Child& child,unsigned p) {
            const unsigned word=(child[p]<<8)|child[p+1];return word<32768?int(word):int(word)-65536;
        };
        if(kind(r)==72)for(unsigned n=r[51];n>0;--n) {
            const auto& child=children.at(slot(r,n-1));
            if(child[18] && signed_word(child,8)>c.thresholds[r[18]]) {r[18]=child[1];break;}
        }
        r[22]=0;r[20]&=static_cast<uint8_t>(~32u);
        if(!(c.template_flags[kind(r)]&32))return;
        int best=0;
        for(unsigned n=r[51];n>0;--n) {
            const auto& child=children.at(slot(r,n-1));const int score=signed_word(child,16);
            if(score<=1 || (child[24]&2) || (child[25]&2) || signed_word(child,8)!=0 || (child[24]&8))continue;
            if(score>best) {best=score;r[22]=static_cast<uint8_t>(n-1);}
        }
        if(best)r[20]|=32;
    }
};
}
