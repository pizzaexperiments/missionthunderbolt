#pragma once
#include "level_grid_conversion_model.hpp"
#include "supplied_record_placement_model.hpp"
#include <sstream>
#include <locale>
#include <string>
#include <vector>

namespace mt {
// Playable authored scenario using recovered routines with synthetic inputs.
// Rooms, collision and collection policy are new; historical gameplay is absent.
class ResearchMission {
public:
    static constexpr int Width=67,Height=19;
    static constexpr uint32_t ItemHandle=0x1000;
    using Cells=LevelGridConversionModel::Records;
    using Item=SuppliedRecordPlacementModel::Factory::Record;
    explicit ResearchMission(uint32_t seed=1)
        :seed_(seed),rng_(ShuffledLcgModel::initialized(seed,1)) {
        glyphs_.fill(35);
        room(1,1,8,5);
        int previous_x=4,previous_y=3;
        for(unsigned index=0;index<9;++index) {
            const int width=5+static_cast<int>(rng_.zeroBased(8));
            const int height=3+static_cast<int>(rng_.zeroBased(4));
            const int left=1+static_cast<int>(rng_.zeroBased(66-width));
            const int top=1+static_cast<int>(rng_.zeroBased(18-height));
            room(left,top,width,height);
            const int x=left+width/2,y=top+height/2;
            if(rng_.zeroBased(2)==0) {horizontal(previous_x,x,previous_y);vertical(previous_y,y,x);}
            else {vertical(previous_y,y,previous_x);horizontal(previous_x,x,y);}
            previous_x=x;previous_y=y;
        }
        // The two markers are authored destinations, never level transitions.
        glyphs_[3*Width+6]=94;
        if(previous_x==6 && previous_y==3)previous_x=7;
        glyphs_[previous_y*Width+previous_x]=118;
        LevelGridConversionModel::Context context{{16,0,1,{7,11,13}},17,19,23};
        LevelGridConversionModel::convert(glyphs_,cells_,context,rng_);
        for(unsigned i=0;i<cells_.size();++i)grid_[i].bytes=cells_[i];
        using Factory=SuppliedRecordPlacementModel::Factory;
        Factory::Templates templates{};Factory::DescriptorFlags descriptors{};
        Factory::Thresholds thresholds{};Factory::Children children{};
        // An authored raw type-0 record; no item table or assets are imported.
        templates[0][2]=1;templates[0][15]=7;
        nodes_.emplace(ItemHandle,LinkedRecordModel::Node{0,0,0});
        SuppliedRecordPlacementModel::place(item_,header_,grid_,nodes_,ItemHandle,1,3,
            templates,descriptors,{0,1,0,0},rng_,children,thresholds);
        syncCells();
    }
    bool walkable(int x,int y) const {
        // Authored collision: converted raw kind 0 is floor; kind 2 is wall.
        return x>=0 && x<Width && y>=0 && y<Height && grid_[y*Width+x].bytes[0]==0;
    }
    std::vector<std::string> asciiRows() const {
        std::vector<std::string> rows(Height,std::string(Width,'#'));
        for(int y=0;y<Height;++y)for(int x=0;x<Width;++x) {
            const unsigned i=static_cast<unsigned>(y*Width+x);
            if(walkable(x,y))rows[y][x]=glyphs_[i]==94?'^':glyphs_[i]==118?'v':'.';
            if(!carried_ && grid_[i].longAt(12)==ItemHandle)rows[y][x]='!';
        }
        return rows;
    }
    bool pickup(int x,int y) {
        if(carried_ || x!=3 || y!=1 || !walkable(x,y) || grid_[y*Width+x].longAt(12)!=ItemHandle)return false;
        auto staged_grid=grid_;auto staged_nodes=nodes_;auto staged_header=header_;auto staged_item=item_;
        const auto result=LinkedRecordModel::unlink12(staged_header,staged_grid,staged_nodes,ItemHandle,1);
        if(result.status!=LinkedRecordModel::Status::unlinked)throw std::logic_error("research sample unlink failed");
        const auto next=staged_nodes.at(ItemHandle).next56;
        for(unsigned i=0;i<4;++i)staged_item[56+i]=static_cast<uint8_t>(next>>(24-8*i));
        grid_=staged_grid;nodes_=std::move(staged_nodes);header_=staged_header;item_=staged_item;carried_=true;
        syncCells();return true;
    }
    bool carried() const {return carried_;}
    uint32_t seed() const {return seed_;}
    const ShuffledLcgModel::State& rngState() const {return rng_.state();}
    const Cells& cells() const {return cells_;}
    const GridFallbackSelector::Grid& grid() const {return grid_;}
    const LinkedRecordModel::Header& header() const {return header_;}
    const LinkedRecordModel::Nodes& nodes() const {return nodes_;}
    const Item& item() const {return item_;}
    std::string serialize() const {
        std::ostringstream output;output.imbue(std::locale::classic());output<<"RM1 "<<seed_<<' '<<unsigned(carried_);
        const auto& state=rng_.state();
        output<<' '<<state.local_seed<<' '<<state.selector_seed<<' '<<state.last_result;
        for(auto value:state.table)output<<' '<<value;
        return output.str();
    }
    static ResearchMission restore(const std::string& data) {
        if(data.size()>4096)throw std::invalid_argument("research mission save too large");
        std::istringstream input(data);input.imbue(std::locale::classic());std::string tag;
        if(!(input>>tag) || tag!="RM1")throw std::invalid_argument("unsupported research mission save");
        const auto seed=number(input);const auto carried=number(input);
        if(carried>1)throw std::invalid_argument("invalid carried state");
        ShuffledLcgModel::State saved;saved.local_seed=number(input);saved.selector_seed=number(input);saved.last_result=number(input);
        for(auto& value:saved.table)value=number(input);
        std::string extra;if(input>>extra)throw std::invalid_argument("trailing research mission save data");
        ResearchMission mission(seed);
        const auto& state=mission.rngState();
        if(state.local_seed!=saved.local_seed || state.selector_seed!=saved.selector_seed ||
           state.last_result!=saved.last_result || state.table!=saved.table)
            throw std::invalid_argument("research mission RNG does not match scenario");
        if(carried && !mission.pickup(3,1))throw std::invalid_argument("invalid restored sample state");
        return mission;
    }
private:
    uint32_t seed_;
    ShuffledLcgModel rng_;
    LevelGridConversionModel::Glyphs glyphs_{};
    Cells cells_{};
    GridFallbackSelector::Grid grid_{};
    LinkedRecordModel::Nodes nodes_{};
    LinkedRecordModel::Header header_{0,0};
    Item item_{};
    bool carried_=false;
    void room(int left,int top,int width,int height) {
        for(int y=top;y<top+height;++y)for(int x=left;x<left+width;++x)glyphs_[y*Width+x]=32;
    }
    void horizontal(int from,int to,int y) {
        const int step=from<=to?1:-1;
        for(int x=from;;x+=step) {glyphs_[y*Width+x]=32;if(x==to)break;}
    }
    void vertical(int from,int to,int x) {
        const int step=from<=to?1:-1;
        for(int y=from;;y+=step) {glyphs_[y*Width+x]=32;if(y==to)break;}
    }
    void syncCells() {for(unsigned i=0;i<cells_.size();++i)cells_[i]=grid_[i].bytes;}
    static uint32_t number(std::istream& input) {
        std::string token;if(!(input>>token) || token.empty() || token.size()>10)throw std::invalid_argument("missing research mission value");
        uint64_t value=0;
        for(char c:token) {
            if(c<'0' || c>'9')throw std::invalid_argument("invalid research mission number");
            value=value*10u+static_cast<unsigned>(c-'0');
            if(value>0xffffffffULL)throw std::invalid_argument("research mission value overflow");
        }
        return static_cast<uint32_t>(value);
    }
};
}
