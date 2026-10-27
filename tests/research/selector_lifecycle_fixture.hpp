#pragma once
#include "engine/grid_candidate_selector.hpp"
#include "engine/linked_record_model.hpp"
#include "engine/record_release_model.hpp"
#include <iomanip>
#include <iostream>
#include <algorithm>

namespace lifecycle_fixture {
using F=mt::GridFallbackSelector;using L=mt::LinkedRecordModel;using R=mt::RecordReleaseModel;
constexpr uint32_t primary=0xb0000,child=0xb0100,target=0xc0000,previous=0xc1000,following=0xc2000,extra=0xd0000,grid_id=0x90000;
struct Config {
    uint32_t seed;unsigned directions,profile,shape,prefix,word,flags,count,row,column,position;
};
struct Raw {uint16_t prefix;std::vector<uint8_t> bytes;bool parent=false;};
class World : public F::Services {
public:
    F::Grid grid{};L::Header header{3,target};std::map<uint32_t,Raw> records;
    std::vector<std::array<uint32_t,3>> events;
    explicit World(const Config& c) {
        for(unsigned i=0;i<5;++i)records.emplace(primary+i*0x100,Raw{static_cast<uint16_t>(c.prefix),std::vector<uint8_t>(64,0xa5),false});
        for(auto id:{target,previous,following})records.emplace(id,Raw{static_cast<uint16_t>(c.prefix),std::vector<uint8_t>(568,0xa5),true});
        records.emplace(extra,Raw{static_cast<uint16_t>(c.prefix),std::vector<uint8_t>(16,0xa5),false});
        for(unsigned i=0;i<5;++i) {
            auto& b=records.at(primary+i*0x100).bytes;b[0]=0;b[1]=1;b[25]=0;put(b,26,0);put(b,30,0);
        }
        auto& p=records.at(primary).bytes;p[0]=static_cast<uint8_t>(c.word>>8);p[1]=static_cast<uint8_t>(c.word);p[25]=static_cast<uint8_t>(c.flags);
        if(c.shape) {put(p,26,child);put(p,30,child+0x200);put(records.at(child).bytes,26,child+0x100);put(records.at(child).bytes,30,child+0x300);}
        for(auto id:{target,previous,following}) {
            auto& b=records.at(id).bytes;b[0]=0;b[1]=1;b[48]=1;b[49]=1;b[51]=0;put(b,52,0);put(b,56,0);
            for(unsigned i=0;i<127;++i)put(b,60+i*4,0);
        }
        auto& parent=records.at(target).bytes;parent[48]=static_cast<uint8_t>(c.row);parent[49]=static_cast<uint8_t>(c.column);
        parent[51]=static_cast<uint8_t>(c.count);put(parent,52,extra);
        for(unsigned i=0;i<c.count;++i)put(parent,60+i*4,child+(i%4)*0x100);
        if(c.profile==5)parent[1]=73;
        if(c.profile==6)records.at(child).bytes[1]=52;
        if(c.position==0){header.head20=target;put(parent,56,previous);put(records.at(previous).bytes,56,following);}
        else if(c.position==1){header.head20=previous;put(records.at(previous).bytes,56,target);put(parent,56,following);}
        else {header.head20=previous;put(records.at(previous).bytes,56,following);put(records.at(following).bytes,56,target);}
        for(unsigned row=0;row<19;++row)for(unsigned column=0;column<67;++column) {
            auto& cell=grid[row*67+column];cell.bytes={1,0,0x12,0x34,0,0,171,205,1,85,102,119,0,0,0,0,0,0,0,0};
            if(c.profile==0 || (c.profile==1 && (row+column)%2==0)){cell.bytes[0]=0;cell.bytes[8]=0;}
        }
        if(c.profile>=2) {
            auto& cell=grid[c.row*67+c.column];
            if(c.profile==2){cell.bytes[0]=0;cell.bytes[8]=0;cell.setLong(16,primary);}
            else if(c.profile==7){cell.bytes[0]=0;cell.bytes[8]=0;}
            else {cell.bytes[0]=c.profile==4?2:c.profile==8?25:1;cell.bytes[4]=c.profile==4?64:0;cell.setLong(16,primary);cell.setLong(12,target);}
        }
    }
    static uint32_t get(const std::vector<uint8_t>& b,unsigned at) {
        return (uint32_t(b.at(at))<<24)|(uint32_t(b.at(at+1))<<16)|(uint32_t(b.at(at+2))<<8)|b.at(at+3);
    }
    static void put(std::vector<uint8_t>& b,unsigned at,uint32_t value) {
        for(unsigned i=0;i<4;++i)b.at(at+i)=static_cast<uint8_t>(value>>(24-i*8));
    }
    F::Link16 read16(uint32_t id) override {const auto& b=records.at(id).bytes;return {static_cast<uint16_t>((b[0]<<8)|b[1]),b[25]};}
    F::Link12 read12(uint32_t id) override {
        const auto& b=records.at(id).bytes;std::vector<uint32_t> slots;
        for(unsigned i=0;i<b[51];++i)slots.push_back(get(b,60+i*4));
        return {static_cast<uint16_t>((b[0]<<8)|b[1]),b[51],slots};
    }
    uint16_t query16(uint32_t id) override {events.push_back({1,id,0});const auto& b=records.at(id).bytes;return L::query16(read16(id).word0,get(b,30));}
    void unlink12(uint32_t identity,uint32_t id) override {
        events.push_back({3,identity,id});L::Nodes nodes;
        for(const auto& e:records)if(e.second.parent){const auto& b=e.second.bytes;nodes.emplace(e.first,L::Node{b[48],b[49],get(b,56)});}
        const auto result=L::unlink12(header,grid,nodes,id,32);
        if(result.status!=L::Status::unlinked)throw std::runtime_error("fixture unlink did not complete");
        for(const auto& e:nodes)put(records.at(e.first).bytes,56,e.second.next56);
    }
    void release16(uint32_t id) override {
        events.push_back({2,id,0});auto nodes=graph();
        const auto result=R::release16(nodes,id,1024,[&](uint32_t ref){sync(nodes);dispose(ref);});
        sync(nodes);if(result.status!=R::Status::complete)throw std::runtime_error("fixture release did not complete");
    }
    void release12(uint32_t id) override {
        events.push_back({4,id,0});auto nodes=graph();R::Parent parent;
        auto& b=records.at(id).bytes;parent.count51=b[51];parent.field52=get(b,52);
        for(unsigned i=0;i<127;++i)parent.slots60[i]=get(b,60+i*4);
        auto save=[&](){sync(nodes);b[51]=parent.count51;put(b,52,parent.field52);for(unsigned i=0;i<127;++i)put(b,60+i*4,parent.slots60[i]);};
        const auto result=R::release12(nodes,parent,id,1024,[&](uint32_t ref){save();dispose(ref);},
                                     [&](uint32_t ref){save();events.push_back({2,ref,0});});
        save();if(result.status!=R::Status::complete)throw std::runtime_error("fixture parent release did not complete");
    }
private:
    R::Nodes graph() const {R::Nodes result;for(unsigned i=0;i<5;++i){auto id=primary+i*0x100;const auto& b=records.at(id).bytes;result.emplace(id,R::Node{get(b,26),get(b,30)});}return result;}
    void sync(const R::Nodes& nodes){for(const auto& e:nodes){auto& b=records.at(e.first).bytes;put(b,26,e.second.next26);put(b,30,e.second.branch30);}}
    void dispose(uint32_t id) {
        auto& prefix=records.at(id).prefix;events.push_back({5,id,prefix});
        R::releasePrefix(id,prefix,[&](uint32_t address){events.push_back({6,address,0});});
    }
};
struct Outcome {int phase,attempts,row,column,pre_attempts;};
inline Outcome run(World& world,const Config& c,mt::ShuffledLcgModel& rng,
                   const mt::GridCandidateSelector::Directions* supplied=nullptr) {
    mt::GridCandidateSelector::Grid compact;
    for(unsigned i=0;i<world.grid.size();++i)compact[i]={world.grid[i].bytes[0],world.grid[i].longAt(16)};
    mt::GridCandidateSelector::Directions directions{{{-1,0},{-1,1},{0,1},{1,1},{1,0},{1,-1},{0,-1},{-1,-1}}};
    if(c.directions==1)std::rotate(directions.begin(),directions.begin()+3,directions.end());
    if(c.directions==2)directions={{{-128,-128},{127,127},{-128,127},{127,-128},{0,127},{127,0},{0,-128},{-128,0}}};
    if(supplied)directions=*supplied;
    const auto first=mt::GridCandidateSelector::select(compact,directions,rng);
    if(first.outcome!=mt::GridCandidateSelector::Outcome::needs_fallback)
        return {first.outcome==mt::GridCandidateSelector::Outcome::direct?4:5,0,first.coordinate.row,first.coordinate.column,first.iterations};
    const auto result=F::select(world.grid,rng,world,grid_id,1);
    return {static_cast<int>(result.phase),static_cast<int>(result.random_attempts),result.coordinate.row,result.coordinate.column,200};
}
inline void write(const World& world,const Outcome& result,const mt::ShuffledLcgModel& rng) {
    const auto& s=rng.state();
    std::cout<<result.phase<<' '<<result.attempts<<' '<<result.row<<' '<<result.column<<' '<<result.pre_attempts<<' '<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
    for(auto value:s.table)std::cout<<' '<<value;
    std::cout<<' '<<world.header.count18<<' '<<world.header.head20<<' '<<std::hex<<std::setfill('0');
    for(const auto& cell:world.grid)for(auto b:cell.bytes)std::cout<<std::setw(2)<<unsigned(b);
    for(const auto& e:world.records){std::cout<<' '<<std::dec<<e.first<<' '<<e.second.prefix<<' '<<std::hex;for(auto b:e.second.bytes)std::cout<<std::setw(2)<<unsigned(b);}
    std::cout<<std::dec<<' '<<world.events.size();for(const auto& event:world.events)for(auto value:event)std::cout<<' '<<value;
    std::cout<<'\n';
}
}
