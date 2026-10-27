#pragma once
#include "grid_fallback_selector.hpp"
#include <map>

namespace mt {
// Isolated research helpers, not active inventory/entity/gameplay rules.
class LinkedRecordModel {
public:
    static bool query16(uint16_t word0,uint32_t field30) {
        return word0==0 || word0==29 || word0==30 || (word0>=56 && word0<=58) ||
               (word0>=65 && word0<=69) || (word0==70 && field30!=0) || word0==81 ||
               (word0>=107 && word0<=109) || word0==119 || word0==141 || word0==175;
    }
    struct Header {uint16_t count18;uint32_t head20;};
    struct Node {uint8_t row48,column49;uint32_t next56;};
    using Nodes=std::map<uint32_t,Node>;
    enum class Status {unlinked=0,budget_exhausted=1,missing_node=2};
    struct Result {Status status;uint32_t visits;};
    static Result unlink12(Header& header,GridFallbackSelector::Grid& grid,Nodes& nodes,
                           uint32_t target,uint32_t traversal_budget) {
        auto found=nodes.find(target);
        if(target==0 || found==nodes.end())throw std::invalid_argument("missing target record");
        auto& record=found->second;
        // The original sign-extends these coordinates and performs an unchecked
        // memory write. This model's explicit precondition is a valid grid cell.
        if(record.row48>=19 || record.column49>=67)throw std::out_of_range("linked record coordinates");
        header.count18=static_cast<uint16_t>(header.count18-1);
        grid[record.row48*67+record.column49].setLong(12,0);
        if(header.head20==target) {
            header.head20=record.next56;record.next56=0;return {Status::unlinked,0};
        }
        auto cursor=header.head20;
        for(uint32_t visit=0;visit<traversal_budget;++visit) {
            auto current=nodes.find(cursor);
            if(current==nodes.end())return {Status::missing_node,visit};
            if(current->second.next56==target) {
                current->second.next56=record.next56;record.next56=0;
                return {Status::unlinked,visit+1};
            }
            cursor=current->second.next56;
        }
        // Original traversal is unbounded. Preserve the already-decremented
        // count and cleared grid link when stopping research on cyclic lists.
        return {Status::budget_exhausted,traversal_budget};
    }
};
}
