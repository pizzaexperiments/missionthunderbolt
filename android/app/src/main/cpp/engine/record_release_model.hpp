#pragma once
#include <array>
#include <cstdint>
#include <functional>
#include <map>
#include <stdexcept>
#include <vector>

namespace mt {
// Isolated release control flow. Disposal is observed, not actual allocation
// ownership/freeing. The supplied observer must not mutate these records.
class RecordReleaseModel {
public:
    struct Node {uint32_t next26=0,branch30=0;};
    using Nodes=std::map<uint32_t,Node>;
    struct Parent {uint8_t count51=0;uint32_t field52=0;std::array<uint32_t,127> slots60{};};
    using Dispose=std::function<void(uint32_t)>;
    enum class Status {complete=0,budget_exhausted=1,missing_node=2};
    struct Result {Status status;uint32_t steps;};
    // CODE 11 wrapper: prefix lives at payload-2; the final memory-manager
    // operation is an observer callback, not a native free of a historical ptr.
    static void releasePrefix(uint32_t payload,uint16_t& prefix,const Dispose& memory_dispose) {
        if(!payload)return;
        prefix=static_cast<uint16_t>(prefix^0xffffu);
        if(prefix==0)memory_dispose(payload-2u);
    }
    static Result release16(Nodes& nodes,uint32_t root,uint32_t limit,const Dispose& dispose) {
        Budget budget{limit,0};return {walk(nodes,root,budget,dispose),budget.steps};
    }
    static Result release12(Nodes& nodes,Parent& parent,uint32_t identity,uint32_t limit,const Dispose& dispose) {
        // Original signed-byte indices outside this domain can read/write before
        // the slot array. Refuse that unsupported input without changing state.
        if(parent.count51>127)throw std::out_of_range("unsupported parent child count");
        Budget budget{limit,0};
        if(!budget.take())return {Status::budget_exhausted,budget.steps};
        while(parent.count51) {
            if(!budget.take())return {Status::budget_exhausted,budget.steps};
            --parent.count51;
            const auto status=walk(nodes,parent.slots60[parent.count51],budget,dispose);
            if(status!=Status::complete)return {status,budget.steps};
            parent.slots60[parent.count51]=0;
        }
        if(parent.field52)dispose(parent.field52);
        dispose(identity);return {Status::complete,budget.steps};
    }
private:
    struct Budget {
        uint32_t limit,steps;
        bool take() {if(steps==limit)return false;++steps;return true;}
    };
    struct Frame {uint32_t identity,cursor=0;unsigned phase=0;bool had_chain=false;};
    static Status walk(Nodes& nodes,uint32_t root,Budget& budget,const Dispose& dispose) {
        // Explicit frames retain the original order without using the host C++
        // call stack for a cyclic or deeply nested research input.
        std::vector<Frame> frames{{root}};
        while(!frames.empty()) {
            auto& frame=frames.back();
            if(frame.phase==0) {
                if(!budget.take())return Status::budget_exhausted;
                const auto node=nodes.find(frame.identity);
                if(node==nodes.end() || frame.identity==0)return Status::missing_node;
                frame.cursor=node->second.next26;frame.had_chain=frame.cursor!=0;frame.phase=1;
            } else if(frame.phase==2) {
                frame.cursor=nodes.at(frame.identity).branch30;frame.had_chain=frame.cursor!=0;frame.phase=3;
            } else if(frame.phase==1 || frame.phase==3) {
                if(frame.cursor) {
                    if(!budget.take())return Status::budget_exhausted;
                    const auto child=nodes.find(frame.cursor);
                    if(child==nodes.end())return Status::missing_node;
                    const auto identity=frame.cursor;
                    frame.cursor=child->second.next26;child->second.next26=0;
                    if(child->second.branch30)frames.push_back({identity});
                    else dispose(identity);
                } else {
                    if(frame.had_chain) {
                        auto& node=nodes.at(frame.identity);
                        if(frame.phase==1)node.next26=0;else node.branch30=0;
                    }
                    frame.phase=frame.phase==1?2:4;
                }
            } else {
                dispose(frame.identity);frames.pop_back();
            }
        }
        return Status::complete;
    }
};
}
