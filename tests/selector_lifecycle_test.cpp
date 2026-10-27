#include "research/selector_lifecycle_fixture.hpp"
#include <cassert>
using namespace lifecycle_fixture;
int main() {
    // Frozen original-instruction traces from authored worlds; no original bytes.
    Config c{42,0,3,0,65535,70,0,3,16,62,1};World world(c);
    auto rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);auto result=run(world,c,rng);
    assert(result.phase==2 && result.attempts==1 && result.pre_attempts==200 && result.row==16 && result.column==62);
    assert(rng.state().last_result==62 && rng.state().local_seed==3434688321u && rng.state().selector_seed==820909630u);
    assert(world.header.count18==2 && world.header.head20==previous);
    assert(World::get(world.records.at(previous).bytes,56)==following && World::get(world.records.at(target).bytes,56)==0);
    const std::vector<std::array<uint32_t,3>> expected{
        {2,primary,0},{5,primary,65535},{6,primary-2,0},{3,grid_id,target},{4,target,0},
        {2,child+0x200,0},{5,child+0x200,65535},{6,child+0x200-2,0},
        {2,child+0x100,0},{5,child+0x100,65535},{6,child+0x100-2,0},
        {2,child,0},{5,child,65535},{6,child-2,0},
        {5,extra,65535},{6,extra-2,0},{5,target,65535},{6,target-2,0}};
    assert(world.events==expected && world.records.at(target).bytes[51]==0);
    for(unsigned i=0;i<3;++i)assert(World::get(world.records.at(target).bytes,60+i*4)==0);
    assert(world.grid[16*67+62].longAt(12)==0 && world.grid[16*67+62].longAt(16)==0);
    c.prefix=0;World no_traps(c);rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);result=run(no_traps,c,rng);
    assert(result.phase==2 && no_traps.events.size()==12);
    for(const auto& event:no_traps.events)assert(event[0]!=6);
    assert(no_traps.records.at(primary).prefix==65535 && no_traps.records.at(target).prefix==65535);
    c={42,0,4,0,65535,65535,0,0,16,62,2};World rejected(c);rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);result=run(rejected,c,rng);
    assert(result.phase==3 && result.attempts==1 && rejected.events.size()==9);
    assert(rejected.header.count18==2 && rejected.grid[16*67+62].bytes[0]==2);
    assert(rejected.grid[16*67+62].longAt(12)==0 && rejected.grid[16*67+62].longAt(16)==0);
    assert(rejected.records.at(target).prefix==0 && World::get(rejected.records.at(following).bytes,56)==0);
    c={42,0,2,1,65535,29,0,3,16,62,1};World scan(c);rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);result=run(scan,c,rng);
    assert(result.phase==1 && result.attempts==0 && scan.events.size()==12 && scan.header.count18==3);
    assert((scan.events.front()==std::array<uint32_t,3>{1,primary,0}));
    assert(rng.state().last_result==1 && rng.state().local_seed==2836888651u && rng.state().selector_seed==1125943744u);
    c.profile=0;World direct(c);rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);result=run(direct,c,rng);
    assert(result.phase==4 && result.pre_attempts==1 && result.row==16 && result.column==3 && direct.events.empty());
}
