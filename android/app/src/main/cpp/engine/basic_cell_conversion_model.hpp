#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>

namespace mt {
// Partial, instruction-checked conversion. No terrain/item names or unresolved
// creation callbacks are inferred; unsupported glyphs reject before mutation.
class BasicCellConversionModel {
public:
    using Cell=std::array<uint8_t,20>;
    struct Context {uint8_t flags6,byte8;int level;std::array<uint16_t,3> tuning;};
    static bool supported(uint8_t glyph) {
        switch(glyph) {
        case 32:case 119:case 80:case 112:case 120:case 35:case 38:case 37:
        case 92:case 195:case 96:case 196:case 39:case 197:case 47:case 198:
        case 177:case 176:case 200:case 164:case 213:case 166:case 211:case 188:
        case 217:case 163:case 161:case 162:case 212:case 210:case 172:case 140:
        case 201:case 190:case 173:case 199:case 185:case 191:case 180:case 123:
        case 125:case 40:case 41:return true;
        default:return false;
        }
    }
    static void adjustSubtype(Cell& cell) {
        if(!(cell[5]&128) && !(cell[4]&64) && !(cell[6]&15))return;
        if(cell[1]>=2 && cell[1]<=27)cell[1]=static_cast<uint8_t>(cell[1]+50);
        else if(cell[1]==0 && cell[0]>=2 && cell[0]<=27)cell[1]=static_cast<uint8_t>(cell[0]+50);
    }
    static void convert(uint8_t glyph,Cell& cell,const Context& context) {
        if(!supported(glyph))throw std::invalid_argument("glyph needs unmodeled conversion/service");
        if(context.level < -32768 || context.level > 32767)throw std::invalid_argument("level must fit word");
        auto add=[&](uint32_t delta) {
            const uint16_t value=static_cast<uint16_t>(((cell[2]<<8)|cell[3])+delta);
            cell[2]=static_cast<uint8_t>(value>>8);cell[3]=static_cast<uint8_t>(value);
        };
        if(!(context.flags6&16)) {
            const int signed_byte=context.byte8<128?int(context.byte8):int(context.byte8)-256;
            add(static_cast<uint16_t>(signed_byte*10));
        }
        switch(glyph) {
        case 32:cell[0]=0;add(context.tuning[0]);break;
        case 119:cell[0]=1;add(context.tuning[1]);break;
        case 80:cell[4]|=16;[[fallthrough]];
        case 112:cell[0]=1;cell[1]=45;add(context.tuning[1]);break;
        case 120:cell[0]=1;cell[1]=45;cell[4]|=8;add(context.tuning[1]);break;
        case 35:case 38:case 37:
            cell[0]=2;if(glyph==38)cell[4]|=64;
            if(context.flags6&16)cell[1]=82;
            add(uint32_t(context.tuning[2])*(glyph==37?3u:1u));
            if(glyph==37 && context.level!=0)cell[5]|=128;
            break;
        case 92:case 195:case 96:case 196:case 39:case 197:case 47:case 198: {
            const unsigned group=(glyph==92 || glyph==195)?0:(glyph==96 || glyph==196)?1:(glyph==39 || glyph==197)?2:3;
            if(glyph>=195)cell[4]|=64;
            cell[0]=2;cell[1]=static_cast<uint8_t>((context.flags6&16?83:9)+group);add(context.tuning[2]);break;
        }
        default: {
            uint8_t subtype=0;
            switch(glyph) {
            case 177:case 176:case 212:subtype=5;break;
            case 200:case 164:case 210:subtype=6;break;
            case 213:case 166:case 172:subtype=7;break;
            case 211:case 188:case 140:subtype=8;break;
            case 217:case 163:case 201:subtype=3;break;
            case 161:case 162:case 190:subtype=4;break;
            case 173:subtype=13;break;case 199:subtype=14;break;case 185:subtype=15;break;
            case 191:subtype=16;break;case 180:subtype=17;break;case 123:subtype=18;break;
            case 125:subtype=19;break;case 40:subtype=20;break;case 41:subtype=21;break;
            default:throw std::logic_error("unsupported basic recipe");
            }
            if(glyph==177 || glyph==200 || glyph==213 || glyph==211 || glyph==217 || glyph==161)cell[5]|=128;
            if(glyph==212 || glyph==210 || glyph==172 || glyph==140 || glyph==201 || glyph==190)cell[4]|=64;
            cell[0]=2;cell[1]=subtype;add(context.tuning[2]);break;
        }
        }
        adjustSubtype(cell);
    }
};
}
