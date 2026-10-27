#pragma once
#include "basic_cell_conversion_model.hpp"
#include "shuffled_lcg_model.hpp"
#include <optional>

namespace mt {
// Six more raw glyph branches. Names describe fields, not terrain semantics.
class LevelCellConversionModel {
public:
    using Cell=BasicCellConversionModel::Cell;
    struct Context {
        BasicCellConversionModel::Context direct;
        uint16_t tuning31,tuning32,tuning34;
    };
    static bool supported(uint8_t glyph) {
        return glyph==215 || glyph==175 || glyph==187 || glyph==171 || glyph==94 || glyph==118;
    }
    // A result is present only when this branch consumes one one-based bound-3 draw.
    static std::optional<uint32_t> convert(uint8_t glyph,Cell& cell,const Context& context,ShuffledLcgModel& rng) {
        if(!supported(glyph))throw std::invalid_argument("unsupported level glyph");
        const auto& c=context.direct;
        if(c.level < -32768 || c.level > 32767)throw std::invalid_argument("level must fit word");
        auto add=[&](uint32_t delta) {
            const auto word=static_cast<uint16_t>(((cell[2]<<8)|cell[3])+delta);
            cell[2]=static_cast<uint8_t>(word>>8);cell[3]=static_cast<uint8_t>(word);
        };
        if(!(c.flags6&16))add(static_cast<uint16_t>((c.byte8<128?int(c.byte8):int(c.byte8)-256)*10));
        std::optional<uint32_t> draw;
        switch(glyph) {
        case 215:cell[0]=34;cell[1]=c.flags6&16?87:89;add(context.tuning34);break;
        case 175:cell[0]=34;cell[1]=88;add(context.tuning34);break;
        case 187:case 171:
            cell[0]=glyph==187?32:31;cell[4]|=4;add(glyph==187?context.tuning32:context.tuning31);
            cell[9]=static_cast<uint8_t>(c.level+(glyph==187?1:-1));break;
        case 94:case 118:
            cell[0]=0;
            if(c.level==0)add(c.tuning[0]);
            else {
                add(glyph==94?context.tuning31:context.tuning32);cell[4]|=4;
                draw=rng.oneBased(3);
                cell[9]=static_cast<uint8_t>(c.level+(glyph==94?-int(*draw):int(*draw)));
            }
            break;
        }
        BasicCellConversionModel::adjustSubtype(cell);return draw;
    }
};
}
