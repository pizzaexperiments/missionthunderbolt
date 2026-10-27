#include "engine/grid_fallback_selector.hpp"
#include <cassert>
using F=mt::GridFallbackSelector;
static constexpr uint32_t linked16=0xb0000,linked12=0xc0000,gridId=0x90000;
struct Services : F::Services {
    uint16_t query=1,word16=1,word12=1;
    std::vector<std::array<uint32_t,3>> events;
    F::Link16 read16(uint32_t ref) override {assert(ref==linked16);return {word16,0};}
    F::Link12 read12(uint32_t ref) override {assert(ref==linked12);return {word12,0,{}};}
    uint16_t query16(uint32_t ref) override {events.push_back({1,ref,0});return query;}
    void release16(uint32_t ref) override {events.push_back({2,ref,0});}
    void unlink12(uint32_t grid,uint32_t ref) override {events.push_back({3,grid,ref});}
    void release12(uint32_t ref) override {events.push_back({4,ref,0});}
};
static F::Record record(uint8_t kind=1) {
    F::Record result;result.bytes={kind,0,0x12,0x34,0,0,0xab,0xcd,1,0x55,0x66,0x77,0,0,0,0,0,0,0,0};return result;
}
static mt::ShuffledLcgModel rng() {return mt::ShuffledLcgModel::initialized(42,42,123);}
int main() {
    F::Grid grid;grid.fill(record());Services services;auto random=rng();const auto before=random.state();
    grid[2*67+3]=record(0);grid[2*67+3].bytes[8]=0;
    auto result=F::select(grid,random,services,gridId,1);
    assert(result.phase==F::Phase::first_scan && result.coordinate.row==2 && result.coordinate.column==3);
    assert(result.random_attempts==0 && random.state().table==before.table && random.state().selector_seed==42);
    grid.fill(record());grid[68]=record(0);grid[68].bytes[8]=0;grid[68].setLong(16,linked16);
    result=F::select(grid,random,services,gridId,1);
    assert(result.phase==F::Phase::second_scan && result.coordinate.row==1 && result.coordinate.column==1);
    assert(grid[68].longAt(16)==0 && services.events.size()==2);
    assert((services.events[0]==std::array<uint32_t,3>{1,linked16,0}));
    assert((services.events[1]==std::array<uint32_t,3>{2,linked16,0}));
    assert(random.state().table==before.table);
    grid.fill(record());services.events.clear();random=rng();
    result=F::select(grid,random,services,gridId,1);
    assert(result.phase==F::Phase::random && result.random_attempts==1);
    assert(result.coordinate.row==16 && result.coordinate.column==3);
    assert(random.state().last_result==3 && random.state().local_seed==601077795u && random.state().selector_seed==3263785912u);
    const std::array<uint8_t,20> expected{0,0,3,232,0,0,160,205,0,85,0,0,0,0,0,0,0,0,0,0};
    assert(grid[1075].bytes==expected && grid[0].bytes==record().bytes);
    // A rejected random attempt can already have issued callbacks and cleared field +16.
    auto protectedKind=record(2);protectedKind.bytes[4]=64;protectedKind.setLong(12,linked12);protectedKind.setLong(16,linked16);
    grid.fill(protectedKind);services.events.clear();random=rng();
    result=F::select(grid,random,services,gridId,1);
    assert(result.phase==F::Phase::budget_exhausted && result.random_attempts==1);
    assert(grid[1075].bytes[0]==2 && grid[1075].longAt(16)==0 && grid[1075].longAt(12)==linked12);
    assert((services.events==std::vector<std::array<uint32_t,3>>{{2,linked16,0},{3,gridId,linked12},{4,linked12,0}}));
    grid.fill(record(28));services.events.clear();random=rng();
    result=F::select(grid,random,services,gridId,0);
    assert(result.phase==F::Phase::budget_exhausted && result.coordinate.row==-1 && result.coordinate.column==-1);
    assert(random.state().table==before.table && random.state().last_result==123);
    result=F::select(grid,random,services,gridId,1);
    assert(result.phase==F::Phase::budget_exhausted && grid[1075].bytes==record(28).bytes);
    auto flags=record(35);flags.bytes[4]=255;flags.bytes[5]=255;flags.bytes[6]=255;
    grid.fill(flags);random=rng();result=F::select(grid,random,services,gridId,1);
    const std::array<uint8_t,20> expectedFlags{35,0,18,52,250,18,240,205,0,0,0,0,0,0,0,0,0,0,0,0};
    assert(result.phase==F::Phase::random && grid[1075].bytes==expectedFlags);
    auto invalid=record();const auto saved=invalid.bytes;bool rejected=false;
    try {invalid.setLong(17,1);} catch(const std::out_of_range&) {rejected=true;}
    assert(rejected && invalid.bytes==saved);
}
