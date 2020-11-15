"""
hanasim is a simulator for the card game Hanabi.
"""

import random
import logging

# Configure logger
logLevel = logging.INFO

formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
fh = logging.FileHandler(filename='hanabi.log', mode='w')
fh.setLevel(logLevel)
fh.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logLevel)
logger.addHandler(fh)

# Constants
MINPLAYERS = 2
MAXPLAYERS = 5
COLOURS = ['R', 'G', 'B', 'Y', 'P']
VALUES = [1, 2, 3, 4, 5]
MAXHINTS = 8
MAXSTRIKES = 3

# Number of duplicates of a card with a particular value in a fresh deck
CARDCOUNTS = {1: 3,
              2: 2,
              3: 2,
              4: 2,
              5: 1}


class Card:
    """
    A class that models a Hanabi card. It contains the colour and value of
    the card, as well as hints that apply to it.
    """

    def __init__(self, colour, value):
        self.colour = colour
        self.value = value

    def __eq__(self, other):
        if ((self.colour == other.colour) and (self.value == other.value)):
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.colour, self.value))

    def asString(self):
        return '{}{}'.format(self.colour, self.value)

class Firework:

    def __init__(self, colour):
        self.colour = colour
        self.pile = []

    def getNextCard(self):
        """
        Gets the colour and value of the next card to go on the pile
        :return: tuple: (colour, value)
        """
        nextCard = Card(self.colour, len(self.pile)+1)
        return nextCard

    def getTopCard(self):
        """
        Gets the top card of the pile if it is nonempty. otherwise return None
        :return: The top card in the form of a tuple (c,v)
        """
        if self.pile:
            topCard = self.pile[-1]
        else:
            topCard = None

        return topCard

    def addCard(self, card):
        """
        Attempt to play the card on top of this pile.
        :param card: card to be played on this pile
        :return:        Boolean value signifying the whether it the attempt is 
                        successful or not.
        """
        nextCard = self.getNextCard()
        if nextCard == card:
            self.pile.append(card)
            return True
        else:
            return False

class Hint:
    """
    Represents a hint given from one player to another.
    """

    def __init__(self, receivingPlayerID, value):
        """
        :param player:  integer representing the receiving player
        :param value:   integer or char representing the hint value. Must be a 
                        in VALUE or COLOURS
        """
        assert(value in COLOURS or value in VALUES)
        self.playerID = receivingPlayerID
        self.value = value

class Move:
    """
    Represents a move performed by a player in a single turn.
    """
    
    def __init__(self, playerID, moveType, value):

        allowedMoveTypes = ['DISCARD', 'PLAY', 'HINT']
        assert (isinstance(playerID, int))
        assert (moveType in allowedMoveTypes)
        assert (isinstance(value, int) or isinstance(value, Hint))

        self.playerID = playerID
        self.moveType = moveType
        self.value = value

class GameState:

    def __init__(self, nPlayers, handSize, seed=0, deck=None):
        """
        Constructor for the gamestate class
        :param nPlayers: integer in the range [MINPLAYERS, MAXPLAYERS], the number of
                        players in the game
        :param handSize: number of cards in each player's hand
        :param seed: optional parameter, seed for the rng to shuffle the deck
        :param deck: optional parameter, a deck of cards as a list of tuples
                    (colour, value)
        """
        assert (nPlayers >= MINPLAYERS)
        assert (nPlayers <= MAXPLAYERS)
        assert (isinstance(handSize, int))
        assert (handSize > 0)
        assert (isinstance(seed, int))


        self.nHints = MAXHINTS
        self.strikes = 0
        self.score = 0

        self.turn = 0
        self.playerTurn = 0

        self.nPlayers = nPlayers
        self.handSize = handSize
        self.rSeed = seed
        self.deck = deck

        # setup player hands
        self.hands = [[] for _ in range(self.nPlayers)]

        # keep track of number of discarded cards for each type
        self.discarded = {}

        # initialise piles as dictionary, taking colours as keys
        self.fireworks = {}
        for colour in COLOURS:
            self.fireworks[colour] = Firework(colour)

    def doMove(self, move):
        """
        Perform a player move
        :param move: object of type Move
        """

        assert (isinstance(move, Move))
        moveType = move.moveType
        
        # Resolve move depending on movetype
        if moveType == 'DISCARD':
            self.discard(move.playerID, move.value)
        elif moveType == 'PLAY':
            pass 
        elif moveType == 'HINT':
            pass
        else:
            raise ValueError('Illegal move type')


    def playCard(self, playerID, idx, colour):
        """
        Player a card from playerIDs hand onko a pile
        :param playerID: integer in range [0, nPlayers-1]
        :param idx: index of the card to play, in the player's hand
        :param firework: a colour firework to play the card on
        :return:
        """
        # Check that the index refers to a valid card
        assert (idx < len(self.hands[playerID]))

        # Pop the card from the player hand
        card = self.hands[playerID][idx]
        playedSuccess = self.fireworks[colour].addCard(card)
        if playedSuccess:
            self.hands[playerID].pop(idx)
            self.drawCard(playerID)
            self.score += 1
            logger.info('Player {} successfully plays {}'.format(playerID, card.asString()))
            if card.value == 5:
                self.addHint()
        else:
            self.strikes += 1
            logger.info('Player {} fails to play {}. {} strikes'.format(
                playerID, card.asString(), self.strikes))
            self.forcedDiscard(playerID, idx)


    def forcedDiscard(self, playerID, index):
        """
        Discard a card from a player's hand without awarding a hint.
        :param playerID: integer
        :param index: the index of the card to be discarded
        """

        card = self.hands[playerID].pop(index)
        if card in self.discarded:
            self.discarded[card] += 1
        else:
            self.discarded[card] = 1
        logger.info('Player {} discarded {}'.format(playerID, card.asString()))
        logger.info('Discard pile: {}'.format(self.discarded))
        self.drawCard(playerID)

    def discard(self, playerID, index):
        """
        Discard a card from a player's hand, then draw a new card from the deck.
        :param playerID: integer
        :param index: the index of the card to be discarded
        :return:
        """
        self.addHint()
        self.forcedDiscard(playerID, index)

    def drawCard(self, playerID):
        """
        Deals the top card of the deck to hand of playerID
        :param playerID: an integer in the range [0, nPlayers-1]
        :return:
        """
        if (self.deck):
            card = self.deck.pop()
            self.hands[playerID].append(card)
            logger.info(f'player {playerID} draws {card.asString()}')

    def addHint(self):
        """
        Increment the number of hints
        :return:
        """
        if self.nHints < MAXHINTS:
            self.nHints += 1

        logger.info('There are {} hints available'.format(self.nHints))

    def setup(self):
        """
        Setup the game by:
            - Creating a sorted deck
            - Setup discarded pile
            - Dealing hands
        :return:
        """

        # Create a shuffled deck if no deck is provided
        if not self.deck:
            self.createDeck()
            self.shuffleDeck()

        # Setup pile of discarded cards
        self.setupDiscardedPile()

        # Deal from deck into hands
        self.dealHands()

    def createDeck(self):
        """
        Creates a deck of cards
        :return:
        """
        self.deck = [Card(colour, value) for colour in COLOURS
                     for value in VALUES for _ in range(CARDCOUNTS[value])]
        logger.info('Creating deck...')

    def shuffleDeck(self):
        """
        Shuffles the deck
        :return:
        """
        logger.info('Shuffling deck...')
        random.seed(self.rSeed)
        random.shuffle(self.deck)

    def dealHands(self):
        """
        Deal initial hands
        :return:
        """
        for i in range(self.handSize):
            for player in range(self.nPlayers):
                self.drawCard(player)

    def setupDiscardedPile(self):
        """
        Setup the discarded pile
        :return:
        """

        cards = [Card(colour, value) for colour in COLOURS
                for value in VALUES]

        for card in cards:
            self.discarded[card] = 0


