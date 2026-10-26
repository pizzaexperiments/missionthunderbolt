#include "game.hpp"
#include <limits>
#include <locale>
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <vector>
namespace mt {
PrototypeGame::PrototypeGame(int w, int h, uint32_t seed) : map_(w, h, seed), seed_(seed) {}
bool PrototypeGame::move(int dx, int dy) {
    if (dx < -1 || dx > 1 || dy < -1 || dy > 1 || (dx == 0 && dy == 0)) return false;
    if (turns_ == std::numeric_limits<int>::max()) return false;
    const int x = player_.x + dx, y = player_.y + dy;
    if (!map_.walkable(x, y)) return false;
    player_ = {x, y};
    ++turns_;
    return true;
}
std::string PrototypeGame::asciiMap() const {
    auto grid = map_.cells();
    grid[player_.y][player_.x] = '@';
    std::string out;
    out.reserve(static_cast<size_t>((width()+1)*height()));
    for (const auto& line : grid) { out += line; out += '\n'; }
    return out;
}
}

namespace mt {
namespace {
uint32_t crc32(const std::string& data) {
    uint32_t crc=0xffffffffu;
    for (unsigned char ch : data) {
        crc ^= ch;
        for (int i=0;i<8;++i) crc=(crc>>1) ^ (0xedb88320u & (0u-(crc&1u)));
    }
    return ~crc;
}
}
std::string PrototypeGame::save() const {
    std::ostringstream out; out.imbue(std::locale::classic());
    out << "MTDEMO 1\n" << width() << ' ' << height() << ' ' << seed_ << ' ' << rngState()
        << ' ' << turns_ << ' ' << player_.x << ' ' << player_.y << ' '
        << (presentation_==Presentation::Modern ? 1 : 0) << '\n';
    for (const auto& row : map_.cells()) out << row << '\n';
    const auto body=out.str();
    out << "CRC32 " << std::hex << std::setw(8) << std::setfill('0') << crc32(body) << '\n';
    return out.str();
}
PrototypeGame PrototypeGame::load(const std::string& data) {
    if (data.size()>1024*1024 || data.empty() || data.back()!='\n')
        throw std::invalid_argument("invalid save length");
    const auto trailer=data.rfind("CRC32 ");
    if (trailer==std::string::npos || trailer==0 || data[trailer-1]!='\n' || data.size()-trailer!=15)
        throw std::invalid_argument("invalid save checksum trailer");
    const auto digits=data.substr(trailer+6,8);
    if (!std::all_of(digits.begin(),digits.end(),[](char ch) { return (ch>='0' && ch<='9') || (ch>='a' && ch<='f'); }))
        throw std::invalid_argument("invalid checksum digits");
    std::istringstream checksum(digits); checksum.imbue(std::locale::classic());
    uint64_t expected=0;
    checksum >> std::hex >> expected;
    if (!checksum || expected>0xffffffffu || crc32(data.substr(0,trailer))!=expected)
        throw std::invalid_argument("save checksum mismatch");
    std::istringstream input(data.substr(0,trailer)); input.imbue(std::locale::classic());
    std::string magic; int version=0,w=0,h=0,turns=0,x=0,y=0,modern=0;
    uint64_t seed=0,rng=0;
    input >> magic >> version;
    if (magic!="MTDEMO" || (version!=0 && version!=1)) throw std::invalid_argument("unsupported save version");
    input >> w >> h >> seed;
    if (version==1) input >> rng;
    input >> turns >> x >> y;
    if (version==1) input >> modern;
    if (!input || seed>0xffffffffu || rng>0xffffffffu || turns<0 || (modern!=0 && modern!=1))
        throw std::invalid_argument("invalid saved state");
    PrototypeGame game(w,h,static_cast<uint32_t>(seed));
    if (version==0) rng=game.rngState();
    std::vector<std::string> cells;
    for (int row=0;row<h;++row) { std::string line; input >> line; cells.push_back(line); }
    std::string extra;
    if (!input || (input>>extra)) throw std::invalid_argument("truncated/trailing save data");
    DemoMap map(std::move(cells),static_cast<uint32_t>(rng));
    if (!map.walkable(x,y)) throw std::invalid_argument("saved player is outside walkable map");
    game.map_=std::move(map);game.player_={x,y};game.turns_=turns;
    game.presentation_=modern ? Presentation::Modern : Presentation::Classic;
    return game;
}
}
