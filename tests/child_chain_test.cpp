#include "engine/child_chain_model.hpp"
#include <cassert>
#include <initializer_list>
using M=mt::ChildChainModel;
static void put(M::Record& record,unsigned offset,unsigned value) {
    record[offset]=static_cast<uint8_t>(value>>8);record[offset+1]=static_cast<uint8_t>(value);
}
static void putLong(M::Record& record,unsigned offset,uint32_t value) {
    for(unsigned i=0;i<4;++i)record[offset+i]=static_cast<uint8_t>(value>>(24u-i*8u));
}
static unsigned word(const M::Record& record,unsigned offset) {return (unsigned(record[offset])<<8)|record[offset+1];}
static uint32_t longWord(const M::Record& record,unsigned offset) {
    return (uint32_t(record[offset])<<24)|(uint32_t(record[offset+1])<<16)
           |(uint32_t(record[offset+2])<<8)|record[offset+3];
}
static bool equal(const mt::ShuffledLcgModel::State& a,const mt::ShuffledLcgModel::State& b) {
    return a.local_seed==b.local_seed && a.selector_seed==b.selector_seed && a.last_result==b.last_result && a.table==b.table;
}
static bool equal(const M::Context& a,const M::Context& b) {
    return a.lookup==b.lookup && a.factor_word==b.factor_word && a.counter==b.counter && a.address_base==b.address_base;
}
static M::Templates templates() {
    M::Templates table{};
    for(unsigned i=0;i<table.size();++i) {
        for(unsigned j=0;j<56;++j)table[i][j]=static_cast<uint8_t>(i*17u+j*31u);
        put(table[i],0,i);put(table[i],10,1);table[i][24]=0;
    }
    return table;
}
static M::Record parent() {
    M::Record record{};record.fill(0x5a);putLong(record,30,0);return record;
}
static mt::ShuffledLcgModel forced(std::initializer_list<uint32_t> values) {
    for(uint32_t selector=1;selector<10000;++selector) {
        mt::ShuffledLcgModel::State state;state.local_seed=42;state.selector_seed=selector;state.last_result=123;
        auto seed=selector;std::array<bool,100> used{};bool distinct=true;
        for(const auto value:values) {
            seed=seed*1103515245u+12345u;const auto index=((seed>>16)&32767u)%100u;
            if(used[index]) {distinct=false;break;}
            used[index]=true;state.table[index]=value;
        }
        if(distinct)return mt::ShuffledLcgModel(state);
    }
    throw std::logic_error("no distinct authored RNG slots");
}
static const M::Handles handles{{0x20000,0x20038,0x20070,0x200a8,0x200e0}};
static void checkKnownTrace() {
    auto table=templates();auto root=parent();M::Records records{};M::Context context{};context.lookup.fill(2);
    const auto before_table=table;const auto before_parent=root;const auto before_context=context;
    auto rng=forced({0,49,0,2,199,24});
    const auto result=M::prepare(root,0x10000,records,handles,table,rng,context);
    const std::array<unsigned,5> expected{{201,75,26,300,50}};
    const std::array<unsigned,5> variants{{31,27,28,37,72}};
    for(unsigned i=0;i<5;++i) {
        auto frozen=before_table[variants[i]];
        if(i==3)put(frozen,8,2); // The authored type-37 lookup draw.
        put(frozen,10,expected[i]);if(i<4)putLong(frozen,26,handles[i+1]);
        assert(records[i]==frozen);
        assert(word(records[i],14)==word(before_table[variants[i]],14));
        assert(word(records[i],10)==expected[i]);
        assert(longWord(records[i],26)==(i<4?handles[i+1]:longWord(table[72],26)));
    }
    assert(longWord(root,30)==handles[0]);
    for(unsigned i=0;i<56;++i)if(i<30 || i>=34)assert(root[i]==before_parent[i]);
    assert(table==before_table && equal(context,before_context));
    assert((result.factory_draw_counts==std::array<unsigned,5>{{0,0,0,1,0}}));
    const std::vector<M::Draw> expected_draws{{200,1,1},{50,1,50},{50,1,1},{50,0,2},{200,1,200},{25,1,25}};
    assert(result.draws==expected_draws);
}
static void checkComposedState() {
    for(unsigned seed=0;seed<128;++seed) {
        auto table=templates();const std::array<unsigned,5> variants{{31,27,28,37,72}};
        // These authored dispatch substitutions exercise shared context updates,
        // prefix draws, signed bounds and the two optional type-37 draws.
        put(table[31],0,137);put(table[27],0,138);put(table[28],0,77);
        for(unsigned i:variants) {put(table[i],10,3);table[i][24]=32;table[i][6]=1;}
        auto root=parent();M::Records records{},expected_records{};M::Context context{};
        context.lookup.fill(static_cast<uint8_t>(seed));context.counter=65535;
        context.address_base=0xfffffff0;context.factor_word=0x8000;
        auto expected_context=context;auto rng=mt::ShuffledLcgModel::initialized(seed,42,0x89abcdef);
        auto expected_rng=rng;std::vector<M::Draw> draws;
        const std::array<unsigned,5> bounds{{200,50,50,200,25}},biases{{200,25,25,100,25}};
        for(unsigned i=0;i<5;++i) {
            const auto result=M::Factory::prepare(expected_records[i],table,static_cast<int>(variants[i]),1,expected_rng,expected_context);
            draws.insert(draws.end(),result.draws.begin(),result.draws.end());
            const auto value=expected_rng.oneBased(static_cast<int>(bounds[i]));draws.push_back({bounds[i],1,value});
            put(expected_records[i],10,value+biases[i]);
            if(i)putLong(expected_records[i-1],26,handles[i]);
        }
        const auto result=M::prepare(root,0x10000,records,handles,table,rng,context);
        assert(records==expected_records && result.draws==draws);
        assert(equal(rng.state(),expected_rng.state()) && equal(context,expected_context));
        assert(context.counter==1);
    }
}
static void checkRejected(const M::Handles& supplied,uint32_t parent_handle,unsigned bad_variant=0) {
    auto table=templates();if(bad_variant)put(table[bad_variant],0,36);
    auto root=parent();M::Records records{};for(auto& record:records)record.fill(0xc3);
    M::Context context{};context.counter=65535;context.lookup.fill(128);
    auto rng=mt::ShuffledLcgModel::initialized(42,42,123);
    const auto old_root=root;const auto old_records=records;const auto old_context=context;const auto old_rng=rng.state();
    bool rejected=false;
    try {(void)M::prepare(root,parent_handle,records,supplied,table,rng,context);}
    catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected && root==old_root && records==old_records && equal(context,old_context) && equal(rng.state(),old_rng));
}
static void checkValidation() {
    assert(!M::Factory::supportsType(36,true));
    for(unsigned i=0;i<5;++i) {
        for(uint32_t invalid:{0u,1u,0xfffffff0u,0x10000u}) {
            auto bad=handles;bad[i]=invalid;checkRejected(bad,0x10000);
        }
        for(unsigned j=0;j<i;++j) {auto bad=handles;bad[i]=handles[j]+2u;checkRejected(bad,0x10000);}
    }
    for(uint32_t invalid:{0u,1u,0xfffffff0u,handles[2]})checkRejected(handles,invalid);
    for(unsigned variant:{31u,27u,28u,37u,72u})checkRejected(handles,0x10000,variant);
    auto table=templates();auto root=parent();M::Records records{};M::Context context{};auto rng=forced({});
    const auto frozen_context=context;const auto frozen_rng=rng.state();
    const auto frozen_table=table;const auto frozen_records=records;
    putLong(root,30,0x20000);const auto before=root;bool rejected=false;
    try {(void)M::prepare(root,0x10000,records,handles,table,rng,context);}catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected && root==before && records==frozen_records && table==frozen_table);
    assert(equal(context,frozen_context) && equal(rng.state(),frozen_rng));
    records[0]=parent();const auto before_records=records;rejected=false;
    try {(void)M::prepare(records[0],0x10000,records,handles,table,rng,context);}catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected && records==before_records && root==before && table==frozen_table);
    assert(equal(context,frozen_context) && equal(rng.state(),frozen_rng));
    table[0]=parent();const auto before_table=table;rejected=false;
    try {(void)M::prepare(table[0],0x10000,records,handles,table,rng,context);}catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected && table==before_table && records==before_records && root==before);
    assert(equal(context,frozen_context) && equal(rng.state(),frozen_rng));
    // Last valid word-aligned address with a nonwrapping 56-byte extent.
    root=parent();auto high=handles;high[4]=0xffffffc8u;context.lookup.fill(2);rng=forced({});
    (void)M::prepare(root,0x10000,records,high,table,rng,context);
    assert(longWord(records[3],26)==0xffffffc8u);
}
int main() {checkKnownTrace();checkComposedState();checkValidation();}
