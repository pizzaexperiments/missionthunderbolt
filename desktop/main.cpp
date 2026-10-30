#include "game.hpp"
#include <iostream>
#include <string>
int main(){
    mt::PrototypeGame game=mt::PrototypeGame::researchMission(1);
    std::cout<<"Mission Thunderbolt RESEARCH MISSION, authored gameplay\nWASD move, Space wait, G collect sample, N new seed, R restart, Q quit\n";
    std::string command;
    for(;;){
        std::cout<<game.asciiMap()<<game.missionStatus()<<" | Turns: "<<game.turns()<<" > "<<std::flush;
        if(!std::getline(std::cin,command)||command=="q"||command=="Q")break;
        if(command=="r"||command=="R"){game=mt::PrototypeGame::researchMission(game.seed());continue;}
        if(command=="n"||command=="N"){game=mt::PrototypeGame::researchMission(game.seed()+1u);continue;}
        if(command=="g"||command=="G")game.pickup();
        if(command==" ")game.wait();
        if(command=="w"||command=="W")game.move(0,-1);
        if(command=="s"||command=="S")game.move(0,1);
        if(command=="a"||command=="A")game.move(-1,0);
        if(command=="d"||command=="D")game.move(1,0);
    }
}
