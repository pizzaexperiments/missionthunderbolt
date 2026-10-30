#pragma once
#include "finalized_template_factory_model.hpp"
#include "linked_record_model.hpp"

namespace mt {
class SuppliedRecordPlacementModel {
public:
    using Factory=FinalizedTemplateFactoryModel;
    static RecordTemplateFactoryModel::Result place(Factory::Record& record,LinkedRecordModel::Header& header,
        GridFallbackSelector::Grid& grid,LinkedRecordModel::Nodes& nodes,uint32_t target,int row,int column,
        const Factory::Templates& templates,const Factory::DescriptorFlags& descriptors,const Factory::Context& c,
        ShuffledLcgModel& rng,const Factory::Children& children,const Factory::Thresholds& thresholds) {
        const auto found=nodes.find(target);
        if(target==0 || found==nodes.end())throw std::invalid_argument("missing supplied destination handle");
        if(row<0 || row>=19 || column<0 || column>=67)throw std::out_of_range("placement coordinates");
        auto staged_rng=rng;auto candidate=record;auto staged_grid=grid;auto staged_header=header;
        auto result=Factory::prepare(candidate,templates,descriptors,c,staged_rng,children,thresholds);
        const uint32_t next=(uint32_t(candidate[56])<<24)|(uint32_t(candidate[57])<<16)|(uint32_t(candidate[58])<<8)|candidate[59];
        LinkedRecordModel::Nodes staged_nodes{{target,{candidate[48],candidate[49],next}}};
        LinkedRecordModel::attach12(staged_header,staged_grid,staged_nodes,target,row,column);
        const auto node=staged_nodes.at(target);candidate[48]=node.row48;candidate[49]=node.column49;
        for(unsigned i=0;i<4;++i)candidate[56+i]=static_cast<uint8_t>(node.next56>>(24-8*i));
        record=candidate;header=staged_header;grid=staged_grid;found->second=node;rng=std::move(staged_rng);
        return result;
    }
};
}
