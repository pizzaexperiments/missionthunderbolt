// Batch adapters for synthetic coordinate-byte and candidate-gate oracle inputs.
#include "engine/grid_record_layout.hpp"
#include <iostream>
#include <string>
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    const std::string mode=argv[1];unsigned cases=0;
    if(mode=="--clamp") {
        int row=0,column=0;
        while(std::cin>>row>>column) {
            if(row<0 || row>255 || column<0 || column>255)return 2;
            auto result=mt::GridRecordLayout::clampSignedBytes(column<128 ? column : column-256,row<128 ? row : row-256);
            std::cout<<result.row<<' '<<result.column<<'\n';++cases;
        }
    } else if(mode=="--candidate") {
        unsigned kind=0;uint32_t field16=0;
        while(std::cin>>kind>>field16) {
            if(kind>255)return 2;
            std::cout<<mt::GridRecordLayout::selectionCandidate(static_cast<uint8_t>(kind),field16)<<'\n';++cases;
        }
    } else return 2;
    return std::cin.eof() && cases ? 0 : 2;
}
