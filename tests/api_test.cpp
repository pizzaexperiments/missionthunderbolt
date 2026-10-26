#include "../android/app/src/main/cpp/api.h"
#include <cassert>
#include <vector>
#include <string>
#include <iostream>
int main() {
    assert(mt_api_version()==1);
    assert(mt_game_create(1,1,0)==nullptr);
    assert(mt_game_turns(nullptr)==-1);
    mt_game* g=mt_game_create(20,12,1);
    assert(g);
    const int size=mt_game_map(g,nullptr,0);
    assert(size>0);
    std::vector<char> buf(static_cast<size_t>(size));
    assert(mt_game_map(g,buf.data(),size)==size);
    assert(std::string(buf.data()).find('@')!=std::string::npos);
    assert(mt_game_move(g,-1,0)==0);
    assert(mt_game_turns(g)==0);
    assert(mt_game_move(g,1,0)==1);
    assert(mt_game_turns(g)==1);
    mt_game_set_modern(g,1);
    assert(mt_game_is_modern(g)==1);
    mt_game_destroy(g);
    std::cout<<"C API tests passed\n";
}
