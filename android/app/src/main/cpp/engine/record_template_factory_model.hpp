#pragma once
#include "record_factory_tail_model.hpp"
#include <utility>

namespace mt {
// Partial CODE 9 factory: supplied allocation, no child creation, selected pure
// type branches, stop before final callback. Template data is caller-owned.
class RecordTemplateFactoryModel {
public:
    using Record=RecordFactoryTailModel::Record;
    using Templates=std::array<Record,76>;
    using DescriptorFlags=std::array<uint8_t,76>;
    struct Context {int variant,level;uint8_t flag39,tail_global;int mode=0;};
    struct Result {unsigned selected_template;bool requires_followup;RecordFactoryTailModel::Result tail;};
    static bool supported(int variant) {
        if(variant<0 || variant>32767)return false;
        if(variant>=89)return true;
        switch(variant) {
        case 0:case 1:case 2:case 3:case 4:case 5:case 7:case 10:case 12:case 13:case 14:case 15:case 16:
        case 18:case 19:case 20:case 21:case 22:case 23:case 25:case 27:case 28:case 29:case 31:
        case 32:case 33:case 34:case 35:case 37:case 38:case 39:case 41:case 44:case 46:case 47:
        case 50:case 51:case 52:case 53:case 54:case 55:case 56:case 58:case 62:case 63:case 64:
        case 65:case 66:case 68:case 69:case 70:case 71:case 73:case 76:case 77:case 78:case 79:
        case 80:case 81:case 82:case 83:case 84:case 85:case 86:case 87:case 88:return true;
        default:return false;
        }
    }
    static unsigned templateIndex(int variant) {
        if(variant<0 || variant>32767)throw std::invalid_argument("variant must fit nonnegative word");
        return variant<=75?static_cast<unsigned>(variant):0u;
    }
    static Result prepare(Record& output,const Templates& templates,const DescriptorFlags& descriptors,
                          const Context& c,ShuffledLcgModel& rng) {
        if(!supported(c.variant))throw std::invalid_argument("unmodeled factory variant");
        if(c.level < -32768 || c.level > 32767)throw std::invalid_argument("level must fit word");
        if(c.mode < -32768 || c.mode > 32767)throw std::invalid_argument("mode must fit word");
        const unsigned index=templateIndex(c.variant);
        Record record=templates[index];
        const unsigned kind=(record[0]<<8)|record[1];
        if(kind>=templates.size())throw std::out_of_range("factory template type");
        if(descriptors[kind])throw std::invalid_argument("unmodeled child creation");
        const bool followup=(templates[kind][20]&32)!=0;
        record[20]&=static_cast<uint8_t>(~32u);
        auto add_word=[&](int delta) {
            const auto value=static_cast<uint16_t>(((record[14]<<8)|record[15])+delta);
            record[14]=static_cast<uint8_t>(value>>8);record[15]=static_cast<uint8_t>(value);
        };
        switch(c.variant) {
        case 7:
            if(c.mode>2) {
                record[2]=static_cast<uint8_t>(record[2]+33);
                const auto value=static_cast<uint16_t>(((record[14]<<8)|record[15])*80);
                record[14]=static_cast<uint8_t>(value>>8);record[15]=static_cast<uint8_t>(value);
                record[8]=static_cast<uint8_t>(record[8]-67);
                const uint32_t old=(uint32_t(record[4])<<24)|(uint32_t(record[5])<<16)|(uint32_t(record[6])<<8)|record[7];
                const auto product=static_cast<uint32_t>(uint64_t(old)*1250u);
                for(unsigned i=0;i<4;++i)record[4+i]=static_cast<uint8_t>(product>>(24-8*i));
            }
            [[fallthrough]];
        case 79:record[21]|=8;break;
        case 31:record[26]|=1;add_word(10*c.level);record[21]|=128;break;
        case 39:if(c.flag39)record[21]|=128;break;
        case 65: {
            record[21]|=8;record[2]=static_cast<uint8_t>(record[2]+c.level);add_word(20*c.level);
            record[8]=static_cast<uint8_t>(record[8]-c.level);record[9]=static_cast<uint8_t>(record[9]+c.level);
            const uint16_t product=static_cast<uint16_t>(100*c.level);
            const int delta=product<32768?int(product):int(product)-65536;
            const uint32_t value=(uint32_t(record[4])<<24)|(uint32_t(record[5])<<16)|(uint32_t(record[6])<<8)|record[7];
            const auto sum=static_cast<uint32_t>(int64_t(value)+delta);
            for(unsigned i=0;i<4;++i)record[4+i]=static_cast<uint8_t>(sum>>(24-8*i));
            break;
        }
        case 35:case 46:record[8]=static_cast<uint8_t>(record[8]-c.level/5);[[fallthrough]];
        case 0:case 18:case 20:case 21:case 23:case 33:case 86:case 88:record[21]|=16;break;
        case 87:record[18]=15;record[21]|=16;record[26]|=192;break;
        case 38:add_word(c.level>=0?c.level/2:-((-c.level+1)/2));break;
        default:break;
        }
        auto tail=RecordFactoryTailModel::apply(record,c.tail_global,rng);
        output=record;return {index,followup,std::move(tail)};
    }
};
}
