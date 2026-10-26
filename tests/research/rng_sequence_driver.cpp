// Synthetic-input batch adapter for private original-instruction comparisons.
#include "engine/shuffled_lcg_model.hpp"
#include <iostream>
#include <sstream>
#include <string>
static void emit(const mt::ShuffledLcgModel& model) {
    const auto& s=model.state();
    std::cout<<s.last_result<<' '<<s.local_seed<<' '<<s.selector_seed;
    for(auto v:s.table)std::cout<<' '<<v;
    std::cout<<'\n';
}
int main() {
    std::string line;unsigned cases=0;
    while(std::getline(std::cin,line)) {
        std::istringstream in(line);uint32_t argument=0,last=0;unsigned fallback=0,count=0;
        if(!(in>>argument>>fallback>>last>>count) || fallback>65535 || count>1000)return 2;
        auto model=mt::ShuffledLcgModel::initialized(argument,static_cast<uint16_t>(fallback),last);
        emit(model);
        for(unsigned i=0;i<count;++i) {
            int one=0,bound=0;
            if(!(in>>one>>bound) || (one!=0 && one!=1))return 2;
            if(one)model.oneBased(bound);else model.zeroBased(bound);
            emit(model);
        }
        std::string extra;if(in>>extra)return 2;
        ++cases;
    }
    return cases ? 0 : 3;
}
