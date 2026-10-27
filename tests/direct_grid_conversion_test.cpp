#include "engine/direct_grid_conversion_model.hpp"
#include <cassert>
using M=mt::DirectGridConversionModel;
int main() {
    assert(M::baseWord(-32768)==0 && M::baseWord(15)==0);
    assert(M::baseWord(16)==250 && M::baseWord(29)==250);
    assert(M::baseWord(30)==1000 && M::baseWord(32767)==1000);
    M::Glyphs glyphs;glyphs.fill(32);M::Records records;
    for(auto& cell:records)cell.fill(0xa5);
    // Every cell's previous word is overwritten; all other untouched fields survive.
    for(int level:{-32768,14,15,28,29,32767}) {
        M::convert(glyphs,records,{0,255,level,{11,22,33}});
        const unsigned expected=level==15 || level==28 ? 251 : level==29 ? 1001 : 1;
        for(auto& cell:records) {
            assert(cell[0]==0 && cell[1]==0xa5 && ((cell[2]<<8)|cell[3])==int(expected));
            for(unsigned i=4;i<20;++i)assert(cell[i]==0xa5);
        }
    }
    glyphs.fill(32);glyphs[0]=80;glyphs[66]=112;glyphs[67]=198;glyphs.back()=37;
    for(auto& cell:records)cell.fill(0);
    M::convert(glyphs,records,{0,0,15,{1,2,3}});
    assert(records[0][0]==1 && records[0][1]==45 && records[0][4]==16 && records[0][3]==252);
    assert(records[66][0]==1 && records[66][1]==45 && records[66][4]==0);
    assert(records[67][0]==2 && records[67][1]==62 && records[67][4]==64);
    assert(records.back()[0]==2 && records.back()[1]==52 && records.back()[5]==128 && records.back()[2]==1 && records.back()[3]==3);
    const auto before=records;glyphs.back()=46;
    bool rejected=false;try {M::convert(glyphs,records,{0,0,15,{1,2,3}});}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && records==before);
    glyphs.back()=32;rejected=false;
    try {M::convert(glyphs,records,{0,0,32768,{1,2,3}});}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected && records==before);
}
