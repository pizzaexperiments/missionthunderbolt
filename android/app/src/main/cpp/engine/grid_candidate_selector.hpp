#pragma once
#include "grid_record_layout.hpp"
#include "shuffled_lcg_model.hpp"
#include <array>

namespace mt {
// Research model of CODE 13 entry 12328 up to its fallback call.
// Direction-table contents are explicit inputs, not recovered original defaults.
class GridCandidateSelector {
public:
    struct Cell {uint8_t kind=0;uint32_t field16=0;};
    struct Direction {int row,column;};
    using Grid=std::array<Cell,GridRecordLayout::rows*GridRecordLayout::columns>;
    using Directions=std::array<Direction,8>;
    enum class Outcome {direct=0,neighbor=1,needs_fallback=2};
    struct Result {GridRecordLayout::Coordinate coordinate;Outcome outcome;int iterations;};
    static Result select(const Grid& grid,const Directions& directions,ShuffledLcgModel& rng) {
        for(const auto& d:directions)
            if(d.row < -128 || d.row > 127 || d.column < -128 || d.column > 127)
                throw std::out_of_range("direction must fit signed byte input");
        int row=static_cast<int>(rng.oneBased(17));
        int column=static_cast<int>(rng.oneBased(65));
        for(int attempt=1;attempt<=200;++attempt) {
            if(candidate(grid,column,row))return {{column,row},Outcome::direct,attempt};
            const auto first=rng.oneBased(8)-1;
            for(unsigned n=0;n<8;++n) {
                const auto& d=directions[(first+n)%8];
                auto nearby=GridRecordLayout::clampSignedBytes(signedByte(column+d.column),signedByte(row+d.row));
                if(candidate(grid,nearby.column,nearby.row))return {nearby,Outcome::neighbor,attempt};
            }
            row+=static_cast<int>(rng.zeroBased(3))-1;
            column+=static_cast<int>(rng.zeroBased(3))-1;
            auto clipped=GridRecordLayout::clampSignedBytes(column,row);column=clipped.column;row=clipped.row;
        }
        // The original calls its multi-pass fallback here; no fallback behavior is guessed.
        return {{column,row},Outcome::needs_fallback,200};
    }
private:
    static int signedByte(int value) {const auto bits=static_cast<uint8_t>(value);return bits<128 ? bits : static_cast<int>(bits)-256;}
    static bool candidate(const Grid& grid,int column,int row) {
        const auto& cell=grid[static_cast<unsigned>(row*GridRecordLayout::columns+column)];
        return GridRecordLayout::selectionCandidate(cell.kind,cell.field16);
    }
};
}
