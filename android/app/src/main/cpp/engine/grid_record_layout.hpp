#pragma once
#include <cstdint>
#include <stdexcept>

namespace mt {
// Research-only address layout corroborated with CODE 12 entry 19476.
// Record fields, terrain semantics and generation are intentionally unspecified.
struct GridRecordLayout {
    static constexpr int columns=67, rows=19;
    static constexpr uint32_t header_bytes=104, record_bytes=20;
    static constexpr uint32_t row_bytes=columns*record_bytes;
    static constexpr uint32_t end_offset=header_bytes+rows*row_bytes;
    static uint32_t offset(int column,int row) {
        if(column<0 || column>=columns || row<0 || row>=rows)
            throw std::out_of_range("grid record coordinate outside research layout");
        return header_bytes+static_cast<uint32_t>(row)*row_bytes+static_cast<uint32_t>(column)*record_bytes;
    }
    struct Coordinate {int column,row;};
    static Coordinate clampSignedBytes(int column,int row) {
        if(column < -128 || column > 127 || row < -128 || row > 127)
            throw std::out_of_range("coordinate must fit signed byte input");
        return {column<0 ? 0 : (column>=columns ? columns-1 : column),
                row<0 ? 0 : (row>=rows ? rows-1 : row)};
    }
    // Gate from CODE 13 entry 12328, not a general movement/collision predicate.
    static bool selectionCandidate(uint8_t kind,uint32_t field16) {
        if(field16)return false;
        switch(kind) {
            case 1:case 2:case 22:case 25:case 28:case 29:case 30:case 34:return false;
            default:return true;
        }
    }
    // Analytical 32-bit address bits, not a pointer to dereference in a native host.
    static uint32_t address32(uint32_t base,int column,int row) {return base+offset(column,row);}
};
}
