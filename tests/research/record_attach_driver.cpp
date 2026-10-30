#include "engine/linked_record_model.hpp"
#include <iostream>
using M=mt::LinkedRecordModel;
int main() {
    unsigned count,row,column,oldrow,oldcolumn,remove;uint32_t head,target,next,link;
    while(std::cin>>count>>head>>target>>row>>column>>oldrow>>oldcolumn>>next>>link>>remove) {
        if(count>65535 || row>=19 || column>=67 || oldrow>255 || oldcolumn>255 || remove>1)return 2;
        M::Header header{static_cast<uint16_t>(count),head};mt::GridFallbackSelector::Grid grid;
        for(auto& cell:grid)cell.bytes.fill(0x5a);
        grid[row*67+column].setLong(12,link);const auto before=grid;
        M::Nodes nodes{{target,{static_cast<uint8_t>(oldrow),static_cast<uint8_t>(oldcolumn),next}}};
        M::attach12(header,grid,nodes,target,static_cast<int>(row),static_cast<int>(column));
        if(remove) {
            const auto result=M::unlink12(header,grid,nodes,target,0);
            if(result.status!=M::Status::unlinked || result.visits!=0)return 3;
        }
        for(unsigned i=0;i<grid.size();++i)for(unsigned j=0;j<20;++j)
            if((i!=row*67+column || j<12 || j>=16) && grid[i].bytes[j]!=before[i].bytes[j])return 3;
        const auto& node=nodes.at(target);
        std::cout<<header.count18<<' '<<header.head20<<' '<<unsigned(node.row48)<<' '
                 <<unsigned(node.column49)<<' '<<node.next56<<' '<<grid[row*67+column].longAt(12)<<'\n';
    }
    return std::cin.eof()?0:2;
}
