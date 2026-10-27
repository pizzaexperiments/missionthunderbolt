#pragma once
#include "basic_cell_conversion_model.hpp"
#include "grid_record_layout.hpp"

namespace mt {
// Partial generator traversal: all cells must use the already verified direct
// branches. Neither original allocation nor creation/RNG branches are modeled.
class DirectGridConversionModel {
public:
    static constexpr unsigned count=GridRecordLayout::rows*GridRecordLayout::columns;
    using Glyphs=std::array<uint8_t,count>;
    using Records=std::array<BasicCellConversionModel::Cell,count>;
    using Context=BasicCellConversionModel::Context;
    // CODE 6 entry 9816 consumes a signed word; coordinate byte arguments are unused.
    static uint16_t baseWord(int raw_word) {
        if(raw_word < -32768 || raw_word > 32767)throw std::invalid_argument("level must fit word");
        return raw_word>=16 && raw_word<=29 ? 250 : raw_word>=30 ? 1000 : 0;
    }
    static void convert(const Glyphs& glyphs,Records& records,const Context& context) {
        if(context.level < -32768 || context.level > 32767)throw std::invalid_argument("level must fit word");
        // Model capability check is atomic. The original has no such preflight.
        for(auto glyph:glyphs)if(!BasicCellConversionModel::supported(glyph))
            throw std::invalid_argument("grid contains unmodeled conversion/service");
        const int next=context.level==32767 ? -32768 : context.level+1;
        const uint16_t seed=baseWord(next);
        for(unsigned row=0;row<GridRecordLayout::rows;++row)
            for(unsigned column=0;column<GridRecordLayout::columns;++column) {
                const unsigned index=row*GridRecordLayout::columns+column;
                auto& cell=records[index];
                cell[2]=static_cast<uint8_t>(seed>>8);cell[3]=static_cast<uint8_t>(seed);
                BasicCellConversionModel::convert(glyphs[index],cell,context);
            }
    }
};
}
