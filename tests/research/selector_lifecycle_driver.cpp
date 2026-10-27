#include "selector_lifecycle_fixture.hpp"
#include "engine/a5_initialization_model.hpp"
static std::vector<uint8_t> decode(const std::string& text) {
    if(text.size()%2)throw std::invalid_argument("odd startup hex");
    std::vector<uint8_t> result;
    for(size_t i=0;i<text.size();i+=2) {
        auto nibble=[](char c)->unsigned {if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::invalid_argument("bad startup hex");};
        result.push_back(static_cast<uint8_t>((nibble(text[i])<<4)|nibble(text[i+1])));
    }
    return result;
}
int main(int argc,char** argv) {
    const bool startup=argc==2 && std::string(argv[1])=="--startup-data";
    if(argc!=1 && !startup)return 2;
    mt::GridCandidateSelector::Directions directions{};
    if(startup) {
        size_t below,above;std::string data,zero,relocations;
        if(!(std::cin>>below>>above>>data>>zero>>relocations) || above>65536)return 2;
        auto expanded=mt::A5InitializationModel::expand(decode(data),decode(zero),below);
        auto image=expanded.bytes;image.resize(below+above,0x5a);
        mt::A5InitializationModel::relocate(image,below,decode(relocations),0x80000,0x10000);
        directions=mt::A5InitializationModel::directions(image,below);
    }
    lifecycle_fixture::Config c{};unsigned cases=0;
    while(std::cin>>c.seed>>c.directions>>c.profile>>c.shape>>c.prefix>>c.word>>c.flags>>c.count>>c.row>>c.column>>c.position) {
        if(c.directions>2 || c.profile>8 || c.shape>1 || c.prefix>65535 || c.word>65535 || c.flags>255 || c.count>3 || c.row<1 || c.row>17 || c.column<1 || c.column>65 || c.position>2)return 2;
        lifecycle_fixture::World world(c);auto rng=mt::ShuffledLcgModel::initialized(c.seed,42,123);
        const auto result=lifecycle_fixture::run(world,c,rng,startup?&directions:nullptr);lifecycle_fixture::write(world,result,rng);++cases;
    }
    return std::cin.eof() && cases?0:2;
}
