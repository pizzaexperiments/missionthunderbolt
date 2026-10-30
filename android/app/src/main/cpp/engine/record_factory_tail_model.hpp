#pragma once
#include "shuffled_lcg_model.hpp"
#include <vector>

namespace mt {
// Bounded CODE 9 factory tail, before template lookup/optional callback.
// Supplied bytes do not imply recovered record-type or gameplay semantics.
class RecordFactoryTailModel {
public:
    using Record=std::array<uint8_t,112>;
    using Draw=std::array<uint32_t,3>; // raw bound word, one-based, result
    struct Result {bool took_zero_path=false;std::vector<Draw> draws;};
    static Result apply(Record& record,uint8_t global_byte,ShuffledLcgModel& rng) {
        Result result;result.draws.reserve(8);
        auto signed_byte=[](uint8_t b){return b<128?int(b):int(b)-256;};
        auto half=[](int64_t value){return value>=0?value/2:-((-value+1)/2);};
        auto word=[&](unsigned p){return static_cast<uint16_t>((record[p]<<8)|record[p+1]);};
        auto put_word=[&](unsigned p,uint16_t value){record[p]=static_cast<uint8_t>(value>>8);record[p+1]=static_cast<uint8_t>(value);};
        auto draw=[&](int bound,bool one) {
            const auto value=one?rng.oneBased(bound):rng.zeroBased(bound);
            result.draws.push_back({static_cast<uint16_t>(bound),one?1u:0u,value});return value;
        };
        if(draw(100,false)==0) {
            result.took_zero_path=true;
            const int bound=static_cast<int>(half(signed_byte(global_byte)))+1;
            record[2]=static_cast<uint8_t>(record[2]+draw(bound,true));
            const auto raw=word(14);const int signed_word=raw<32768?int(raw):int(raw)-65536;
            put_word(14,static_cast<uint16_t>(raw+draw(signed_word,true)));
            record[8]=static_cast<uint8_t>(record[8]-draw(bound,true));
            for(unsigned p:{13u,10u,11u})record[p]=static_cast<uint8_t>(record[p]+draw(10,true));
            const int byte_bound=static_cast<int>(half(signed_byte(record[9])))+1;
            record[9]=static_cast<uint8_t>(record[9]+draw(byte_bound,true));
            const uint32_t bits=(uint32_t(record[4])<<24)|(uint32_t(record[5])<<16)|(uint32_t(record[6])<<8)|record[7];
            const int64_t signed_long=bits<0x80000000u?int64_t(bits):int64_t(bits)-0x100000000LL;
            const auto adjusted=static_cast<uint32_t>(signed_long+half(signed_long));
            for(unsigned n=0;n<4;++n)record[4+n]=static_cast<uint8_t>(adjusted>>(24-8*n));
        }
        put_word(16,word(14));return result;
    }
};
}
