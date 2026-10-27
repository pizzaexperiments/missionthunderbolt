#pragma once
#include "grid_record_layout.hpp"
#include "shuffled_lcg_model.hpp"
#include <array>
#include <vector>

namespace mt {
// Research model of CODE 13 entry 15742. Linked-record callbacks are explicit;
// their original implementations/ownership semantics are not reconstructed here.
class GridFallbackSelector {
public:
    struct Record {
        std::array<uint8_t,20> bytes{};
        uint32_t longAt(unsigned offset) const {
            if(offset>16)throw std::out_of_range("record long offset");
            return (uint32_t(bytes[offset])<<24)|(uint32_t(bytes[offset+1])<<16)|
                   (uint32_t(bytes[offset+2])<<8)|bytes[offset+3];
        }
        void setLong(unsigned offset,uint32_t value) {
            if(offset>16)throw std::out_of_range("record long offset");
            for(unsigned n=0;n<4;++n)bytes[offset+n]=static_cast<uint8_t>(value>>(24-8*n));
        }
    };
    using Grid=std::array<Record,GridRecordLayout::columns*GridRecordLayout::rows>;
    struct Link16 {uint16_t word0;uint8_t byte25;};
    struct Link12 {uint16_t word0;uint8_t byte51;std::vector<uint32_t> slots60;};
    class Services {
    public:
        virtual ~Services()=default;
        virtual Link16 read16(uint32_t reference)=0;
        virtual Link12 read12(uint32_t reference)=0;
        virtual uint16_t query16(uint32_t reference)=0;
        virtual void release16(uint32_t reference)=0;
        virtual void unlink12(uint32_t grid_identity,uint32_t reference)=0;
        virtual void release12(uint32_t reference)=0;
    };
    enum class Phase {first_scan=0,second_scan=1,random=2,budget_exhausted=3};
    struct Result {GridRecordLayout::Coordinate coordinate;Phase phase;uint32_t random_attempts;};
    static Result select(Grid& grid,ShuffledLcgModel& rng,Services& services,
                         uint32_t grid_identity,uint32_t random_budget) {
        for(int row=1;row<18;++row)for(int column=1;column<66;++column) {
            auto& cell=grid[row*67+column];
            if(scanEligible(cell) && cell.longAt(16)==0)return {{column,row},Phase::first_scan,0};
        }
        for(int row=1;row<18;++row)for(int column=1;column<66;++column) {
            auto& cell=grid[row*67+column];if(!scanEligible(cell))continue;
            const auto link=cell.longAt(16);
            if(link) {
                if(!services.query16(link))continue;
                services.release16(cell.longAt(16));cell.setLong(16,0);
            }
            return {{column,row},Phase::second_scan,0};
        }
        GridRecordLayout::Coordinate last{-1,-1};
        for(uint32_t attempt=0;attempt<random_budget;++attempt) {
            const int row=static_cast<int>(rng.oneBased(17)),column=static_cast<int>(rng.oneBased(65));
            last={column,row};auto& cell=grid[row*67+column];
            if(cell.bytes[0]==28 || cell.bytes[0]==29 || cell.bytes[1]==51)continue;
            auto link=cell.longAt(16);
            if(link) {
                if(protected16(services.read16(link)))continue;
                services.release16(link);cell.setLong(16,0);
            }
            link=cell.longAt(12);
            if(link) {
                const auto record=services.read12(link);if(record.word0==73)continue;
                const unsigned count=record.byte51<128 ? record.byte51 : 0;
                if(count>record.slots60.size())throw std::out_of_range("linked record slots missing");
                bool blocked=false;
                for(unsigned n=0;n<count;++n)
                    if(protected16(services.read16(record.slots60[n]))) {blocked=true;break;}
                if(blocked)continue;
                services.unlink12(grid_identity,link);services.release12(link);
            }
            const auto kind=cell.bytes[0];
            if((kind==2 || kind==22) && ((cell.bytes[4]&64) || (cell.bytes[5]&128)))continue;
            if(kind==1 || kind==2 || kind==22 || kind==25) {
                cell.bytes[0]=0;cell.bytes[2]=3;cell.bytes[3]=232; // big-endian 1000
            }
            cell.bytes[8]=0;cell.bytes[4]&=254;cell.bytes[5]&=18;cell.bytes[6]&=240;
            if(cell.bytes[4]&4) {cell.bytes[9]=0;cell.bytes[4]&=251;}
            cell.bytes[10]=0;cell.bytes[11]=0;
            return {last,Phase::random,attempt+1};
        }
        // Original retry loop is unbounded. This caller-supplied research limit
        // returns partial state and does not manufacture an accepted coordinate.
        return {last,Phase::budget_exhausted,random_budget};
    }
private:
    static bool scanEligible(const Record& cell) {
        return cell.longAt(12)==0 && cell.bytes[0]==0 && cell.bytes[8]==0 &&
               !(cell.bytes[4]&4) && cell.bytes[1]!=51;
    }
    static bool protected16(Link16 record) {return (record.byte25&1) || record.word0==52;}
};
}
