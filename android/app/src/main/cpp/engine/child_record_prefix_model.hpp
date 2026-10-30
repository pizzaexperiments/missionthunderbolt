#pragma once
#include "shuffled_lcg_model.hpp"
#include <utility>
#include <vector>

namespace mt {
// Research-only CODE 9 prefix, 0x484e..0x4974. Allocation is supplied;
// type dispatch, recursive child construction and finalization are not modeled.
class ChildRecordPrefixModel {
public:
    using Record=std::array<uint8_t,56>;
    using Templates=std::array<Record,137>;
    using Draw=std::array<uint32_t,3>; // bound, one-based flag, result
    struct Result {unsigned selected_template;std::vector<Draw> draws;};
    static Result prepare(Record& output,const Templates& templates,int variant,ShuffledLcgModel& rng) {
        if(variant<0 || variant>32767)throw std::invalid_argument("variant must fit nonnegative word");
        const unsigned index=variant<=136?static_cast<unsigned>(variant):0u;
        Record record=templates[index];auto staged_rng=rng;
        Result result{index,{}};result.draws.reserve(8);
        auto word=[&](unsigned p) {return (unsigned(record[p])<<8)|record[p+1];};
        auto put=[&](unsigned p,unsigned value) {
            record[p]=static_cast<uint8_t>(value>>8);record[p+1]=static_cast<uint8_t>(value);
        };
        auto signed_word=[](unsigned value) {return value<32768?int(value):int(value)-65536;};
        auto draw=[&](int bound,bool one_based) {
            const auto value=one_based?staged_rng.oneBased(bound):staged_rng.zeroBased(bound);
            result.draws.push_back({static_cast<uint32_t>(bound),one_based?1u:0u,value});return value;
        };
        const int count=signed_word(word(10));
        if(count>1) {
            const auto value=draw(count,true);put(10,value);
            put(14,static_cast<uint16_t>(word(14)*value));
        }
        if((record[24]&32)!=0 && record[6]!=0) {
            if((record[24]&2)==0 && word(0)!=71) {
                if(draw(20,false)==0)put(14,static_cast<uint16_t>(word(14)+draw(10,true)));
                else if(draw(20,false)==0) {
                    const auto value=static_cast<uint16_t>(word(14)-draw(10,true));
                    put(14,signed_word(value)<1?1u:value);
                }
            }
            if(draw(20,false)==0) {
                const auto delta=draw(10,false)!=0?1u:draw(3,true);
                record[6]=static_cast<uint8_t>(record[6]+delta);
            } else if(draw(20,false)==0) {
                const auto delta=draw(10,false)!=0?1u:draw(3,true);
                record[6]=static_cast<uint8_t>(record[6]-delta);
                if(record[6]>=128)record[6]=0;
            }
        }
        output=record;rng=std::move(staged_rng);return result;
    }
};
}
