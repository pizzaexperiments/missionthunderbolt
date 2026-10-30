#pragma once
#include "child_record_prefix_model.hpp"

namespace mt {
// Research-only supplied-allocation CODE 9 body, 0x484e..0x4cd8. Selected
// dispatch cases needing recursion, external helpers or globals are rejected.
// No original table contents, allocator, caller ABI or gameplay is supplied.
class ChildRecordFactoryModel {
public:
    using Record=ChildRecordPrefixModel::Record;
    using Templates=ChildRecordPrefixModel::Templates;
    using Draw=ChildRecordPrefixModel::Draw;
    using Result=ChildRecordPrefixModel::Result;
    static bool supportsType(unsigned type) {
        if(type>65535u)return false;
        switch(type) {
        case 36:case 37:case 70:case 77:case 137:case 138:case 166:return false;
        default:return true;
        }
    }
    static Result prepare(Record& output,const Templates& templates,int variant,int level,ShuffledLcgModel& rng) {
        if(variant<0 || variant>32767)throw std::invalid_argument("variant must fit nonnegative word");
        if(level < -32768 || level>32767)throw std::invalid_argument("level must fit signed word");
        const auto selected=variant<=136?static_cast<unsigned>(variant):0u;
        const auto& source=templates[selected];
        const unsigned type=(unsigned(source[0])<<8)|source[1];
        if(!supportsType(type))throw std::invalid_argument("unmodeled child-record dispatch type");
        auto staged_rng=rng;Record record{};
        auto result=ChildRecordPrefixModel::prepare(record,templates,variant,staged_rng);
        result.draws.reserve(10);
        auto word=[&](unsigned p) {return (unsigned(record[p])<<8)|record[p+1];};
        auto put=[&](unsigned p,unsigned value) {
            record[p]=static_cast<uint8_t>(value>>8);record[p+1]=static_cast<uint8_t>(value);
        };
        auto signed_word=[](unsigned value) {return value<32768?int(value):int(value)-65536;};
        auto draw=[&](int bound,bool one_based) {
            const auto value=one_based?staged_rng.oneBased(bound):staged_rng.zeroBased(bound);
            result.draws.push_back({static_cast<uint16_t>(bound),one_based?1u:0u,value});return value;
        };
        switch(type) {
        case 25: {
            const int quotient=level/5;
            if(quotient<0 || quotient>2)put(8,33);
            else if(quotient==2) {
                record[6]=static_cast<uint8_t>(record[6]-4u);put(8,2);
            } else {
                record[6]=static_cast<uint8_t>(record[6]-7u);put(8,13);
            }
            break;
        }
        case 39:put(22,draw(200,true));break;
        case 63:put(8,draw(5,true));break;
        case 62: {
            const auto value=static_cast<uint16_t>(draw(11,false)+static_cast<uint16_t>(level)-5u);
            const int signed_value=signed_word(value);
            put(8,signed_value<0?draw(5,false):(signed_value>=15?0u:value));break;
        }
        case 81:case 141:put(14,word(14)+draw(20,true));break;
        case 109:put(14,word(14)+draw(10,true));break;
        case 108:put(14,word(14)+draw(5,true));break;
        case 100:put(8,draw(50,false));break;
        case 114:case 116:put(22,draw(signed_word(word(22)),true));break;
        case 93:case 94:case 95:case 96:case 97:case 98:case 101:
            record[25]|=4;break;
        case 127: {
            const auto value=draw(5,false);put(22,value);
            // The original byte offset 0x93e is slot 42, word +14.
            const unsigned factor=(unsigned(templates[42][14])<<8)|templates[42][15];
            put(14,word(14)+factor*value);break;
        }
        case 129:record[2]=draw(4,false)!=0?1:2;break;
        case 140:case 164:case 165:case 167:record[24]|=8;break;
        case 144:record[13]=3;break;
        case 143:record[25]|=4;break;
        default:break; // All other word types select the table/default no-op.
        }
        output=record;rng=std::move(staged_rng);return result;
    }
};
}
