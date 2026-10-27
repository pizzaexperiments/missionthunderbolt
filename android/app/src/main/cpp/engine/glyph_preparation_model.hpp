#pragma once
#include "shuffled_lcg_model.hpp"
#include <vector>

namespace mt {
// Bounded map-byte preparation from CODE 12 offsets 4866..5238. Glyphs are
// literal bytes; terrain/item meanings and the full generator remain unknown.
class GlyphPreparationModel {
public:
    using Map=std::array<uint8_t,19*67>;
    struct Result {
        std::array<uint32_t,3> attempts{};
        std::vector<std::array<uint32_t,3>> draws; // bound, one-based, result
        std::vector<std::array<uint32_t,5>> writes; // pass, row, column, before, after
    };
    static Result prepare(Map& map,uint8_t flags6,int level,uint8_t metadata2,ShuffledLcgModel& rng) {
        if(level < -32768 || level > 32767)throw std::invalid_argument("level must fit signed word");
        Result result;
        auto draw=[&](unsigned bound,bool one=false) {
            const auto value=one?rng.oneBased(static_cast<int>(bound)):rng.zeroBased(static_cast<int>(bound));
            result.draws.push_back({bound,one?1u:0u,value});return value;
        };
        auto paint=[&](unsigned pass,unsigned row,unsigned column,uint8_t value) {
            auto& cell=map[row*67+column];result.writes.push_back({pass,row,column,cell,value});cell=value;
        };
        if(!(flags6&4))for(unsigned n=0;n<32;++n) {
            ++result.attempts[0];const auto row=draw(19),column=draw(67);
            if(map[row*67+column]==0x20)paint(0,row,column,draw(32)?0x2e:0x3b);
        }
        if(level==46 || level==69)return result;
        const unsigned count=(flags6&4) && metadata2<128?16:32;
        for(unsigned n=0;n<count;++n) {
            ++result.attempts[1];const auto row=draw(19),column=draw(67);
            if(map[row*67+column]==0x20)paint(1,row,column,0x2d);
        }
        // The original draws a NEW 1..3 bound at every condition, including
        // the final failed condition. Drawing one count in advance is different.
        for(unsigned n=1;n<=draw(3,true);++n) {
            ++result.attempts[2];const auto row=draw(19),column=draw(67);
            if(map[row*67+column]==0x20)paint(2,row,column,0x24);
        }
        return result;
    }
};
}
