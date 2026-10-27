#include "engine/record_release_model.hpp"
#include <iostream>
#include <string>
using M=mt::RecordReleaseModel;
static uint32_t snapshot(const M::Nodes& nodes,const M::Parent& parent) {
    uint32_t hash=2166136261u;
    auto byte=[&](uint8_t value){hash=(hash^value)*16777619u;};
    auto word=[&](uint32_t value){for(unsigned s:{24,16,8,0})byte(static_cast<uint8_t>(value>>s));};
    for(const auto& entry:nodes){word(entry.first);word(entry.second.next26);word(entry.second.branch30);}
    byte(parent.count51);word(parent.field52);for(auto value:parent.slots60)word(value);
    return hash;
}
int main(int argc,char** argv) {
    if(argc==2 && std::string(argv[1])=="--prefix") {
        uint32_t payload;unsigned value;
        while(std::cin>>payload>>value) {
            if(value>65535)return 2;
            uint16_t prefix=static_cast<uint16_t>(value);unsigned calls=0;uint32_t address=0;
            M::releasePrefix(payload,prefix,[&](uint32_t ref){++calls;address=ref;});
            std::cout<<prefix<<' '<<calls<<' '<<address<<'\n';
        }
        return std::cin.eof()?0:2;
    }
    if(argc!=1)return 2;
    unsigned mode,count,size;uint32_t root,budget;
    while(std::cin>>mode>>root>>budget>>count) {
        if(mode>1 || count>127)return 2;
        M::Parent parent;parent.count51=static_cast<uint8_t>(count);
        if(!(std::cin>>parent.field52))return 2;
        for(auto& slot:parent.slots60)if(!(std::cin>>slot))return 2;
        if(!(std::cin>>size) || size>256)return 2;
        M::Nodes nodes;
        for(unsigned i=0;i<size;++i) {
            uint32_t id,next,branch;if(!(std::cin>>id>>next>>branch))return 2;
            if(id==0 || !nodes.emplace(id,M::Node{next,branch}).second)return 2;
        }
        std::vector<std::array<uint32_t,2>> events;
        const auto dispose=[&](uint32_t id){events.push_back({id,snapshot(nodes,parent)});};
        const auto result=mode?M::release12(nodes,parent,root,budget,dispose):M::release16(nodes,root,budget,dispose);
        std::cout<<static_cast<unsigned>(result.status)<<' '<<result.steps<<' '<<snapshot(nodes,parent)<<' '<<events.size();
        for(const auto& event:events)std::cout<<' '<<event[0]<<' '<<event[1];
        // Compare every modeled final field exactly, beyond the observer-time
        // fingerprints used to capture disposal ordering and intermediate state.
        std::cout<<' '<<static_cast<unsigned>(parent.count51)<<' '<<parent.field52;
        for(auto slot:parent.slots60)std::cout<<' '<<slot;
        for(const auto& entry:nodes)std::cout<<' '<<entry.first<<' '<<entry.second.next26<<' '<<entry.second.branch30;
        std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
