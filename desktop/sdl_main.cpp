#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "game.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace {
namespace fs=std::filesystem;
void saveAtomic(const fs::path& file,const std::string& data) {
    fs::create_directories(file.parent_path());
    auto temp=file;temp+=".tmp";
    {
        std::ofstream output(temp,std::ios::binary|std::ios::trunc);
        output.write(data.data(),static_cast<std::streamsize>(data.size()));output.flush();
        if(!output) throw std::runtime_error("cannot write save temporary file");
    }
#ifdef _WIN32
    if(!MoveFileExW(temp.c_str(),file.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))
        throw std::runtime_error("cannot replace save file");
#else
    fs::rename(temp,file);
#endif
}
std::string readSave(const fs::path& file) {
    if(fs::file_size(file)>1024*1024) throw std::runtime_error("oversized save file");
    std::ifstream input(file,std::ios::binary);
    if(!input) throw std::runtime_error("cannot read save file");
    return std::string(std::istreambuf_iterator<char>(input),{});
}
void require(bool result,const char* message) {if(!result) throw std::runtime_error(message);}
class Host {
public:
    mt::PrototypeGame game;
    fs::path savePath;
    std::unique_ptr<SDL_Window,decltype(&SDL_DestroyWindow)> window{nullptr,SDL_DestroyWindow};
    std::unique_ptr<SDL_Renderer,decltype(&SDL_DestroyRenderer)> renderer{nullptr,SDL_DestroyRenderer};
    std::vector<SDL_GameController*> controllers;
    int axisX=0,axisY=0,lastX=0,lastY=0;
    bool running=true;
    explicit Host(fs::path directory) : savePath(std::move(directory)/"demo-state.mt") {
        window.reset(SDL_CreateWindow("Thunderbolt RESEARCH DEMO",SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,640,480,SDL_WINDOW_RESIZABLE));
        require(bool(window),SDL_GetError());
        renderer.reset(SDL_CreateRenderer(window.get(),-1,SDL_RENDERER_SOFTWARE));
        require(bool(renderer),SDL_GetError());
        for(int i=0;i<SDL_NumJoysticks();++i) openController(i);
        if(fs::exists(savePath)) {
            try {game=mt::PrototypeGame::load(readSave(savePath));}
            catch(const std::exception& error) {std::cerr<<"Saved demo ignored: "<<error.what()<<'\n';}
        }
    }
    ~Host() {for(auto* controller:controllers) SDL_GameControllerClose(controller);}
    void openController(int index) {
        if(SDL_IsGameController(index)) if(auto* c=SDL_GameControllerOpen(index)) controllers.push_back(c);
    }
    void persist() {saveAtomic(savePath,game.save());}
    void toggle() {game.setPresentation(game.presentation()==mt::Presentation::Classic ? mt::Presentation::Modern : mt::Presentation::Classic);}
    void restart() {auto mode=game.presentation();game=mt::PrototypeGame();game.setPresentation(mode);}
    void event(const SDL_Event& e) {
        if(e.type==SDL_QUIT) running=false;
        else if(e.type==SDL_KEYDOWN) {
            const auto key=e.key.keysym.sym;
            if((e.key.keysym.mod&KMOD_CTRL) && key==SDLK_s) persist();
            else if((e.key.keysym.mod&KMOD_CTRL) && key==SDLK_l) game=mt::PrototypeGame::load(readSave(savePath));
            else if(key==SDLK_ESCAPE || key==SDLK_q) running=false;
            else if(key==SDLK_TAB && !e.key.repeat) toggle();
            else if(key==SDLK_r && !e.key.repeat) restart();
            else if(key==SDLK_RIGHT || key==SDLK_d) game.move(1,0);
            else if(key==SDLK_LEFT || key==SDLK_a) game.move(-1,0);
            else if(key==SDLK_UP || key==SDLK_w) game.move(0,-1);
            else if(key==SDLK_DOWN || key==SDLK_s) game.move(0,1);
        } else if(e.type==SDL_CONTROLLERBUTTONDOWN) {
            switch(e.cbutton.button) {
            case SDL_CONTROLLER_BUTTON_DPAD_RIGHT:game.move(1,0);break;
            case SDL_CONTROLLER_BUTTON_DPAD_LEFT:game.move(-1,0);break;
            case SDL_CONTROLLER_BUTTON_DPAD_UP:game.move(0,-1);break;
            case SDL_CONTROLLER_BUTTON_DPAD_DOWN:game.move(0,1);break;
            case SDL_CONTROLLER_BUTTON_BACK:toggle();break;
            case SDL_CONTROLLER_BUTTON_START:restart();break;
            default:break;
            }
        } else if(e.type==SDL_CONTROLLERAXISMOTION) {
            if(e.caxis.axis==SDL_CONTROLLER_AXIS_LEFTX) axisX=e.caxis.value;
            else if(e.caxis.axis==SDL_CONTROLLER_AXIS_LEFTY) axisY=e.caxis.value;
            else return;
            int x=0,y=0;
            if(std::max(std::abs(axisX),std::abs(axisY))>16000) {
                if(std::abs(axisX)>=std::abs(axisY)) x=axisX>0?1:-1; else y=axisY>0?1:-1;
            }
            if((x!=lastX || y!=lastY) && (x||y)) game.move(x,y);
            lastX=x;lastY=y;
        } else if(e.type==SDL_CONTROLLERDEVICEADDED) openController(e.cdevice.which);
        else if(e.type==SDL_CONTROLLERDEVICEREMOVED) {
            controllers.erase(std::remove_if(controllers.begin(),controllers.end(),[&](SDL_GameController* c) {
                if(SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(c))!=e.cdevice.which) return false;
                SDL_GameControllerClose(c);return true;
            }),controllers.end());
        } else if(e.type==SDL_WINDOWEVENT && e.window.event==SDL_WINDOWEVENT_FOCUS_LOST) {
            lastX=lastY=axisX=axisY=0;persist();
        }
    }
    void draw() {
        const bool modern=game.presentation()==mt::Presentation::Modern;
        std::string title="Thunderbolt RESEARCH DEMO | ";title+=modern?"Modern":"Classic";
        title+=" | Turns: "+std::to_string(game.turns())+" | WASD/arrows, Tab skin, R restart, Ctrl-S save";
        SDL_SetWindowTitle(window.get(),title.c_str());
        int width=0,height=0;SDL_GetRendererOutputSize(renderer.get(),&width,&height);
        SDL_SetRenderDrawColor(renderer.get(),modern?21:255,modern?28:255,modern?36:255,255);SDL_RenderClear(renderer.get());
        const int cell=std::max(1,std::min(width/game.width(),height/game.height()));
        const int left=(width-game.width()*cell)/2,top=(height-game.height()*cell)/2;
        const auto map=game.asciiMap();
        for(int y=0;y<game.height();++y) for(int x=0;x<game.width();++x) {
            const char tile=map[static_cast<size_t>(y*(game.width()+1)+x)];
            if(tile=='@') SDL_SetRenderDrawColor(renderer.get(),0,modern?255:0,modern?255:0,255);
            else if(tile=='#') SDL_SetRenderDrawColor(renderer.get(),modern?95:64,modern?115:64,modern?132:64,255);
            else SDL_SetRenderDrawColor(renderer.get(),modern?36:192,modern?48:192,modern?58:192,255);
            SDL_Rect rect{left+x*cell+1,top+y*cell+1,std::max(1,cell-2),std::max(1,cell-2)};
            SDL_RenderFillRect(renderer.get(),&rect);
        }
        SDL_RenderPresent(renderer.get());
    }
};
void smoke(Host& host) {
    host.restart();host.game.setPresentation(mt::Presentation::Classic);
    SDL_Event e{};e.type=SDL_KEYDOWN;e.key.keysym.sym=SDLK_RIGHT;require(SDL_PushEvent(&e)==1,"queue keyboard");
    e.key.keysym.sym=SDLK_TAB;require(SDL_PushEvent(&e)==1,"queue mode");
    e={};e.type=SDL_CONTROLLERBUTTONDOWN;e.cbutton.button=SDL_CONTROLLER_BUTTON_DPAD_RIGHT;
    require(SDL_PushEvent(&e)==1,"queue controller");
    while(SDL_PollEvent(&e))host.event(e);
    require(host.game.turns()==2,"keyboard/controller moves missing");
    require(host.game.presentation()==mt::Presentation::Modern,"mode switch failed");
    host.draw();host.persist();
    require(mt::PrototypeGame::load(readSave(host.savePath)).save()==host.game.save(),"disk save round-trip failed");
    std::vector<uint32_t> pixels(640*480);
    require(SDL_RenderReadPixels(host.renderer.get(),nullptr,SDL_PIXELFORMAT_ARGB8888,pixels.data(),640*4)==0,SDL_GetError());
    require(std::any_of(pixels.begin(),pixels.end(),[&](uint32_t v){return v!=pixels.front();}),"board rendering is blank");
    std::cout<<"SDL keyboard/controller, shared state, rendered pixels and atomic disk save checks passed\n";
}
}
int main(int argc,char** argv) {
    bool test=false;std::filesystem::path directory;
    for(int i=1;i<argc;++i) {
        std::string arg=argv[i];
        if(arg=="--smoke-test")test=true;
        else if(arg=="--save-dir" && i+1<argc)directory=std::filesystem::u8path(argv[++i]);
        else {std::cerr<<"Usage: mission-thunderbolt-demo [--save-dir PATH] [--smoke-test]\n";return 2;}
    }
    SDL_SetMainReady();
    if(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMECONTROLLER)!=0) {std::cerr<<SDL_GetError()<<'\n';return 1;}
    int result=0;
    try {
        if(directory.empty()) {
            char* pref=SDL_GetPrefPath("pizzaexperiments","missionthunderbolt");
            require(pref!=nullptr,SDL_GetError());directory=std::filesystem::u8path(pref);SDL_free(pref);
        }
        Host host(directory);
        if(test)smoke(host);
        else {
            host.draw();SDL_Event event{};
            while(host.running) {
                if(SDL_WaitEventTimeout(&event,100)) {
                    try {host.event(event);while(SDL_PollEvent(&event))host.event(event);host.draw();}
                    catch(const std::exception& error) {std::cerr<<error.what()<<'\n';}
                }
            }
            host.persist();
        }
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';result=1;}
    SDL_Quit();return result;
}
