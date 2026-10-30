#include "engine/child_record_factory_model.hpp"
#include <cassert>
#include <initializer_list>
using M=mt::ChildRecordFactoryModel;
static unsigned word(const M::Record& r,unsigned p) {return (unsigned(r[p])<<8)|r[p+1];}
static void put(M::Record& r,unsigned p,unsigned value) {r[p]=static_cast<uint8_t>(value>>8);r[p+1]=static_cast<uint8_t>(value);}
static uint32_t long_word(const M::Record& r,unsigned p) {
    return (uint32_t(r[p])<<24)|(uint32_t(r[p+1])<<16)|(uint32_t(r[p+2])<<8)|r[p+3];
}
static bool equal(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
static bool equal(const M::Context& a,const M::Context& b) {
    return a.lookup==b.lookup && a.factor_word==b.factor_word && a.counter==b.counter && a.address_base==b.address_base;
}
static mt::ShuffledLcgModel rng(std::initializer_list<uint32_t> values) {
    for(uint32_t seed=1;seed<10000;++seed) {
        mt::ShuffledLcgModel::State s;s.selector_seed=seed;s.local_seed=42;s.last_result=123;
        auto selector=seed;std::array<bool,100> used{};bool distinct=true;
        for(auto value:values) {
            selector=selector*1103515245u+12345u;const auto index=((selector>>16)&32767u)%100;
            if(used[index]) {distinct=false;break;}
            used[index]=true;s.table[index]=value;
        }
        if(distinct)return mt::ShuffledLcgModel(s);
    }
    throw std::logic_error("no distinct authored slots");
}
static M::Record source(unsigned type) {
    M::Record record;record.fill(0xa5);put(record,0,type);put(record,10,1);record[24]=0;
    return record;
}
int main() {
    M::Templates templates{};M::Record out{};M::Context context;
    context.lookup.fill(255);context.factor_word=65535;context.counter=65535;context.address_base=0xfffffff0u;
    for(unsigned type:{37u,77u,137u,138u})assert(!M::supportsType(type) && M::supportsType(type,true));
    for(unsigned type:{36u,70u,166u,65536u})assert(!M::supportsType(type,true));
    // Missing context remains a rejection, including when the prefix could draw.
    for(unsigned type:{37u,77u,137u,138u}) {
        templates[0]=source(type);put(templates[0],10,32767);
        out.fill(0x5a);const auto before=out;const auto context_before=context;
        auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,0,0,random);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(random.state(),state) && equal(context,context_before));
    }
    for(unsigned type:{36u,70u,166u}) {
        templates[0]=source(type);out.fill(0x5a);const auto before=out;const auto context_before=context;
        auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,0,0,random,context);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(state,random.state()) && equal(context,context_before));
    }
    for(const auto& values:std::initializer_list<std::array<int,2>>{{-1,0},{32768,0},{0,-32769},{0,32768}}) {
        templates[0]=source(137);out.fill(0x5a);const auto before=out;const auto context_before=context;
        auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,values[0],values[1],random,context);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(state,random.state()) && equal(context,context_before));
    }
    // Lookup values straddle every exclusion and signed-byte decision boundary.
    struct LookupCase {unsigned value;bool eligible;};
    for(const auto& c:std::initializer_list<LookupCase>{{0,true},{1,true},{2,false},{3,true},{4,false},
            {5,true},{6,false},{7,true},{32,true},{33,false},{34,true},{127,true},{128,true},{255,true}}) {
        for(unsigned gate:{0u,1u,4u})for(unsigned delta:{0u,2u}) {
            templates[0]=source(37);put(templates[0],14,65535);auto expected=templates[0];put(expected,8,17);
            context.lookup.fill(2);context.lookup[17]=static_cast<uint8_t>(c.value);const auto before=context;
            const auto source_before=templates;auto random=rng({17,gate,delta});auto expected_rng=random;
            assert(expected_rng.zeroBased(50)==17);std::vector<M::Draw> trace{{50,0,17}};
            if(c.eligible) {
                assert(expected_rng.zeroBased(5)==gate);trace.push_back({5,0,gate});
                if(gate==0) {
                    const auto count=delta+1;assert(expected_rng.oneBased(3)==count);trace.push_back({3,1,count});
                    put(expected,10,count);put(expected,14,65535u*count);
                }
            }
            const auto result=M::prepare(out,templates,0,0,random,context);
            assert(out==expected && result.draws==trace && equal(random.state(),expected_rng.state()));
            assert(equal(context,before) && templates==source_before);
        }
    }
    // Every index reads its own authored byte, including both lookup boundaries.
    context.lookup.fill(2);
    for(unsigned index=0;index<50;++index) {
        templates[0]=source(37);auto random=rng({index});const auto result=M::prepare(out,templates,0,0,random,context);
        assert(word(out,8)==index && (result.draws==std::vector<M::Draw>{{50,0,index}}));
    }
    // Signed byte multiplication and positive/nonpositive caller-word branches.
    for(int level:{-32768,-5,-1,0,1,127,128,255,256,32767})
        for(unsigned factor:{0u,1u,32767u,32768u,65535u})
            for(unsigned byte:{0u,1u,127u,128u,255u})for(unsigned old_word:{0u,65535u}) {
                templates[0]=source(77);templates[0][6]=3;templates[0][7]=static_cast<uint8_t>(byte);put(templates[0],16,old_word);
                context.factor_word=static_cast<uint16_t>(factor);const auto before=context;auto expected=templates[0];
                expected[2]=static_cast<uint8_t>(level);put(expected,8,level>0?7:10);
                if(level>0) {expected[6]=252;expected[7]=4;put(expected,16,old_word+10u);}
                const int signed_byte=expected[7]<128?int(expected[7]):int(expected[7])-256;
                const int signed_factor=factor<32768?int(factor):int(factor)-65536;
                put(expected,4,static_cast<uint16_t>(signed_byte*signed_factor));
                auto random=rng({});const auto state=random.state();const auto result=M::prepare(out,templates,0,level,random,context);
                assert(out==expected && result.draws.empty() && equal(state,random.state()) && equal(context,before));
            }
    // Counter and arithmetic-address wrapping publish with output and RNG.
    for(unsigned type:{137u,138u})for(unsigned counter:{0u,1u,32767u,32768u,65535u})
        for(uint32_t base:{0u,1u,0xfffffff0u,0xffffffffu,0x80000000u})for(unsigned draw:{0u,1u,499u}) {
            templates[0]=source(type);context.counter=static_cast<uint16_t>(counter);context.address_base=base;
            const auto before=context;auto random=rng({draw});auto expected_rng=random;assert(expected_rng.zeroBased(500)==draw);
            const auto result=M::prepare(out,templates,0,0,random,context);
            auto expected=templates[0];put(expected,40,counter+1u);expected[24]|=8;
            const uint32_t address=base+5000u-draw;
            for(unsigned i=0;i<4;++i)expected[42+i]=static_cast<uint8_t>(address>>(24-8*i));
            assert(out==expected && word(out,40)==static_cast<uint16_t>(counter+1u) && long_word(out,42)==address);
            assert(context.counter==static_cast<uint16_t>(counter+1u) && context.lookup==before.lookup && context.factor_word==before.factor_word && context.address_base==before.address_base);
            assert(equal(random.state(),expected_rng.state()) && (result.draws==std::vector<M::Draw>{{500,0,draw}}));
        }
    // The explicit context overload preserves unrelated context for ordinary cases.
    templates[0]=source(39);const auto before=context;auto random=rng({199});
    const auto ordinary=M::prepare(out,templates,0,0,random,context);
    assert(word(out,22)==200 && ordinary.draws.size()==1 && equal(before,context));
    // Maximum eight prefix draws followed by all three type-37 context draws.
    templates[0]=source(37);templates[0][24]=32;templates[0][6]=1;put(templates[0],10,2);put(templates[0],14,1);
    context.lookup.fill(2);context.lookup[49]=255;const auto context_before=context;
    random=rng({1,1,0,9,1,0,0,2,49,0,2});auto expected_rng=random;
    const std::vector<M::Draw> trace{{2,1,2},{20,0,1},{20,0,0},{10,1,10},{20,0,1},{20,0,0},{10,0,0},{3,1,3},{50,0,49},{5,0,0},{3,1,3}};
    for(const auto& d:trace)assert((d[1]?expected_rng.oneBased(static_cast<int>(d[0])):expected_rng.zeroBased(static_cast<int>(d[0])))==d[2]);
    const auto result=M::prepare(out,templates,0,0,random,context);
    assert(result.draws==trace && word(out,8)==49 && word(out,10)==3 && word(out,14)==3 && out[6]==0);
    assert(equal(random.state(),expected_rng.state()) && equal(context,context_before));
}
