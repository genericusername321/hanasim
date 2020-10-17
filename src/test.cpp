#include "hanabisim.h"

int main() {



    GameState game;
    game.nColours = 5;
    game.nRanks = 5;
    // game.showCardCounts();
    game.setupGame();
    game.showDeck();
    game.showHands();

    game.discard(4, 1);
    game.showHands();



    return 0;
}


