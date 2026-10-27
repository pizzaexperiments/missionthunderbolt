// Batch synthetic maps, seed words and direction tables for the private oracle.
#include "engine/grid_candidate_selector.hpp"
#include <iostream>
#include <sstream>
#include <string>
int main() {
    std::string line;unsigned cases=0;
    while(std::getline(std::cin,line)) {
        std::istringstream in(line);uint32_t seed=0,last=0;unsigned fallback=0;
        if(!(in>>seed>>fallback>>last) || fallback>65535)return 2;
        mt::GridCandidateSelector::Directions directions;
        for(auto& d:directions)if(!(in>>d.row>>d.column))return 2;
        mt::GridCandidateSelector::Grid grid;
        for(auto& c:grid) {
            unsigned kind=0;if(!(in>>kind>>c.field16) || kind>255)return 2;c.kind=static_cast<uint8_t>(kind);
        }
        std::string extra;if(in>>extra)return 2;
        auto rng=mt::ShuffledLcgModel::initialized(seed,static_cast<uint16_t>(fallback),last);
        const auto result=mt::GridCandidateSelector::select(grid,directions,rng);
        std::cout<<static_cast<int>(result.outcome)<<' '<<result.iterations<<' '<<result.coordinate.row<<' '<<result.coordinate.column;
        const auto& state=rng.state();std::cout<<' '<<state.last_result<<' '<<state.local_seed<<' '<<state.selector_seed;
        for(auto value:state.table)std::cout<<' '<<value;
        std::cout<<'\n';++cases;
    }
    return cases ? 0 : 3;
}
