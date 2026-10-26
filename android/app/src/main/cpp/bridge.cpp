#include <jni.h>
#include <mutex>
#include "game.hpp"
namespace { std::mutex lock; mt::PrototypeGame game(20, 12, 1); }
extern "C" JNIEXPORT jstring JNICALL Java_org_missionthunderbolt_prototype_MainActivity_map(JNIEnv* env, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    const auto map = game.asciiMap();
    return env->NewStringUTF(map.c_str());
}
extern "C" JNIEXPORT jint JNICALL Java_org_missionthunderbolt_prototype_MainActivity_move(JNIEnv*, jclass, jint dx, jint dy) {
    std::lock_guard<std::mutex> guard(lock);
    game.move(dx, dy);
    return game.turns();
}
extern "C" JNIEXPORT void JNICALL Java_org_missionthunderbolt_prototype_MainActivity_reset(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    game = mt::PrototypeGame(20, 12, 1);
}
