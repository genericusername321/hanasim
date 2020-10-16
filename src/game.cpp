/* Game logic for Hanabi */

#include <vector>
#include <iostream>

const int MAXHINTS = 8;
const int MAXSTRIKES = 3;

// actions player can perform during their turn
enum class MoveType {clue, play, discard};

// types of clues a player can give
enum class ClueType {colour, rank};
enum class Colour {red = 1, green, blue, yellow, purple};
enum class Rank {one = 1, two, three, four, five};
const int nColours = 5;
const int nRanks = 5;

typedef unsigned char Player;


class Card {
    public:
        Colour colour;
        Rank rank;

    public:
        Card(Colour c, Rank r) {
            colour = c;
            rank = r;
        }

        bool operator==(const Card& rhs) {
            return ((this->colour == rhs.colour) && (this->rank == rhs.rank));
        }

        bool operator!=(const Card& rhs) {
            return (*this == rhs);
        }
};

class Clue {
    public: 
        Player player;      // receiver of the clue
        ClueType type;      // clue type, can be colour or rank
        Colour cval;        // colour value of clue
        Rank rval;          // rank value of clue

    public: Clue() {};
};

class Move {
    public:
        Player player;      // player at turn
        MoveType move;      // type of move, can be clue, play or discard
        Card play;          // card played this turn
        Card discard;       // card discarded in this turn
        Clue clue;          // clue given in this turn

    public:
        Move();
        Move(Player p) {
            player = p;
        }
};

class GameState {
    public:
        int nHints;
        int nStrikes;
        int nPlayers;
        int nTurnsAfterDeckEmpty;
        int nTurns;
        int handSize;

        std::vector<Card> deck;
        std::vector<Move> moveList;

    public: 
        GameState() {};

        createNewDeck() {
            /* Creates a shuffled deck with a full set of cards for each colour:
               - 3 cards of rank 1 
               - 2 cards of ranks [2, 3, 4]
               - 1 card of rank 5
            */

            std::vector<Card> d;
            for (int ic = Colour::red; ic <= Colour::purple; ic++) {
                for (int ir = Rank::one; ir <= Rank::five; ir++) {
                    d.push_back(Card(ic, ir));
                }
            }
            
            // Can we use a move assignment here?
            this->deck = d;
        }

        showDeck() {
            /* Print out the deck to cout */

            for (auto &c : deck) {
                std::cout << c.colour << " " << c.rank << std::endl;
            }
        }
};

int main() {

    GameState gs();
    gs.createNewDeck();
    gs.showDeck();

    return 0;
}


