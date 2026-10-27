#include "engine/record_release_model.hpp"
#include "engine/linked_record_model.hpp"
#include <cassert>
using M=mt::RecordReleaseModel;
struct Services : mt::GridFallbackSelector::Services {
    mt::GridFallbackSelector::Grid& grid;
    mt::LinkedRecordModel::Header header{1,3};
    mt::LinkedRecordModel::Nodes links{{3,{16,3,0}}};
    M::Nodes nodes{{1,{0,0}},{2,{0,0}}};M::Parent parent;
    uint16_t query_word=1;uint32_t query_field=0;
    std::vector<uint32_t> disposed;
    explicit Services(mt::GridFallbackSelector::Grid& cells):grid(cells) {
        parent.count51=1;parent.slots60[0]=2;parent.field52=4;
    }
    mt::GridFallbackSelector::Link16 read16(uint32_t id) override {assert(id==1 || id==2);return {1,0};}
    mt::GridFallbackSelector::Link12 read12(uint32_t id) override {assert(id==3);return {1,parent.count51,{2}};}
    uint16_t query16(uint32_t id) override {assert(id==1);return mt::LinkedRecordModel::query16(query_word,query_field);}
    void release16(uint32_t id) override {
        const auto result=M::release16(nodes,id,128,[&](uint32_t ref){disposed.push_back(ref);});
        assert(result.status==M::Status::complete);
    }
    void unlink12(uint32_t,uint32_t id) override {
        const auto result=mt::LinkedRecordModel::unlink12(header,grid,links,id,128);
        assert(result.status==mt::LinkedRecordModel::Status::unlinked);
    }
    void release12(uint32_t id) override {
        const auto result=M::release12(nodes,parent,id,128,[&](uint32_t ref){disposed.push_back(ref);});
        assert(result.status==M::Status::complete);
    }
};
int main() {
    uint16_t prefix=0xffff;std::vector<uint32_t> freed;
    M::releasePrefix(0,prefix,[&](uint32_t ref){freed.push_back(ref);});
    assert(prefix==0xffff && freed.empty());
    M::releasePrefix(0xb0002,prefix,[&](uint32_t ref){freed.push_back(ref);});
    assert(prefix==0 && (freed==std::vector<uint32_t>{0xb0000}));
    prefix=0x1234;freed.clear();
    M::releasePrefix(0xb0002,prefix,[&](uint32_t ref){freed.push_back(ref);});
    assert(prefix==0xedcb && freed.empty());
    // Authored two-chain/nested shape also executed by the original oracle.
    M::Nodes nodes{{1,{2,3}},{2,{0,4}},{3,{0,0}},{4,{0,0}}};
    std::vector<uint32_t> events;
    auto result=M::release16(nodes,1,32,[&](uint32_t id) {
        if(id==4)assert(nodes.at(1).next26==2 && nodes.at(2).branch30==4);
        if(id==2)assert(nodes.at(2).branch30==0);
        events.push_back(id);
    });
    assert(result.status==M::Status::complete && result.steps==5);
    assert((events==std::vector<uint32_t>{4,2,3,1}));
    for(const auto& entry:nodes)assert(entry.second.next26==0 && entry.second.branch30==0);
    nodes={{1,{2,0}},{2,{3,4}},{3,{0,0}},{4,{0,0}}};events.clear();
    result=M::release16(nodes,1,2,[&](uint32_t id){events.push_back(id);});
    assert(result.status==M::Status::budget_exhausted && result.steps==2 && events.empty());
    assert(nodes.at(1).next26==2 && nodes.at(2).next26==0 && nodes.at(2).branch30==4);
    // A self-child cycle uses bounded explicit frames, not the host call stack.
    nodes={{1,{0,1}}};
    result=M::release16(nodes,1,64,[&](uint32_t){assert(false);});
    assert(result.status==M::Status::budget_exhausted && result.steps==64 && nodes.at(1).branch30==1);
    nodes={{1,{0,0}},{2,{0,0}}};M::Parent parent;parent.count51=2;parent.field52=9;
    parent.slots60[0]=1;parent.slots60[1]=2;parent.slots60[126]=77;events.clear();
    std::vector<uint32_t> entries;
    result=M::release12(nodes,parent,10,32,[&](uint32_t id) {
        if(id==2)assert(parent.count51==1 && parent.slots60[1]==2);
        if(id==1)assert(parent.count51==0 && parent.slots60[1]==0 && parent.slots60[0]==1);
        events.push_back(id);
    },[&](uint32_t id) {
        assert(parent.count51==(id==2?1:0));
        assert(parent.slots60[parent.count51]==id);entries.push_back(id);
    });
    assert(result.status==M::Status::complete && result.steps==5);
    assert((events==std::vector<uint32_t>{2,1,9,10}));
    assert((entries==std::vector<uint32_t>{2,1}));
    assert(parent.count51==0 && parent.field52==9 && parent.slots60[0]==0 && parent.slots60[1]==0 && parent.slots60[126]==77);
    parent.count51=2;parent.slots60[0]=1;parent.slots60[1]=2;events.clear();
    result=M::release12(nodes,parent,10,2,[&](uint32_t id){events.push_back(id);});
    assert(result.status==M::Status::budget_exhausted && events.empty());
    assert(parent.count51==1 && parent.slots60[1]==2);
    parent.count51=128;
    try {M::release12(nodes,parent,10,32,[&](uint32_t){assert(false);});assert(false);}catch(const std::out_of_range&){}
    assert(parent.count51==128 && parent.slots60[1]==2);
    nodes.clear();result=M::release16(nodes,1,32,[&](uint32_t){assert(false);});
    assert(result.status==M::Status::missing_node && result.steps==1);
    // Native interface composition of filter/unlink/release models. Only the
    // final allocation-disposal endpoint remains an observation callback.
    for(uint8_t kind:{uint8_t(1),uint8_t(2)}) {
        mt::GridFallbackSelector::Grid grid{};for(auto& cell:grid)cell.bytes[0]=28;
        auto& cell=grid[16*67+3];cell.bytes[0]=kind;cell.bytes[4]=64;
        cell.setLong(16,1);cell.setLong(12,3);Services services(grid);
        auto rng=mt::ShuffledLcgModel::initialized(42,42,123);
        const auto selected=mt::GridFallbackSelector::select(grid,rng,services,0x90000,1);
        assert((services.disposed==std::vector<uint32_t>{1,2,4,3}));
        assert(cell.longAt(12)==0 && cell.longAt(16)==0 && services.header.count18==0 && services.header.head20==0);
        assert(services.parent.count51==0 && services.parent.slots60[0]==0 && services.parent.field52==4);
        assert(selected.phase==(kind==1?mt::GridFallbackSelector::Phase::random:mt::GridFallbackSelector::Phase::budget_exhausted));
    }
    mt::GridFallbackSelector::Grid grid{};for(auto& cell:grid)cell.bytes[0]=28;
    auto& cell=grid[16*67+3];cell.bytes[0]=0;cell.setLong(16,1);
    Services services(grid);services.query_word=70;
    auto rng=mt::ShuffledLcgModel::initialized(42,42,123);const auto before=rng.state();
    auto selected=mt::GridFallbackSelector::select(grid,rng,services,0x90000,0);
    assert(selected.phase==mt::GridFallbackSelector::Phase::budget_exhausted && services.disposed.empty());
    services.query_field=1;
    selected=mt::GridFallbackSelector::select(grid,rng,services,0x90000,0);
    assert(selected.phase==mt::GridFallbackSelector::Phase::second_scan && cell.longAt(16)==0);
    assert((services.disposed==std::vector<uint32_t>{1}));
    assert(rng.state().table==before.table && rng.state().selector_seed==before.selector_seed && rng.state().last_result==before.last_result);
}
