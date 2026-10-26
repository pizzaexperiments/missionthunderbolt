#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace mt {
enum class Presentation { Classic, Modern };
struct Position { int x = 0, y = 0; };
class PrototypeGame {
public:
    PrototypeGame(int width = 20, int height = 12, uint32_t seed = 1);
    bool move(int dx, int dy);
    void setPresentation(Presentation p) { presentation_ = p; }
    Presentation presentation() const { return presentation_; }
    Position player() const { return player_; }
    int turns() const { return turns_; }
    std::string asciiMap() const;
private:
    int width_, height_, turns_ = 0;
    Position player_{1, 1};
    Presentation presentation_ = Presentation::Classic;
    std::vector<std::string> grid_;
};
}
