#include "engine/grid_record_layout.hpp"
#include <cassert>
#include <climits>
#include <set>
int main() {
    using Layout=mt::GridRecordLayout;
    // Frozen corner offsets from the independently executed original pointer builder.
    assert(Layout::offset(0,0)==104u);
    assert(Layout::offset(66,0)==1424u);
    assert(Layout::offset(0,18)==24224u);
    assert(Layout::offset(66,18)==25544u);
    assert(Layout::end_offset==25564u);
    assert(Layout::address32(0xfffffff0u,0,0)==88u);
    std::set<uint32_t> addresses;
    for(int y=0;y<Layout::rows;++y)for(int x=0;x<Layout::columns;++x) {
        auto offset=Layout::offset(x,y);
        assert(offset>=Layout::header_bytes && offset+Layout::record_bytes<=Layout::end_offset);
        assert(addresses.insert(offset).second);
    }
    assert(addresses.size()==1273);
    auto low=Layout::clampSignedBytes(-128,-128);
    auto high=Layout::clampSignedBytes(127,127);
    auto edge=Layout::clampSignedBytes(66,18);
    assert(low.column==0 && low.row==0);
    assert(high.column==66 && high.row==18);
    assert(edge.column==66 && edge.row==18);
    for(int invalid : {INT_MIN,-129,128,INT_MAX}) {
        bool rejected=false;try {Layout::clampSignedBytes(invalid,0);} catch(const std::out_of_range&) {rejected=true;}
        assert(rejected);
        rejected=false;try {Layout::clampSignedBytes(0,invalid);} catch(const std::out_of_range&) {rejected=true;}
        assert(rejected);
    }
    // Frozen rejection bitmap independently checked at both original selector gates.
    constexpr uint64_t rejected_kinds=0x472400006ull;
    for(unsigned kind=0;kind<256;++kind) {
        const bool accepted=kind>=64 || ((rejected_kinds>>kind)&1u)==0;
        assert(Layout::selectionCandidate(static_cast<uint8_t>(kind),0)==accepted);
        for(uint32_t field16 : {1u,0x80000000u,0xffffffffu})
            assert(!Layout::selectionCandidate(static_cast<uint8_t>(kind),field16));
    }
    for(int x : {INT_MIN,-1,67,INT_MAX}) {
        bool rejected=false;try {Layout::offset(x,0);} catch(const std::out_of_range&) {rejected=true;}
        assert(rejected);
    }
    for(int y : {INT_MIN,-1,19,INT_MAX}) {
        bool rejected=false;try {Layout::offset(0,y);} catch(const std::out_of_range&) {rejected=true;}
        assert(rejected);
    }
}
