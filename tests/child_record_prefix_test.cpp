#include "engine/child_record_prefix_model.hpp"
#include <cassert>
#include <initializer_list>
using M=mt::ChildRecordPrefixModel;
static unsigned word(const M::Record& r,unsigned p) {return (unsigned(r[p])<<8)|r[p+1];}
static void put(M::Record& r,unsigned p,unsigned n) {r[p]=static_cast<uint8_t>(n>>8);r[p+1]=static_cast<uint8_t>(n);}
static bool equal(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
// Assign authored shuffle values to distinct sequential selector indices. This
// controls branch decisions while using the production RNG and its full state.
static mt::ShuffledLcgModel rng(std::initializer_list<uint32_t> values) {
    mt::ShuffledLcgModel::State s;s.selector_seed=1;s.local_seed=42;
    uint32_t selector=s.selector_seed;std::array<bool,100> used{};
    for(auto value:values) {
        selector=selector*1103515245u+12345u;const auto index=((selector>>16)&32767u)%100u;
        assert(!used[index]);used[index]=true;s.table[index]=value;
    }
    return mt::ShuffledLcgModel(s);
}
int main() {
    M::Templates templates{};M::Record out{};
    for(unsigned i=0;i<templates.size();++i)templates[i].fill(static_cast<uint8_t>(i));
    for(int variant:{0,1,136,137,32767}) {
        const unsigned selected=variant<=136?static_cast<unsigned>(variant):0;
        // Disable both optional sections, preserving every copied byte.
        put(templates[selected],10,1);templates[selected][24]=0;
        auto random=rng({});const auto before=random.state();
        const auto result=M::prepare(out,templates,variant,random);
        assert(result.selected_template==selected && result.draws.empty());
        assert(out==templates[selected] && equal(before,random.state()));
    }
    for(int invalid:{-32768,-1,32768}) {
        out.fill(0x5a);const auto before=out;auto random=rng({});const auto state=random.state();bool rejected=false;
        try {(void)M::prepare(out,templates,invalid,random);}catch(const std::invalid_argument&){rejected=true;}
        assert(rejected && out==before && equal(state,random.state()));
    }
    auto& t=templates[0];t.fill(0);put(t,10,32767);put(t,14,65535);
    auto random=rng({32766});auto expected=random;assert(expected.oneBased(32767)==32767);
    auto result=M::prepare(out,templates,0,random);
    assert(word(out,10)==32767 && word(out,14)==32769 && equal(expected.state(),random.state()));
    assert((result.draws==std::vector<M::Draw>{{32767,1,32767}}));
    for(unsigned count:{0u,1u,32768u,65535u}) {
        put(t,10,count);random=rng({});const auto state=random.state();
        result=M::prepare(out,templates,0,random);assert(result.draws.empty() && word(out,10)==count && equal(state,random.state()));
    }
    t.fill(0);t[24]=32;t[6]=1;put(t,10,2);put(t,14,1);
    random=rng({1,1,0,9,1,0,0,2});expected=random;
    const std::vector<M::Draw> trace{{2,1,2},{20,0,1},{20,0,0},{10,1,10},{20,0,1},{20,0,0},{10,0,0},{3,1,3}};
    for(const auto& d:trace)assert((d[1]?expected.oneBased(d[0]):expected.zeroBased(d[0]))==d[2]);
    result=M::prepare(out,templates,0,random);
    assert(result.draws==trace && word(out,10)==2 && word(out,14)==1 && out[6]==0 && equal(expected.state(),random.state()));
    // Word subtraction wraps before the signed clamp: 0x8000 - 1 becomes 0x7fff.
    put(t,10,1);put(t,14,32768);random=rng({1,0,0,1,1});
    result=M::prepare(out,templates,0,random);assert(word(out,14)==32767 && out[6]==1 && result.draws.size()==5);
    // Word addition wraps without clamping; byte addition also retains wrapping.
    put(t,14,65535);t[6]=255;random=rng({0,0,0,0,2});
    result=M::prepare(out,templates,0,random);assert(word(out,14)==0 && out[6]==2 && result.draws.size()==5);
    // Both failed word gates precede both byte gates; dispatch is not executed.
    t.fill(0xa5);put(t,0,65535);put(t,10,1);put(t,14,456);t[24]=32;t[6]=9;
    random=rng({1,1,1,1});result=M::prepare(out,templates,0,random);
    assert(out==t && (result.draws==std::vector<M::Draw>{{20,0,1},{20,0,1},{20,0,1},{20,0,1}}));
    // Bit 1 and raw type 71 independently skip word variation, not byte variation.
    for(unsigned gate:{0u,1u}) {
        t.fill(0);t[24]=static_cast<uint8_t>(32|(gate?2:0));t[6]=127;put(t,0,gate?0:71);put(t,14,456);
        random=rng({0,1});result=M::prepare(out,templates,0,random);
        assert(word(out,14)==456 && out[6]==128 && result.draws.size()==2);
        t[6]=128;random=rng({1,0,1});result=M::prepare(out,templates,0,random);assert(out[6]==127 && result.draws.size()==3);
        t[6]=255;random=rng({1,0,1});result=M::prepare(out,templates,0,random);assert(out[6]==0);
        t[6]=1;random=rng({1,0,0,2});result=M::prepare(out,templates,0,random);assert(out[6]==0 && result.draws.size()==4);
    }
    for(unsigned gate:{0u,1u}) {
        t.fill(0);t[24]=gate?32:0;t[6]=gate?0:9;put(t,14,99);random=rng({});const auto before=random.state();
        result=M::prepare(out,templates,0,random);assert(out==t && result.draws.empty() && equal(before,random.state()));
    }
}
