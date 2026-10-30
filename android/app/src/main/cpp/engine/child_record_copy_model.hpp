#pragma once
#include <array>
#include <cstdint>

namespace mt {
// Research-only supplied-allocation CODE 9 copy, 0x5290 through RTS 0x52b0.
// Allocation/ownership and historical pointer semantics are not implemented.
class ChildRecordCopyModel {
public:
    using Record=std::array<uint8_t,56>;
    static void copy(Record& output,const Record& source) {
        // Distinct records and exact same-object aliasing are supported.
        // Partial overlap between different record objects is outside the contract.
        auto staged=source;
        for(unsigned offset=26;offset<34;++offset)staged[offset]=0;
        output=staged;
    }
};
}
