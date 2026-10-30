#include <jni.h>
#include <mutex>
#include "game.hpp"
namespace { std::mutex lock; mt::PrototypeGame game=mt::PrototypeGame::researchMission(1); }
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
    try {
        const auto presentation=game.presentation();
        auto candidate=game.isResearchMission()?mt::PrototypeGame::researchMission(game.seed()):mt::PrototypeGame(20,12,1);
        candidate.setPresentation(presentation);game=std::move(candidate);
    } catch (...) { /* Preserve the current world if reset cannot allocate. */ }
}
extern "C" JNIEXPORT jint JNICALL Java_org_missionthunderbolt_prototype_MainActivity_turnCount(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    return game.turns();
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_missionthunderbolt_prototype_MainActivity_isModern(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    return game.presentation()==mt::Presentation::Modern ? JNI_TRUE : JNI_FALSE;
}
extern "C" JNIEXPORT void JNICALL Java_org_missionthunderbolt_prototype_MainActivity_setModern(JNIEnv*, jclass, jboolean modern) {
    std::lock_guard<std::mutex> guard(lock);
    game.setPresentation(modern ? mt::Presentation::Modern : mt::Presentation::Classic);
}
extern "C" JNIEXPORT jstring JNICALL Java_org_missionthunderbolt_prototype_MainActivity_snapshot(JNIEnv* env, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    try { const auto data=game.save(); return env->NewStringUTF(data.c_str()); }
    catch (...) { return nullptr; }
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_missionthunderbolt_prototype_MainActivity_restore(JNIEnv* env, jclass, jstring saved) {
    if (!saved) return JNI_FALSE;
    const char* text=env->GetStringUTFChars(saved,nullptr);
    if (!text) return JNI_FALSE;
    bool restored=false;
    try {
        auto candidate=mt::PrototypeGame::load(text);
        std::lock_guard<std::mutex> guard(lock);
        game=std::move(candidate); restored=true;
    } catch (...) { }
    env->ReleaseStringUTFChars(saved,text);
    return restored ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jint JNICALL Java_org_missionthunderbolt_prototype_MainActivity_waitTurn(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    game.wait();
    return game.turns();
}

extern "C" JNIEXPORT jboolean JNICALL Java_org_missionthunderbolt_prototype_MainActivity_researchMission(JNIEnv*, jclass, jint seed) {
    try {
        auto candidate=mt::PrototypeGame::researchMission(static_cast<uint32_t>(seed));
        std::lock_guard<std::mutex> guard(lock);candidate.setPresentation(game.presentation());game=std::move(candidate);
        return JNI_TRUE;
    } catch (...) { return JNI_FALSE; }
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_missionthunderbolt_prototype_MainActivity_pickup(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    try {return game.pickup()?JNI_TRUE:JNI_FALSE;}catch (...) {return JNI_FALSE;}
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_missionthunderbolt_prototype_MainActivity_isResearchMission(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);return game.isResearchMission()?JNI_TRUE:JNI_FALSE;
}
extern "C" JNIEXPORT jint JNICALL Java_org_missionthunderbolt_prototype_MainActivity_inventoryCount(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);return static_cast<jint>(game.inventoryCount());
}
extern "C" JNIEXPORT jint JNICALL Java_org_missionthunderbolt_prototype_MainActivity_missionSeed(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> guard(lock);return static_cast<jint>(game.seed());
}
extern "C" JNIEXPORT jstring JNICALL Java_org_missionthunderbolt_prototype_MainActivity_missionStatus(JNIEnv* env, jclass) {
    std::lock_guard<std::mutex> guard(lock);
    try {const auto status=game.missionStatus();return env->NewStringUTF(status.c_str());}catch (...) {return nullptr;}
}
