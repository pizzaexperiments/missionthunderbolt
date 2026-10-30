#pragma once
#include "engine/map.hpp"
#include "engine/research_mission.hpp"
#include <cstdint>
#include <optional>
#include <string>
namespace mt {
enum class Presentation { Classic, Modern };
struct Position { int x = 0, y = 0; };
class PrototypeGame {
public:
    PrototypeGame(int width = 20, int height = 12, uint32_t seed = 1);
    static PrototypeGame researchMission(uint32_t seed);
    bool isResearchMission() const { return mission_.has_value(); }
    bool pickup();
    unsigned inventoryCount() const { return mission_ && mission_->carried() ? 1u : 0u; }
    std::string missionStatus() const;
    bool move(int dx, int dy);
    bool wait(); // Manual v1.0 p.28: one action in the current location.
    void setPresentation(Presentation p) { presentation_ = p; }
    Presentation presentation() const { return presentation_; }
    Position player() const { return player_; }
    int turns() const { return turns_; }
    int width() const { return mission_ ? ResearchMission::Width : map_.width(); }
    int height() const { return mission_ ? ResearchMission::Height : map_.height(); }
    uint32_t seed() const { return seed_; }
    uint32_t rngState() const { return mission_ ? mission_->rngState().local_seed : map_.rngState(); }
    std::string asciiMap() const;
    std::string save() const;
    static PrototypeGame load(const std::string& data);
private:
    DemoMap map_;
    std::optional<ResearchMission> mission_;
    uint32_t seed_;
    int turns_ = 0;
    Position player_{1, 1};
    Presentation presentation_ = Presentation::Classic;
};
}
