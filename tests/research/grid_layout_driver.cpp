// Batch synthetic base addresses for the private original-instruction oracle.
#include "engine/grid_record_layout.hpp"
#include <iostream>
int main() {
    uint32_t base=0;unsigned cases=0;
    while(std::cin>>base) {
        for(int y=0;y<mt::GridRecordLayout::rows;++y)
            for(int x=0;x<mt::GridRecordLayout::columns;++x)
                std::cout<<mt::GridRecordLayout::address32(base,x,y)<<' ';
        std::cout<<'\n';++cases;
    }
    return std::cin.eof() && cases ? 0 : 2;
}
