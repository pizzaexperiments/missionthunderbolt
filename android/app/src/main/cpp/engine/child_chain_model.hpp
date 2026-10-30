#pragma once
#include "child_record_factory_model.hpp"
#include <array>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace mt {
// Research-only CODE 9 helper 0x4e00..0x4eca with an empty old parent +30.
// Five allocations are supplied. Allocation, release and ownership are absent.
class ChildChainModel {
public:
    using Factory=ChildRecordFactoryModel;
    using Record=Factory::Record;
    using Templates=Factory::Templates;
    using Records=std::array<Record,5>;
    using Handles=std::array<uint32_t,5>;
    using Context=Factory::Context;
    using Draw=Factory::Draw;
    struct Result {
        std::vector<Draw> draws;
        std::array<unsigned,5> factory_draw_counts{};
    };
    static Result prepare(Record& parent,uint32_t parent_handle,Records& children,
                          const Handles& handles,const Templates& templates,
                          ShuffledLcgModel& rng,Context& context) {
        constexpr std::array<unsigned,5> variants{{31,27,28,37,72}};
        constexpr std::array<unsigned,5> bounds{{200,50,50,200,25}};
        constexpr std::array<unsigned,5> biases{{200,25,25,100,25}};
        if(longWord(parent,30)!=0)throw std::invalid_argument("old parent branch must be empty");
        std::array<uint32_t,6> addresses{{parent_handle,handles[0],handles[1],handles[2],handles[3],handles[4]}};
        for(unsigned i=0;i<addresses.size();++i) {
            const uint64_t start=addresses[i];
            if(start==0 || (start&1u)!=0 || start+56u>uint64_t(0x100000000ULL))
                throw std::invalid_argument("invalid supplied record handle");
            for(unsigned j=0;j<i;++j)
                if(start<uint64_t(addresses[j])+56u && uint64_t(addresses[j])<start+56u)
                    throw std::invalid_argument("supplied record handle ranges overlap");
        }
        for(const auto& child:children)
            if(&child==&parent)throw std::invalid_argument("parent aliases supplied child storage");
        for(const auto& source:templates) {
            if(&source==&parent)throw std::invalid_argument("parent aliases supplied template");
            for(const auto& child:children)
                if(&source==&child)throw std::invalid_argument("child aliases supplied template");
        }
        for(const auto variant:variants) {
            const unsigned type=(unsigned(templates[variant][0])<<8)|templates[variant][1];
            if(!Factory::supportsType(type,true))throw std::invalid_argument("unsupported nested child dispatch");
        }
        auto staged_parent=parent;auto staged_children=children;
        auto staged_rng=rng;auto staged_context=context;
        Result result;result.draws.reserve(60);
        for(unsigned i=0;i<5;++i) {
            const auto factory=Factory::prepare(staged_children[i],templates,static_cast<int>(variants[i]),
                                                1,staged_rng,staged_context);
            result.factory_draw_counts[i]=static_cast<unsigned>(factory.draws.size());
            result.draws.insert(result.draws.end(),factory.draws.begin(),factory.draws.end());
            if(i==0)putLong(staged_parent,30,handles[0]);
            else putLong(staged_children[i-1],26,handles[i]);
            const auto value=staged_rng.oneBased(static_cast<int>(bounds[i]));
            result.draws.push_back({bounds[i],1u,value});
            putWord(staged_children[i],10,static_cast<uint16_t>(value+biases[i]));
        }
        parent=staged_parent;children=staged_children;rng=std::move(staged_rng);context=staged_context;
        return result;
    }
private:
    static uint32_t longWord(const Record& record,unsigned offset) {
        return (uint32_t(record[offset])<<24)|(uint32_t(record[offset+1])<<16)
               |(uint32_t(record[offset+2])<<8)|record[offset+3];
    }
    static void putWord(Record& record,unsigned offset,uint16_t value) {
        record[offset]=static_cast<uint8_t>(value>>8);record[offset+1]=static_cast<uint8_t>(value);
    }
    static void putLong(Record& record,unsigned offset,uint32_t value) {
        for(unsigned i=0;i<4;++i)record[offset+i]=static_cast<uint8_t>(value>>(24u-i*8u));
    }
};
}
