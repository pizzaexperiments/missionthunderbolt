#include "engine/child_record_word_selector_model.hpp"
#include <cassert>
#include <cstdint>
#include <stdexcept>

namespace {
using Model=mt::ChildRecordWordSelectorModel;
template<std::size_t N>
void put(std::array<uint8_t,N>& record,unsigned offset,uint16_t value) {
    record[offset]=static_cast<uint8_t>(value>>8);
    record[offset+1]=static_cast<uint8_t>(value);
}
Model::Record authored(uint16_t type) {
    Model::Record record{};
    for(unsigned i=0;i<record.size();++i)record[i]=static_cast<uint8_t>(i*13u+9u);
    put(record,0,type);record[24]=0;record[25]=0;return record;
}
void checkPlainAllTypes() {
    // Every raw type can use its own word except the unconditional descriptor
    // branch. Special template branches are inactive when word 8 is zero.
    for(unsigned type=0;type<65536;++type) {
        if(type==107)continue;
        auto record=authored(static_cast<uint16_t>(type));put(record,8,0);
        const auto expected=static_cast<uint16_t>(type*313u+0x8021u);put(record,14,expected);
        const auto before=record;
        assert(Model::select(record,{}, {})==expected);
        assert(record==before);
    }
}
void checkTemplateAndSpecialPaths() {
    Model::Templates templates(121);
    for(unsigned type=0;type<templates.size();++type)put(templates[type],14,static_cast<uint16_t>(type*701u));
    const Model::Descriptors descriptors{};
    for(unsigned type=0;type<templates.size();++type) {
        if(type==107)continue;
        for(unsigned flags=0;flags<4;++flags) {
            auto record=authored(static_cast<uint16_t>(type));put(record,8,0);put(record,14,0xa35e);
            record[24]=(flags&1u)?2u:0u;record[25]=(flags&2u)?2u:0u;
            const auto original_record=record;const auto original_templates=templates;
            const auto expected=flags?static_cast<uint16_t>(type*701u):uint16_t(0xa35e);
            assert(Model::select(record,templates,descriptors)==expected);
            assert(record==original_record && templates==original_templates);
        }
    }
    for(const unsigned type:{68u,119u})for(const uint16_t count:{uint16_t(1),uint16_t(0x8000),uint16_t(0xffff)}) {
        auto record=authored(static_cast<uint16_t>(type));put(record,8,count);
        for(const uint16_t value:{uint16_t(0),uint16_t(0x7fff),uint16_t(0xffff)}) {
            put(templates[type],14,value);
            assert(Model::select(record,templates,descriptors)==static_cast<uint16_t>(value+1u));
        }
    }
}
void checkDescriptorPrecedence() {
    Model::Descriptors descriptors(8);
    for(unsigned i=0;i<descriptors.size();++i)put(descriptors[i],10,static_cast<uint16_t>(0xf113u+i));
    const auto before=descriptors;
    for(unsigned i=0;i<descriptors.size();++i) {
        auto record=authored(107);put(record,8,static_cast<uint16_t>(i));
        record[24]=record[25]=2;
        assert(Model::select(record,{},descriptors)==static_cast<uint16_t>(0xf113u+i));
    }
    assert(descriptors==before);
}
void checkAccessedTableBoundsAndImmutability() {
    Model::Templates templates(119);Model::Descriptors descriptors(3);
    const auto original_templates=templates;const auto original_descriptors=descriptors;
    for(const uint16_t index:{uint16_t(3),uint16_t(0x8000),uint16_t(0xffff)}) {
        auto record=authored(107);put(record,8,index);const auto before=record;
        bool threw=false;
        try {static_cast<void>(Model::select(record,templates,descriptors));}
        catch(const std::out_of_range&) {threw=true;}
        assert(threw && record==before);
    }
    for(const uint16_t type:{uint16_t(119),uint16_t(0x8000),uint16_t(0xffff)}) {
        auto record=authored(type);put(record,8,0);record[25]=2;const auto before=record;
        bool threw=false;
        try {static_cast<void>(Model::select(record,templates,descriptors));}
        catch(const std::out_of_range&) {threw=true;}
        assert(threw && record==before);
    }
    auto special=authored(119);put(special,8,1);
    bool threw=false;
    try {static_cast<void>(Model::select(special,templates,descriptors));}
    catch(const std::out_of_range&) {threw=true;}
    assert(threw);
    assert(templates==original_templates && descriptors==original_descriptors);
}
}
int main() {
    checkPlainAllTypes();checkTemplateAndSpecialPaths();checkDescriptorPrecedence();
    checkAccessedTableBoundsAndImmutability();
}
