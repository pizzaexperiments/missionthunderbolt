// Batch adapter for the private 68000 oracle harness. No original game bytes included.
#include "engine/shuffled_lcg_model.hpp"
#include <iostream>
#include <sstream>
#include <string>
int main() {
    std::string line;int executed=0;
    while(std::getline(std::cin,line)) {
        std::istringstream input(line);int one=0,bound=0;mt::ShuffledLcgModel::State state;
        input>>one>>bound>>state.local_seed>>state.selector_seed;
        for(auto& value:state.table) input>>value;
        std::string extra;if(!input || (input>>extra) || (one!=0 && one!=1)) return 2;
        mt::ShuffledLcgModel model(state);
        auto result=one ? model.oneBased(bound) : model.zeroBased(bound);
        const auto& after=model.state();
        std::cout<<result<<' '<<after.last_result<<' '<<after.local_seed<<' '<<after.selector_seed;
        for(auto value:after.table)std::cout<<' '<<value;
        std::cout<<'\n';++executed;
    }
    return executed ? 0 : 3;
}
