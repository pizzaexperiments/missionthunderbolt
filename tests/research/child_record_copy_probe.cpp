#include "engine/child_record_copy_model.hpp"
#include <iomanip>
#include <iostream>
#include <string>
#include <stdexcept>
using Model=mt::ChildRecordCopyModel;
static unsigned nibble(char value) {
    if(value>='0' && value<='9')return static_cast<unsigned>(value-'0');
    if(value>='a' && value<='f')return static_cast<unsigned>(value-'a'+10);
    throw std::invalid_argument("invalid hex");
}
static void decode(const std::string& hex,Model::Record& record) {
    if(hex.size()!=112)throw std::invalid_argument("wrong record size");
    for(unsigned i=0;i<56;++i)record[i]=static_cast<uint8_t>((nibble(hex[2*i])<<4)|nibble(hex[2*i+1]));
}
static void print(const Model::Record& record) {
    for(auto byte:record)std::cout<<std::setw(2)<<unsigned(byte);
}
int main() {
    unsigned alias;std::string source_hex,initial_hex;
    std::cout<<std::hex<<std::setfill('0');
    while(std::cin>>alias>>source_hex>>initial_hex) {
        if(alias>1)return 2;
        Model::Record source{},destination{};decode(source_hex,source);decode(initial_hex,destination);
        auto& output=alias?source:destination;Model::copy(output,source);
        print(source);std::cout<<' ';print(output);std::cout<<'\n';
    }
    return std::cin.eof()?0:2;
}
