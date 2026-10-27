#include "api.h"
#include "game.hpp"
#include <cassert>
#include <climits>
#include <iostream>
#include <locale>
#include <random>
#include <string>
#include <vector>
struct GroupedNumbers : std::numpunct<char> {
    char do_thousands_sep() const override { return '_'; }
    std::string do_grouping() const override { return "\3"; }
};
int main() {
    mt::PrototypeGame game(20,12,42);
    const auto baseline=game.save();
    const auto previous=std::locale();
    std::locale::global(std::locale(previous,new GroupedNumbers));
    assert(game.save()==baseline);
    assert(mt::PrototypeGame::load(baseline).save()==baseline);
    std::locale::global(previous);
    std::mt19937 rng(1701);
    for(int i=0;i<2000;++i) {
        auto input=baseline;
        const size_t where=static_cast<size_t>(rng())%input.size();
        input[where]^=static_cast<char>(1u<<(rng()%7));
        try { auto parsed=mt::PrototypeGame::load(input); assert(parsed.width()>=5); }
        catch(const std::invalid_argument&) { }
    }
    for(int dimension : {INT_MIN,-1,0,4,513,INT_MAX}) {
        assert(mt_game_create(dimension,12,1)==nullptr);
        assert(mt_game_last_error()==MT_ERROR_INVALID_ARGUMENT);
    }
    mt_game* handle=mt_game_create(20,12,1);assert(handle);
    const int turns=mt_game_turns(handle);
    for(int delta : {INT_MIN,-100,2,100,INT_MAX}) assert(!mt_game_move(handle,delta,0));
    assert(mt_game_turns(handle)==turns);
    assert(mt_game_map(handle,nullptr,-1)==0);
    assert(!mt_game_load(handle,nullptr,INT_MAX));
    mt_game_destroy(handle);
    std::cout<<"2000 seeded save mutations, numeric limits and locale regression passed\n";
}
