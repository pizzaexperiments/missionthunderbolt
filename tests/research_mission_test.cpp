#include "engine/research_mission.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <locale>
#include <sstream>
#include <string>
#include <utility>
#include <vector>
using M=mt::ResearchMission;
static bool equal(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
static void connected(const M& mission) {
    std::array<bool,M::Width*M::Height> visited{};std::vector<std::pair<int,int>> pending{{1,1}};
    visited[M::Width+1]=true;
    for(unsigned index=0;index<pending.size();++index) {
        const auto position=pending[index];
        for(const auto& delta:std::array<std::pair<int,int>,4>{{{1,0},{-1,0},{0,1},{0,-1}}}) {
            const int x=position.first+delta.first,y=position.second+delta.second;
            if(mission.walkable(x,y) && !visited[y*M::Width+x]) {visited[y*M::Width+x]=true;pending.emplace_back(x,y);}
        }
    }
    unsigned floors=0;
    for(int y=0;y<M::Height;++y)for(int x=0;x<M::Width;++x) {
        if(mission.walkable(x,y)) {++floors;assert(visited[y*M::Width+x]);}
        if(x==0 || y==0 || x==M::Width-1 || y==M::Height-1)assert(!mission.walkable(x,y));
    }
    assert(floors>100 && floors<M::Width*M::Height);
}
static void scenario(uint32_t seed) {
    M mission(seed);const auto rows=mission.asciiRows();
    assert(rows.size()==19 && rows.front().size()==67 && rows[1][3]=='!');
    assert(mission.walkable(1,1) && mission.walkable(2,1) && mission.walkable(3,1));
    assert(!mission.walkable(-1,1) && !mission.walkable(67,1) && !mission.walkable(1,19));
    connected(mission);
    unsigned up=0,down=0,items=0;
    for(int y=0;y<M::Height;++y)for(int x=0;x<M::Width;++x) {
        const auto index=static_cast<unsigned>(y*M::Width+x);const auto& cell=mission.cells()[index];
        assert(cell==mission.grid()[index].bytes);
        if(rows[y][x]=='^') {++up;assert(cell[0]==0 && (cell[4]&4) && cell[3]==17);}
        else if(rows[y][x]=='v') {++down;assert(cell[0]==0 && (cell[4]&4) && cell[3]==19);}
        else if(rows[y][x]=='#')assert(cell[0]==2 && cell[3]==13);
        else {assert(cell[0]==0 && cell[3]==7);if(rows[y][x]=='!')++items;}
    }
    assert(up==1 && down==1 && items==1);
    assert(mission.header().count18==1 && mission.header().head20==M::ItemHandle);
    assert(mission.grid()[M::Width+3].longAt(12)==M::ItemHandle);
    assert(mission.nodes().at(M::ItemHandle).row48==1 && mission.nodes().at(M::ItemHandle).column49==3);
    assert(mission.item()[48]==1 && mission.item()[49]==3 && (mission.item()[21]&16));
    assert(!mission.carried());
    const auto original_save=mission.serialize();const auto original_rng=mission.rngState();
    const auto restored=M::restore(original_save);
    assert(restored.serialize()==original_save && restored.cells()==mission.cells() && restored.item()==mission.item());
    assert(!mission.pickup(1,1) && !mission.pickup(-1,1) && !mission.pickup(3,19));
    assert(mission.serialize()==original_save);
    const auto initial_cells=mission.cells();const auto initial_item=mission.item();
    assert(mission.pickup(3,1));
    assert(mission.carried() && mission.header().count18==0 && mission.header().head20==0);
    assert(mission.grid()[M::Width+3].longAt(12)==0 && mission.asciiRows()[1][3]=='.');
    assert(equal(mission.rngState(),original_rng));
    assert(mission.item()==initial_item && mission.nodes().at(M::ItemHandle).next56==0);
    for(unsigned i=0;i<initial_cells.size();++i)for(unsigned b=0;b<20;++b)
        if(i!=M::Width+3 || b<12 || b>=16)assert(initial_cells[i][b]==mission.cells()[i][b]);
    const auto carried_save=mission.serialize();assert(!mission.pickup(3,1));assert(mission.serialize()==carried_save);
    const auto carried=M::restore(carried_save);
    assert(carried.carried() && carried.serialize()==carried_save && carried.cells()==mission.cells());
    assert(carried.item()==mission.item() && equal(carried.rngState(),mission.rngState()));
}
static void invalidSaves() {
    const auto saved=M(17).serialize();std::istringstream input(saved);std::vector<std::string> parts;std::string part;
    while(input>>part)parts.push_back(part);
    assert(parts.size()==106); // tag, seed, carried, all 103 RNG words
    for(unsigned index=3;index<parts.size();++index) {
        auto changed=parts;changed[index]=changed[index]=="0"?"1":"0";std::ostringstream output;
        for(const auto& token:changed)output<<token<<' ';
        bool rejected=false;try {(void)M::restore(output.str());}catch(const std::invalid_argument&) {rejected=true;}
        assert(rejected);
    }
    for(const auto& invalid:std::vector<std::string>{"", "RM0 1 0", "RM1 -1 0", "RM1 4294967296 0",
            "RM1 17 2", saved+" trailing", saved.substr(0,saved.size()/2), std::string(4097,'0')}) {
        bool rejected=false;try {(void)M::restore(invalid);}catch(const std::invalid_argument&) {rejected=true;}
        assert(rejected);
    }
}
class GroupedNumbers:public std::numpunct<char> {
protected:
    char do_thousands_sep() const override {return '_';}
    std::string do_grouping() const override {return "\3";}
};
static void localeIndependent() {
    M mission(123456);assert(mission.pickup(3,1));const auto expected=mission.serialize();
    const auto before=std::locale();std::locale::global(std::locale(before,new GroupedNumbers));
    const auto saved=mission.serialize();const auto restored=M::restore(saved);
    std::locale::global(before);
    assert(saved==expected && restored.serialize()==expected);
}
int main() {
    for(uint32_t seed=0;seed<64;++seed)scenario(seed);
    scenario(0xffffffffu);
    assert(M(1).asciiRows()==M(1).asciiRows());
    assert(M(1).asciiRows()!=M(2).asciiRows());
    assert(!equal(M(1).rngState(),mt::ShuffledLcgModel::initialized(1,1).state()));
    invalidSaves();localeIndependent();
}
