#include "engine/linked_record_model.hpp"
#include <iostream>
#include <string>
using M=mt::LinkedRecordModel;
int main(int argc,char** argv) {
    if(argc==2 && std::string(argv[1])=="--query") {
        unsigned word;uint32_t field;
        while(std::cin>>word>>field) {
            if(word>65535)return 2;
            std::cout<<M::query16(static_cast<uint16_t>(word),field)<<'\n';
        }
        return std::cin.eof()?0:2;
    }
    if(argc!=1)return 2;
    unsigned count,row,column,n;uint32_t head,target,budget,grid_link;
    while(std::cin>>count>>head>>target>>budget>>row>>column>>grid_link>>n) {
        if(count>65535 || row>=19 || column>=67 || n>100)return 2;
        M::Header header{static_cast<uint16_t>(count),head};M::Nodes nodes;
        for(unsigned i=0;i<n;++i) {
            uint32_t identity,next;if(!(std::cin>>identity>>next))return 2;
            if(identity==0 || !nodes.emplace(identity,M::Node{static_cast<uint8_t>(row),static_cast<uint8_t>(column),next}).second)return 2;
        }
        mt::GridFallbackSelector::Grid grid{};grid[row*67+column].setLong(12,grid_link);
        const auto result=M::unlink12(header,grid,nodes,target,budget);
        std::cout<<static_cast<unsigned>(result.status)<<' '<<result.visits<<' '<<header.count18<<' '<<header.head20<<' '<<grid[row*67+column].longAt(12);
        for(const auto& entry:nodes)std::cout<<' '<<entry.first<<' '<<entry.second.next56;
        std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
