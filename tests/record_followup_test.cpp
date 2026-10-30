#include "engine/record_followup_model.hpp"
#include <cassert>
using M=mt::RecordFollowupModel;
static void slot(M::Record& r,unsigned index,uint32_t id) {
    for(unsigned i=0;i<4;++i)r[60+4*index+i]=static_cast<uint8_t>(id>>(24-8*i));
}
int main() {
    M::Context c{};c.template_flags[1]=32;c.template_flags[72]=32;c.thresholds.fill(-1);
    M::Record r{};r[1]=1;r[51]=3;slot(r,0,100);slot(r,1,200);slot(r,2,300);
    M::Children children{{100,{}},{200,{}},{300,{}}};
    for(auto& pair:children)pair.second[17]=5;
    const auto before_children=children;M::apply(r,children,c);
    assert(r[22]==2 && (r[20]&32) && children==before_children); // Equal scores retain highest slot.
    children[300][24]=2;M::apply(r,children,c);assert(r[22]==1 && (r[20]&32));
    children[200][25]=2;children[100][24]=8;M::apply(r,children,c);assert(r[22]==0 && !(r[20]&32));
    children[100][24]=0;M::apply(r,children,c);assert(r[22]==0 && (r[20]&32)); // Slot zero is a selection.
    r[1]=72;r[18]=255;children[200][18]=1;children[200][1]=77;children[200][8]=0xff;children[200][9]=0xff;
    children[300][18]=1;children[300][1]=88;children[300][9]=1;
    M::apply(r,children,c);assert(r[18]==88); // First eligible reverse slot, not maximum.
    r[1]=1;r[51]=0;r[22]=12;r[20]=255;M::apply(r,children,c);assert(r[22]==0 && r[20]==223);
    r[51]=14;const auto before=r;bool rejected=false;
    try {M::apply(r,children,c);}catch(const std::out_of_range&){rejected=true;}assert(rejected && r==before);
    r[51]=1;slot(r,0,999);const auto missing=r;rejected=false;
    try {M::apply(r,children,c);}catch(const std::invalid_argument&){rejected=true;}assert(rejected && r==missing);
    c.template_flags[1]=0;M::apply(r,children,c);assert(r[22]==0); // No child dereference on this path.
}
