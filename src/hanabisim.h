/* Game logic for Hanabi */

#ifndef HANABISIM
#define HANABISIM

#define NCOLOR 5
#define NRANK 5


#include <algorithm>
#include <iostream>
#include <unordered_map>
#include <vector>
#include <random>

const int MAXHINTS = 8;
const int MAXSTRIKES = 3;

// actions player can perform during their turn
enum class MoveType {clue, play, discard};

// types of clues a player can give
enum class ClueType {colour, rank};

enum Color {purple, blue, green, yellow, red};
enum Rank {one, two, three, four, five};

inline int operator++(const Color& c) {return (c+1);}
inline int operator++(const Rank& r) {return (r+1);}



class Card;

typedef int Player;
typedef std::vector<Card> Hand;
typedef std::vector<Card> Pile;
typedef std::vector<Card> Deck;


class Card {
    public:
        int colour;
        int rank;

    public:
        Card(int c, int r) {
            colour = c;
            rank = r;
        }

        void showCard() const{
            using std::cout;
            using std::endl;
            cout << colour << " " << rank << endl;
            return;
        }

        bool operator==(const Card& rhs) const{
            return ((this->colour == rhs.colour) && (this->rank == rhs.rank));
        }

        bool operator!=(const Card& rhs) const{
            return (*this == rhs);
        }
};

class cardHasher {
    public:
        std::size_t operator()(const Card& card) const {
            using std::size_t;
            using std::hash;

            // As colour is in [1..5], rank in [1..5], the combination
            // 10*colour + rank is unique for every card.
            int c = static_cast<int>(card.colour);
            int r = static_cast<int>(card.rank);
            int keyVal = 10*c + r;

            return (hash<int>()(keyVal));
        }
};

class GameState {
    public:

        // game information
        int nHints;     // number of hints 
        int nStrikes;   // number of strikes


        Deck deck;
        std::vector<Hand> hands;
        std::vector<Pile> piles;
        std::unordered_map<Card, int, cardHasher> cardCounts;

        // administrative
        int nColours;
        int nRanks;
        int nPlayers;   // number of players
        int nHand;      // number of cards per hand
        int rSeed;

    public:
        GameState() {
            
            nColours = NCOLOR;
            nRanks = NRANK;
            rSeed = 0;

            nHints = 8;
            nStrikes = 0;

            nPlayers = 5;
            switch (nPlayers) {
                case 2: nHand = 5; break;
                case 3: nHand = 5; break;
                case 4: nHand = 4; break;
                case 5: nHand = 4; break;
            }
        }

        void setupGame() {
            initCardCounts();
            createDeck();
            shuffleDeck(rSeed);

            for (int i = 0; i < nPlayers; i++) {
                Hand h;
                hands.push_back(h);
            }
            dealHands();
        }

        void showCardCounts() {
            for (auto const &pair : cardCounts) {
                std::cout << (pair.first).colour << " " << (pair.first).rank << 
                    ": " << (pair.second) << std::endl;
            }
            return;
        }

        void showDeck() {
            std::cout << "DECK: " << deck.size() << std::endl;
            for (auto &c : deck) {
                std::cout << c.colour << " " << c.rank << std::endl;
            }
            std::cout << std::endl;
            return;
        }

        void showHands() {
            for (Player i = 0; i < nPlayers; i++) {
                std::cout << "HAND " << i << ": " << std::endl;
                for (auto &c : hands[i]) {
                    c.showCard();
                }
                std::cout << std::endl;
            }
            return;
        }

        void discard(Player p, int i) {
            /* Discard card at index i in player p's hand */

            // discard
            Card c = hands[p][i];
            cardCounts[c]--;
            hands[p].erase(hands[p].begin() + i);

            // draw a card
            drawCard(p);

            return;
        }

        void play(Player p, int i, int j) {
            /* Attempt to play card i of player p's hand onto pile j */

            Card toPlay = hands[p][i];

            // Check if card is of the right colour
            if (toPlay.colour != j+1) {
                discard(p, i);
                nStrikes++;
                return;
            }


            return;
        }



    private:
        void initCardCounts() {

            for (int c = purple; c <= red; c++) {
                for (int r = one; r <= five; r++) {
                    Card card(c, r);
                    cardCounts[card] = 0;
                }
            }

            //for (int colour = 1; colour <= nColours; colour++) {
            //    for (int rank = 1; rank <= nRanks; rank++) {
            //        Card c(colour, rank);
            //        cardCounts[c] = 0;
            //    }
            //}

            return;
        }

        void drawCard(Player p) {
            // skip if deck is empty
            if (deck.empty()) return;

            hands[p].push_back(deck.back());
            deck.pop_back();
        }

        void dealHands() {
            
            for (int i = 0; i < nHand; i++) {
                for (Player j = 0; j < nPlayers; j++) {
                    drawCard(j);
                }
            }
            return;
        }

        void createDeck() {
            std::vector<Card> newDeck;
            for (int colour = purple; colour <= red; colour++) {
                for (int rank = one; rank <= five; rank++) {

                    int d = 0;
                    switch (rank) {
                        case one: d = 3; break;
                        case two: d = 2; break;
                        case three: d = 2; break;
                        case four: d = 2; break;
                        case five: d = 1; break;
                    }

                    for (int i = 0; i < d; i++) {
                        Card c(colour, rank);
                        newDeck.push_back(c);
                        cardCounts[c]++;
                    }
                }
            }
            deck = newDeck;
        }

        void shuffleDeck(int seed) {
            std::mt19937 rand(seed);
            std::random_shuffle(deck.begin(), deck.end());
        }

};

#endif
