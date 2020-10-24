#include "hanabisim.h"

int main() {

    GameState game;
    game.setupGame();
    game.showHands();

    game.showPiles();

    return 0;
}
