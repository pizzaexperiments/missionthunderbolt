#pragma once
#include "direct_grid_conversion_model.hpp"
#include "level_cell_conversion_model.hpp"
#include <vector>

namespace mt {
class LevelGridConversionModel {
public:
    using Glyphs=DirectGridConversionModel::Glyphs;
    using Records=DirectGridConversionModel::Records;
    using Context=LevelCellConversionModel::Context;
    using Draw=std::array<uint32_t,5>; // row, column, bound, one-based, result
    static std::vector<Draw> convert(const Glyphs& glyphs,Records& records,const Context& context,ShuffledLcgModel& rng) {
        const auto& c=context.direct;
        if(c.level < -32768 || c.level > 32767)throw std::invalid_argument("level must fit word");
        for(auto glyph:glyphs)if(!BasicCellConversionModel::supported(glyph) && !LevelCellConversionModel::supported(glyph))
            throw std::invalid_argument("grid contains unmodeled conversion/service");
        // Reserve before mutation so allocation failure cannot consume RNG or change records.
        std::vector<Draw> draws;draws.reserve(DirectGridConversionModel::count);
        const auto seed=DirectGridConversionModel::baseWord(c.level==32767?-32768:c.level+1);
        for(unsigned i=0;i<DirectGridConversionModel::count;++i) {
            auto& cell=records[i];cell[2]=static_cast<uint8_t>(seed>>8);cell[3]=static_cast<uint8_t>(seed);
            if(BasicCellConversionModel::supported(glyphs[i]))BasicCellConversionModel::convert(glyphs[i],cell,c);
            else if(const auto value=LevelCellConversionModel::convert(glyphs[i],cell,context,rng))
                draws.push_back({i/67,i%67,3,1,*value});
        }
        return draws;
    }
};
}
