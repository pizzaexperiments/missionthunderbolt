#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace mt {
// Research-only CODE 9 raw-word selector, entry 0x71b2 through RTS 0x722c.
// Caller supplies both tables; no historical bytes or gameplay meaning supplied.
class ChildRecordWordSelectorModel {
public:
    using Record=std::array<uint8_t,56>;
    using Descriptor=std::array<uint8_t,12>;
    using Templates=std::vector<Record>;
    using Descriptors=std::vector<Descriptor>;

    // Only a table that the selected branch actually reads needs an entry.
    // Return is the low word; original D0 upper bits are outside this contract.
    static uint16_t select(const Record& record,const Templates& templates,const Descriptors& descriptors) {
        const int type=signedWord(word(record,0));
        if(type==107) {
            const int index=signedWord(word(record,8));
            if(index<0 || static_cast<std::size_t>(index)>=descriptors.size())
                throw std::out_of_range("descriptor index outside supplied table");
            return word(descriptors[static_cast<std::size_t>(index)],10);
        }
        const bool increment=(type==68 || type==119) && word(record,8)!=0;
        if(increment || (record[24]&2u)!=0 || (record[25]&2u)!=0) {
            if(type<0 || static_cast<std::size_t>(type)>=templates.size())
                throw std::out_of_range("template index outside supplied table");
            return static_cast<uint16_t>(word(templates[static_cast<std::size_t>(type)],14)+(increment?1u:0u));
        }
        return word(record,14);
    }
private:
    template<std::size_t N>
    static uint16_t word(const std::array<uint8_t,N>& record,std::size_t offset) {
        return static_cast<uint16_t>((unsigned(record[offset])<<8)|record[offset+1]);
    }
    static int signedWord(uint16_t value) {return value<32768?int(value):int(value)-65536;}
};
}
