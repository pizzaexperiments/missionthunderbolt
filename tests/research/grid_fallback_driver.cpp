// Synthetic raw-record/callback batch adapter; no original assets or runtime code.
#include "engine/grid_fallback_selector.hpp"
#include "engine/grid_candidate_selector.hpp"
#include <iostream>
#include <sstream>
#include <string>
#include <iomanip>
#include <algorithm>
using Fallback=mt::GridFallbackSelector;
struct SyntheticServices : Fallback::Services {
    unsigned query=0,word16=0,byte25=0,word12=0,byte51=0,child_word=0,child_flags=0;
    std::vector<std::array<uint32_t,3>> events;
    Fallback::Link16 read16(uint32_t ref) override {
        if(ref==0xb0000)return {static_cast<uint16_t>(word16),static_cast<uint8_t>(byte25)};
        if(ref==0xb1000)return {static_cast<uint16_t>(child_word),static_cast<uint8_t>(child_flags)};
        throw std::out_of_range("unknown synthetic link16");
    }
    Fallback::Link12 read12(uint32_t ref) override {
        if(ref!=0xc0000)throw std::out_of_range("unknown synthetic link12");
        return {static_cast<uint16_t>(word12),static_cast<uint8_t>(byte51),std::vector<uint32_t>(127,0xb1000)};
    }
    uint16_t query16(uint32_t ref) override {events.push_back({1,ref,0});return static_cast<uint16_t>(query);}
    void release16(uint32_t ref) override {events.push_back({2,ref,0});}
    void unlink12(uint32_t grid,uint32_t ref) override {events.push_back({3,grid,ref});}
    void release12(uint32_t ref) override {events.push_back({4,ref,0});}
};
int main(int argc,char** argv) {
    const bool pipeline=argc==2 && std::string(argv[1])=="--pipeline";
    if(argc!=1 && !pipeline)return 2;
    std::string line;unsigned cases=0;
    while(std::getline(std::cin,line)) {
        std::istringstream in(line);uint32_t seed=0,last=0,budget=0;unsigned fallback=0;
        SyntheticServices services;std::string hex;unsigned direction_mode=0;
        if(!(in>>seed>>fallback>>last>>budget>>services.query>>services.word16>>services.byte25>>services.word12>>services.byte51>>services.child_word>>services.child_flags))return 2;
        if(pipeline && (!(in>>direction_mode) || direction_mode>2))return 2;
        if(!(in>>hex))return 2;
        if(fallback>65535 || services.query>65535 || services.word16>65535 || services.word12>65535 || services.child_word>65535 || services.byte25>255 || services.byte51>255 || services.child_flags>255 || budget>10000 || hex.size()!=1273*40)return 2;
        Fallback::Grid grid;
        auto nibble=[](char c)->int {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;return -1;};
        for(unsigned cell=0;cell<grid.size();++cell)for(unsigned b=0;b<20;++b) {
            unsigned at=(cell*20+b)*2;int hi=nibble(hex[at]),lo=nibble(hex[at+1]);if(hi<0 || lo<0)return 2;
            grid[cell].bytes[b]=static_cast<uint8_t>((hi<<4)|lo);
        }
        std::string extra;if(in>>extra)return 2;
        auto rng=mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        Fallback::Result result{{-1,-1},Fallback::Phase::budget_exhausted,0};
        int phase=0,pre_attempts=0;
        if(pipeline) {
            mt::GridCandidateSelector::Grid compact;
            for(unsigned i=0;i<grid.size();++i)compact[i]={grid[i].bytes[0],grid[i].longAt(16)};
            mt::GridCandidateSelector::Directions directions{{{-1,0},{-1,1},{0,1},{1,1},{1,0},{1,-1},{0,-1},{-1,-1}}};
            if(direction_mode==1)std::rotate(directions.begin(),directions.begin()+3,directions.end());
            if(direction_mode==2)directions={{{-128,-128},{127,127},{-128,127},{127,-128},{0,127},{127,0},{0,-128},{-128,0}}};
            const auto first=mt::GridCandidateSelector::select(compact,directions,rng);pre_attempts=first.iterations;
            if(first.outcome!=mt::GridCandidateSelector::Outcome::needs_fallback) {
                phase=first.outcome==mt::GridCandidateSelector::Outcome::direct ? 4 : 5;result.coordinate=first.coordinate;
            } else {result=Fallback::select(grid,rng,services,0x90000,budget);phase=static_cast<int>(result.phase);}
        } else {result=Fallback::select(grid,rng,services,0x90000,budget);phase=static_cast<int>(result.phase);}
        const auto& s=rng.state();
        std::cout<<phase<<' '<<result.random_attempts<<' '<<result.coordinate.row<<' '<<result.coordinate.column<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
        for(auto value:s.table)std::cout<<' '<<value;
        std::cout<<' '<<std::hex<<std::setfill('0');
        for(const auto& c:grid)for(auto b:c.bytes)std::cout<<std::setw(2)<<static_cast<unsigned>(b);
        std::cout<<std::dec<<' '<<services.events.size();
        for(const auto& e:services.events)std::cout<<' '<<e[0]<<' '<<e[1]<<' '<<e[2];
        if(pipeline)std::cout<<' '<<pre_attempts;
        std::cout<<'\n';++cases;
    }
    return cases ? 0 : 3;
}
