#pragma once
#include "grid_candidate_selector.hpp"
#include <vector>

namespace mt {
// Bounded model of observed CODE 1 startup blocks, not a Macintosh loader.
class A5InitializationModel {
public:
    struct Expanded {std::vector<uint8_t> bytes;size_t data_used=0,zero_used=0;};
    static Expanded expand(const std::vector<uint8_t>& data,const std::vector<uint8_t>& zero,size_t size) {
        if(size>16*1024*1024 || size%2)throw std::invalid_argument("unsupported A5 window size");
        Expanded result;result.bytes.reserve(size);
        while(result.bytes.size()<size) {
            const auto value=word(data,result.data_used);result.data_used+=2;
            result.bytes.push_back(static_cast<uint8_t>(value>>8));result.bytes.push_back(static_cast<uint8_t>(value));
            if(value==0) {
                const auto count=word(zero,result.zero_used);result.zero_used+=2;
                if(count%2 || count>size-result.bytes.size())throw std::invalid_argument("unsupported or oversized zero run");
                result.bytes.insert(result.bytes.end(),count,0);
            }
        }
        return result;
    }
    static void relocate(std::vector<uint8_t>& image,size_t a5_index,const std::vector<uint8_t>& entries,
                         uint32_t a5,uint32_t alternate) {
        if(a5_index>image.size() || entries.size()%2 || entries.size()>32766)throw std::invalid_argument("unsupported relocation input");
        for(size_t at=0;at<entries.size();at+=2) {
            const auto raw=word(entries,at);const uint16_t bits=raw&0xfffe;
            const int offset=bits<32768?bits:static_cast<int>(bits)-65536;
            const int64_t index=static_cast<int64_t>(a5_index)+offset;
            if(index<0 || uint64_t(index)+4>image.size())throw std::out_of_range("relocation outside supplied image");
            const auto pos=static_cast<size_t>(index);
            uint32_t value=(uint32_t(image[pos])<<24)|(uint32_t(image[pos+1])<<16)|(uint32_t(image[pos+2])<<8)|image[pos+3];
            value+=raw&1?alternate:a5;
            for(unsigned i=0;i<4;++i)image[pos+i]=static_cast<uint8_t>(value>>(24-8*i));
        }
    }
    static GridCandidateSelector::Directions directions(const std::vector<uint8_t>& image,size_t a5_index) {
        if(a5_index>image.size() || a5_index<2534 || a5_index-2522+9>image.size())throw std::out_of_range("direction tables outside image");
        GridCandidateSelector::Directions result;
        auto signedByte=[](uint8_t value){return value<128?int(value):int(value)-256;};
        for(unsigned i=0;i<8;++i)result[i]={signedByte(image.at(a5_index-2534+i+1)),signedByte(image.at(a5_index-2522+i+1))};
        return result;
    }
private:
    static uint16_t word(const std::vector<uint8_t>& bytes,size_t at) {
        if(at>bytes.size() || bytes.size()-at<2)throw std::out_of_range("truncated startup resource");
        return static_cast<uint16_t>((bytes[at]<<8)|bytes[at+1]);
    }
};
}
