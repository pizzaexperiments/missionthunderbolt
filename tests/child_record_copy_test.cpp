#include "engine/child_record_copy_model.hpp"
#include <array>
#include <cassert>
#include <cstdint>

namespace {
using Model=mt::ChildRecordCopyModel;
struct Guarded {
    std::array<uint8_t,16> before;
    Model::Record record;
    std::array<uint8_t,16> after;
};
void check(unsigned seed,bool alias) {
    Guarded source{},destination{};
    source.before.fill(0xa6);source.after.fill(0x6a);
    destination.before.fill(0xc3);destination.after.fill(0x3c);
    for(unsigned i=0;i<56;++i) {
        source.record[i]=static_cast<uint8_t>(seed*17u+i*31u);
        destination.record[i]=static_cast<uint8_t>(seed*29u+i*13u);
    }
    const auto original_source=source;
    const auto original_destination=destination;
    auto& output=alias?source.record:destination.record;
    Model::copy(output,source.record);
    for(unsigned i=0;i<56;++i)assert(output[i]==(i>=26 && i<34?0:original_source.record[i]));
    assert(source.before==original_source.before && source.after==original_source.after);
    assert(destination.before==original_destination.before && destination.after==original_destination.after);
    if(alias)assert(destination.record==original_destination.record);
    else assert(source.record==original_source.record);
}
}
int main() {
    for(unsigned seed=0;seed<256;++seed) {check(seed,false);check(seed,true);}
    Model::Record source{},output{};
    source.fill(0xff);Model::copy(output,source);
    for(unsigned i=0;i<56;++i)assert(output[i]==(i>=26 && i<34?0:0xff));
    Model::copy(output,output);
    for(unsigned i=0;i<56;++i)assert(output[i]==(i>=26 && i<34?0:0xff));
}
