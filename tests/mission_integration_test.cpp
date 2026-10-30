#include "game.hpp"
#include "api.h"
#include <cassert>
#include <iomanip>
#include <limits>
#include <sstream>
#include <vector>

static std::string checked(const std::string& body) {
    uint32_t crc=0xffffffffu;
    for(unsigned char ch:body) {
        crc^=ch;
        for(int bit=0;bit<8;++bit)crc=(crc>>1)^(0xedb88320u&(0u-(crc&1u)));
    }
    std::ostringstream out;
    out<<body<<"CRC32 "<<std::hex<<std::setw(8)<<std::setfill('0')<<~crc<<'\n';
    return out.str();
}
static std::string withHeader(const std::string& save,const std::string& header) {
    const auto first=save.find('\n'),second=save.find('\n',first+1),trailer=save.rfind("CRC32 ");
    return checked(save.substr(0,first+1)+header+'\n'+save.substr(second+1,trailer-second-1));
}
static void rejects(const std::string& saved) {
    bool rejected=false;
    try {(void)mt::PrototypeGame::load(saved);}catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected);
}
int main() {
    // Frozen RM1 recipe fingerprints catch layout/RNG changes that would
    // otherwise silently reinterpret a seed-based save. New recipes need migration.
    const uint32_t recipe_seeds[]{0u,1u,2u,42u,0xffffffffu};
    const uint64_t map_hashes[]{0x7630978b7a525f73ull,0x7630978b7a525f73ull,
        0x1f1202468ab68aa1ull,0xfd89b35c338762e3ull,0x933113c6c02d0aabull};
    const char* trailers[]{"CRC32 f179fc6b\n","CRC32 2bff7ac1\n","CRC32 1e101b1e\n",
        "CRC32 d02755d5\n","CRC32 9ebc4c8e\n"};
    for(unsigned i=0;i<5;++i) {
        const auto recipe=mt::PrototypeGame::researchMission(recipe_seeds[i]);
        uint64_t hash=14695981039346656037ull;
        for(unsigned char c:recipe.asciiMap()) {hash^=c;hash*=1099511628211ull;}
        const auto saved=recipe.save();
        assert(hash==map_hashes[i] && saved.substr(saved.rfind("CRC32 "))==trailers[i]);
    }
    for(uint32_t seed:{0u,1u,42u,0xffffffffu}) {
        auto game=mt::PrototypeGame::researchMission(seed);
        assert(game.isResearchMission() && game.width()==67 && game.height()==19);
        assert(game.player().x==1 && game.player().y==1 && game.inventoryCount()==0);
        const auto original=game.save();
        assert(original.find("MTDEMO 2\n")==0);
        assert(game.asciiMap().find('!')!=std::string::npos);
        assert(!game.pickup() && game.save()==original);
        assert(!game.move(-1,0) && game.save()==original);
        assert(game.move(1,0) && game.move(1,0));
        auto on_item=mt::PrototypeGame::load(game.save());
        assert(on_item.save()==game.save() && on_item.pickup());
        assert(game.pickup() && game.turns()==3 && game.inventoryCount()==1);
        assert(game.asciiMap().find('!')==std::string::npos);
        auto collected=game.save();
        assert(!game.pickup() && game.save()==collected);
        game.setPresentation(mt::Presentation::Modern);
        auto restored=mt::PrototypeGame::load(game.save());
        assert(restored.isResearchMission() && restored.save()==game.save());
        assert(restored.inventoryCount()==1 && restored.presentation()==mt::Presentation::Modern);
        for(int i=0;i<12;++i) {
            assert(restored.move(1,0)==game.move(1,0));
            assert(restored.wait()==game.wait());
            assert(restored.save()==game.save());
        }
    }
    auto game=mt::PrototypeGame::researchMission(1);
    const auto before=game.save();
    auto corrupt=before;corrupt[corrupt.size()/2]^=1;rejects(corrupt);
    rejects(withHeader(before,"1 0 0 0 0")); // A CRC-valid player in a wall.
    rejects(withHeader(before,"2 0 1 1 0")); // Header and world seeds disagree.
    rejects(withHeader(before,"1 -1 1 1 0"));
    rejects(withHeader(before,"1 0 1 1 2"));
    auto saturated=mt::PrototypeGame::load(withHeader(before,"1 2147483647 3 1 0"));
    const auto full=saturated.save();
    assert(!saturated.pickup() && !saturated.move(1,0) && !saturated.wait());
    assert(saturated.save()==full && saturated.inventoryCount()==0);
    assert(mt::PrototypeGame::researchMission(1).asciiMap()!=mt::PrototypeGame::researchMission(2).asciiMap());
    assert(mt_game_inventory_count(nullptr)==-1 && mt_game_last_error()==MT_ERROR_INVALID_ARGUMENT);
    mt_game* api=mt_game_create_research(1);assert(api && mt_game_is_research(api));
    assert(!mt_game_pickup(api) && mt_game_last_error()==MT_ERROR_NONE);
    assert(mt_game_move(api,1,0) && mt_game_move(api,1,0) && mt_game_pickup(api));
    assert(mt_game_inventory_count(api)==1 && mt_game_turns(api)==3);
    std::vector<char> saved(static_cast<size_t>(mt_game_save(api,nullptr,0)));
    assert(mt_game_save(api,saved.data(),static_cast<int>(saved.size()))==static_cast<int>(saved.size()));
    assert(!mt_game_load(api,"bad",3) && mt_game_inventory_count(api)==1 && mt_game_turns(api)==3);
    mt_game* legacy=mt_game_create(20,12,1);assert(legacy && !mt_game_is_research(legacy));
    assert(mt_game_load(legacy,saved.data(),static_cast<int>(saved.size()-1)));
    assert(mt_game_is_research(legacy) && mt_game_inventory_count(legacy)==1);
    const auto legacy_save=mt::PrototypeGame(20,12,42).save();
    assert(mt_game_load(api,legacy_save.data(),static_cast<int>(legacy_save.size())) && !mt_game_is_research(api));
    assert(!mt_game_pickup(api) && mt_game_inventory_count(api)==0);
    mt_game_destroy(api);mt_game_destroy(legacy);
}
