#include "game.hpp"
#include <iostream>
#include <string>
int main(){
    mt::PrototypeGame game(20,12,1);
    std::cout<<"Mission Thunderbolt RESEARCH DEMO, not original gameplay\nWASD move, Space wait, R restart, Q quit\n";
    std::string command;
    for(;;){
        std::cout<<game.asciiMap()<<"Turns: "<<game.turns()<<" > "<<std::flush;
        if(!std::getline(std::cin,command)||command=="q"||command=="Q")break;
        if(command=="r"||command=="R"){game=mt::PrototypeGame(20,12,1);continue;}
        if(command==" ")game.wait();
        if(command=="w"||command=="W")game.move(0,-1);
        if(command=="s"||command=="S")game.move(0,1);
        if(command=="a"||command=="A")game.move(-1,0);
        if(command=="d"||command=="D")game.move(1,0);
    }
}
