#include "engine/child_record_factory_model.hpp"
#include <cassert>
#include <initializer_list>
using M=mt::ChildRecordFactoryModel;
static unsigned word(const M::Record& r,unsigned p) {return (unsigned(r[p])<<8)|r[p+1];}
static void put(M::Record& r,unsigned p,unsigned n) {r[p]=static_cast<uint8_t>(n>>8);r[p+1]=static_cast<uint8_t>(n);}
static bool equal(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
static mt::ShuffledLcgModel rng(std::initializer_list<uint32_t> values) {
    for(uint32_t seed=1;seed<10000;++seed) {
        mt::ShuffledLcgModel::State state;state.local_seed=42;state.selector_seed=seed;state.last_result=123;
        auto selector=seed;std::array<bool,100> used{};bool distinct=true;
        for(auto value:values) {
            selector=selector*1103515245u+12345u;const auto index=((selector>>16)&32767u)%100u;
            if(used[index]) {distinct=false;break;}
            used[index]=true;state.table[index]=value;
        }
        if(distinct)return mt::ShuffledLcgModel(state);
    }
    throw std::logic_error("no distinct authored shuffle slots");
}
static M::Record source(unsigned type) {
    M::Record result;result.fill(0xa5);put(result,0,type);put(result,10,1);result[24]=0;
    return result;
}
int main() {
    M::Templates templates{};M::Record out{};
    assert(!M::supportsType(65536));
    for(unsigned type:{36u,37u,70u,77u,137u,138u,166u}) {
        templates[0]=source(type);put(templates[0],10,32767);templates[0][24]=32;templates[0][6]=1;
        out.fill(0x5a);const auto before=out;auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,0,0,random);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(state,random.state()));
    }
    templates[0]=source(0);
    for(int invalid:{-32769,-32768,-1,32768,65535}) {
        out.fill(0x5a);const auto before=out;auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,invalid,0,random);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(state,random.state()));
    }
    for(int invalid:{-32769,32768}) {
        out.fill(0x5a);const auto before=out;auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,0,invalid,random);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(state,random.state()));
    }
    // Unmodified dispatcher entries and raw-word range defaults preserve all bytes.
    for(unsigned type:{0u,24u,26u,35u,38u,71u,168u,32767u,32768u,65535u}) {
        for(int variant:{0,136,137,32767}) {
            const unsigned index=variant<=136?static_cast<unsigned>(variant):0;
            templates[index]=source(type);const auto before=templates;auto random=rng({});const auto state=random.state();
            const auto result=M::prepare(out,templates,variant,-32768,random);
            assert(out==templates[index] && result.selected_template==index && result.draws.empty());
            assert(templates==before && equal(state,random.state()));
        }
    }
    // Single-draw cases replace their raw fields and preserve complete RNG state.
    for(unsigned type:{39u,63u,81u,141u,109u,108u,100u}) {
        templates[0]=source(type);put(templates[0],14,65535);auto expected=templates[0];
        unsigned bound=0,field=0;bool one=true;
        switch(type) {
        case 39:bound=200;field=22;break;
        case 63:bound=5;field=8;break;
        case 100:bound=50;field=8;one=false;break;
        case 81:case 141:bound=20;field=14;break;
        case 109:bound=10;field=14;break;
        case 108:bound=5;field=14;break;
        }
        auto random=rng({199});auto expected_rng=random;
        const auto value=one?expected_rng.oneBased(static_cast<int>(bound)):expected_rng.zeroBased(static_cast<int>(bound));
        put(expected,field,field==14?65535+value:value);
        const auto result=M::prepare(out,templates,0,0,random);
        assert(out==expected && equal(random.state(),expected_rng.state()));
        assert((result.draws==std::vector<M::Draw>{{bound,one?1u:0u,value}}));
    }
    // Nonpositive signed bounds still store one but must not advance the seeds/table.
    for(unsigned type:{114u,116u})for(unsigned bound:{0u,1u,2u,32767u,32768u,65535u}) {
        templates[0]=source(type);put(templates[0],22,bound);auto expected=templates[0];
        auto random=rng({32766});auto expected_rng=random;const int signed_bound=bound<32768?int(bound):int(bound)-65536;
        const auto value=expected_rng.oneBased(signed_bound);put(expected,22,value);
        const auto result=M::prepare(out,templates,0,0,random);
        assert(out==expected && equal(random.state(),expected_rng.state()));
        assert((result.draws==std::vector<M::Draw>{{bound,1,value}}));
    }
    // Word-sized wrap occurs before type 62's signed comparisons and reroll.
    struct LevelCase {int level;unsigned first,second,result;bool reroll;};
    for(const auto& c:std::initializer_list<LevelCase>{{-32768,0,4,0,false},{-32768,10,3,3,true},
            {0,0,4,4,true},{5,0,0,0,false},{19,0,0,14,false},{20,0,0,0,false},
            {32767,10,2,2,true},{32767,0,0,0,false}}) {
        templates[0]=source(62);auto expected=templates[0];put(expected,8,c.result);
        auto random=rng({c.first,c.second});auto expected_rng=random;
        assert(expected_rng.zeroBased(11)==c.first);if(c.reroll)assert(expected_rng.zeroBased(5)==c.second);
        const auto result=M::prepare(out,templates,0,c.level,random);
        assert(out==expected && equal(random.state(),expected_rng.state()));
        assert(result.draws.size()==(c.reroll?2u:1u));
    }
    // Division is signed and truncates toward zero, including negative fractions.
    struct DivideCase {int level;unsigned field,delta;};
    for(const auto& c:std::initializer_list<DivideCase>{{-32768,33,0},{-5,33,0},{-4,13,7},
            {-1,13,7},{0,13,7},{9,13,7},{10,2,4},{14,2,4},{15,33,0},{32767,33,0}}) {
        templates[0]=source(25);templates[0][6]=1;auto expected=templates[0];
        expected[6]=static_cast<uint8_t>(1u-c.delta);put(expected,8,c.field);
        auto random=rng({});const auto state=random.state();const auto result=M::prepare(out,templates,0,c.level,random);
        assert(out==expected && result.draws.empty() && equal(state,random.state()));
    }
    for(unsigned type:{93u,94u,95u,96u,97u,98u,101u,140u,164u,165u,167u,143u,144u}) {
        templates[0]=source(type);auto expected=templates[0];
        if(type==144)expected[13]=3;
        else if(type==140 || type==164 || type==165 || type==167)expected[24]|=8;
        else expected[25]|=4;
        auto random=rng({});const auto state=random.state();const auto result=M::prepare(out,templates,0,0,random);
        assert(out==expected && result.draws.empty() && equal(state,random.state()));
    }
    for(unsigned value:{0u,1u,3u}) {
        templates[0]=source(129);auto expected=templates[0];expected[2]=value?1:2;
        auto random=rng({value});const auto result=M::prepare(out,templates,0,0,random);
        assert(out==expected && (result.draws==std::vector<M::Draw>{{4,0,value}}));
    }
    // Type 127 reads the caller's slot-42 word, not the selected source word.
    for(unsigned factor:{0u,1u,32767u,32768u,65535u}) {
        templates[0]=source(127);put(templates[0],14,1);put(templates[42],14,factor);const auto before=templates;
        auto expected=templates[0];put(expected,22,4);put(expected,14,1+factor*4u);
        auto random=rng({4});auto expected_rng=random;assert(expected_rng.zeroBased(5)==4);
        const auto result=M::prepare(out,templates,0,0,random);
        assert(out==expected && templates==before && equal(random.state(),expected_rng.state()));
        assert((result.draws==std::vector<M::Draw>{{5,0,4}}));
    }
    // Compose the maximum eight-draw prefix with both type-62 dispatch draws.
    templates[0]=source(62);templates[0][24]=32;templates[0][6]=1;put(templates[0],10,2);put(templates[0],14,1);
    auto random=rng({1,1,0,9,1,0,0,2,0,4});auto expected_rng=random;
    const std::vector<M::Draw> trace{{2,1,2},{20,0,1},{20,0,0},{10,1,10},{20,0,1},{20,0,0},{10,0,0},{3,1,3},{11,0,0},{5,0,4}};
    for(const auto& d:trace)assert((d[1]?expected_rng.oneBased(static_cast<int>(d[0])):expected_rng.zeroBased(static_cast<int>(d[0])))==d[2]);
    const auto result=M::prepare(out,templates,0,0,random);
    assert(result.draws==trace && word(out,10)==2 && word(out,14)==1 && out[6]==0 && word(out,8)==4);
    assert(equal(random.state(),expected_rng.state()));
}
