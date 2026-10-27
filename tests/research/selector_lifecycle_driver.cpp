#include "selector_lifecycle_fixture.hpp"
int main() {
    lifecycle_fixture::Config c{};unsigned cases=0;
    while(std::cin>>c.seed>>c.directions>>c.profile>>c.shape>>c.prefix>>c.word>>c.flags>>c.count>>c.row>>c.column>>c.position) {
        if(c.directions>2 || c.profile>8 || c.shape>1 || c.prefix>65535 || c.word>65535 || c.flags>255 || c.count>3 || c.row<1 || c.row>17 || c.column<1 || c.column>65 || c.position>2)return 2;
        lifecycle_fixture::World world(c);auto rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);
        const auto result=lifecycle_fixture::run(world,c,rng);lifecycle_fixture::write(world,result,rng);++cases;
    }
    return std::cin.eof() && cases?0:2;
}
