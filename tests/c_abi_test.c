#include "api.h"
#include <string.h>
int main(void) {
    mt_game* game = mt_game_create(20,12,1);
    if (!game || mt_api_version()!=1) return 1;
    if (mt_game_move(game,1,0)!=1 || mt_game_turns(game)!=1) return 2;
    if (mt_game_wait(game)!=1 || mt_game_turns(game)!=2) return 8;
    char small[2]={'x','y'};
    if (mt_game_map(game,small,2)<=2 || mt_game_last_error()!=MT_ERROR_BUFFER_TOO_SMALL) return 3;
    if (small[0]!='x' || small[1]!='y') return 4;
    mt_game_destroy(game);
    if (mt_game_create(2147483647,2147483647,1)!=0) return 5;
    if (mt_game_last_error()!=MT_ERROR_INVALID_ARGUMENT) return 6;
    return strcmp(mt_error_message(mt_game_last_error()),"invalid argument")==0 ? 0 : 7;
}
