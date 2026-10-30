#pragma once
#include "record_template_factory_model.hpp"
#include "record_followup_model.hpp"

namespace mt {
// Supplied-allocation factory through the actual follow-up model. Allocator,
// child creation and unsupported variant paths remain outside this composition.
class FinalizedTemplateFactoryModel {
public:
    using Record=RecordTemplateFactoryModel::Record;
    using Templates=RecordTemplateFactoryModel::Templates;
    using DescriptorFlags=RecordTemplateFactoryModel::DescriptorFlags;
    using Context=RecordTemplateFactoryModel::Context;
    using Children=RecordFollowupModel::Children;
    using Thresholds=std::array<int16_t,256>;
    static RecordTemplateFactoryModel::Result prepare(Record& output,const Templates& templates,
        const DescriptorFlags& descriptors,const Context& c,ShuffledLcgModel& rng,
        const Children& children,const Thresholds& thresholds) {
        // Stage RNG and destination so callback input errors also reject atomically.
        auto staged_rng=rng;Record candidate=output;
        auto result=RecordTemplateFactoryModel::prepare(candidate,templates,descriptors,c,staged_rng);
        if(result.requires_followup) {
            RecordFollowupModel::Context followup;followup.thresholds=thresholds;
            for(unsigned i=0;i<76;++i)followup.template_flags[i]=templates[i][20];
            RecordFollowupModel::apply(candidate,children,followup);
        }
        output=candidate;rng=std::move(staged_rng);return result;
    }
};
}
