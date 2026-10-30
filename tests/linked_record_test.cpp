#include "engine/linked_record_model.hpp"
#include <cassert>
using M=mt::LinkedRecordModel;
struct RecoveredServices : mt::GridFallbackSelector::Services {
    M::Header header{3,100};M::Nodes nodes{{100,{16,3,0}}};
    mt::GridFallbackSelector::Grid& grid;unsigned releases=0;
    explicit RecoveredServices(mt::GridFallbackSelector::Grid& cells):grid(cells){}
    mt::GridFallbackSelector::Link16 read16(uint32_t) override {return {1,0};}
    mt::GridFallbackSelector::Link12 read12(uint32_t ref) override {assert(ref==100);return {1,0,{}};}
    uint16_t query16(uint32_t) override {return M::query16(1,0);}
    void release16(uint32_t) override {assert(false);}
    void unlink12(uint32_t,uint32_t ref) override {
        const auto result=M::unlink12(header,grid,nodes,ref,1);
        assert(result.status==M::Status::unlinked);
    }
    void release12(uint32_t ref) override {assert(ref==100);++releases;}
};
int main() {
    {
        M::Header header{65535,0x2000};mt::GridFallbackSelector::Grid grid{};
        M::Nodes nodes{{0x1000,{9,10,0x3000}},{0x2000,{1,2,0}}};
        grid[18*67+66].setLong(12,0xdeadbeef);
        M::attach12(header,grid,nodes,0x1000,18,66);
        assert(header.count18==0 && header.head20==0x1000);
        assert(nodes.at(0x1000).row48==18 && nodes.at(0x1000).column49==66 && nodes.at(0x1000).next56==0x2000);
        assert(grid.back().longAt(12)==0x1000 && nodes.at(0x2000).next56==0);
        const auto removed=M::unlink12(header,grid,nodes,0x1000,0);
        assert(removed.status==M::Status::unlinked && header.count18==65535 && header.head20==0x2000);
        assert(grid.back().longAt(12)==0 && nodes.at(0x1000).next56==0); // Old cell link is not restored.
        M::attach12(header,grid,nodes,0x1000,0,0);M::attach12(header,grid,nodes,0x1000,0,0);
        assert(nodes.at(0x1000).next56==0x1000 && header.count18==1); // Original permits self-links.
        const auto before=header;const auto cell=grid[0].bytes;const auto node=nodes.at(0x1000);
        for(auto coordinate:std::array<std::array<int,2>,4>{{{-1,0},{19,0},{0,-1},{0,67}}}) {
            bool rejected=false;try {M::attach12(header,grid,nodes,0x1000,coordinate[0],coordinate[1]);}catch(const std::out_of_range&){rejected=true;}
            assert(rejected && header.count18==before.count18 && header.head20==before.head20 && grid[0].bytes==cell);
            assert(nodes.at(0x1000).next56==node.next56 && nodes.at(0x1000).row48==node.row48);
        }
        for(uint32_t target:{0u,0x9999u}) {
            bool rejected=false;try {M::attach12(header,grid,nodes,target,0,0);}catch(const std::invalid_argument&){rejected=true;}
            assert(rejected && header.count18==before.count18 && header.head20==before.head20 && grid[0].bytes==cell);
        }
    }

    // Frozen accepted values from the independently executed complete word sweep.
    const std::array<unsigned,18> accepted{0,29,30,56,57,58,65,66,67,68,69,81,107,108,109,119,141,175};
    for(unsigned word=0;word<65536;++word) {
        bool expected=false;for(auto value:accepted)if(word==value)expected=true;
        assert(M::query16(static_cast<uint16_t>(word),0)==expected);
        assert(M::query16(static_cast<uint16_t>(word),0xffffffff)==(expected || word==70));
    }
    mt::GridFallbackSelector::Grid grid{};M::Header header{0,100};
    M::Nodes nodes{{100,{1,2,200}},{200,{1,2,300}},{300,{1,2,0}}};
    grid[69].setLong(12,200);grid[69].setLong(16,0xabcdef01);
    auto result=M::unlink12(header,grid,nodes,200,1);
    assert(result.status==M::Status::unlinked && result.visits==1);
    assert(header.count18==65535 && header.head20==100 && nodes.at(100).next56==300);
    assert(nodes.at(200).next56==0 && grid[69].longAt(12)==0 && grid[69].longAt(16)==0xabcdef01);
    header={3,100};nodes.at(100).next56=100;nodes.at(200).next56=300;grid[69].setLong(12,200);
    result=M::unlink12(header,grid,nodes,200,7);
    assert(result.status==M::Status::budget_exhausted && result.visits==7);
    assert(header.count18==2 && grid[69].longAt(12)==0 && nodes.at(200).next56==300);
    header={1,200};result=M::unlink12(header,grid,nodes,200,0);
    assert(result.status==M::Status::unlinked && header.head20==300 && header.count18==0);
    header={2,999};result=M::unlink12(header,grid,nodes,300,2);
    assert(result.status==M::Status::missing_node && header.count18==1);
    nodes.at(300).row48=255;const auto old=header.count18;
    try {M::unlink12(header,grid,nodes,300,2);assert(false);}catch(const std::out_of_range&){}
    assert(header.count18==old);
    // Interface composition retains unlink effects even if the fallback later
    // rejects the candidate. Release/ownership remains a synthetic callback.
    for(uint8_t kind:{uint8_t(1),uint8_t(2)}) {
        for(auto& cell:grid)cell.bytes[0]=28;
        auto& cell=grid[16*67+3];cell.bytes.fill(0);cell.bytes[0]=kind;
        cell.bytes[4]=64;cell.setLong(12,100);
        RecoveredServices services(grid);auto rng=mt::ShuffledLcgModel::initialized(42,42,123);
        const auto selected=mt::GridFallbackSelector::select(grid,rng,services,0x90000,1);
        assert(cell.longAt(12)==0 && services.header.count18==2 && services.header.head20==0 && services.releases==1);
        assert(selected.coordinate.row==16 && selected.coordinate.column==3);
        assert(selected.phase==(kind==1 ? mt::GridFallbackSelector::Phase::random : mt::GridFallbackSelector::Phase::budget_exhausted));
    }
}
