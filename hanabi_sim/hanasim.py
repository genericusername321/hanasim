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
MAXPLAYERS = 4
COLOURS = ['R', 'G', 'B', 'Y', 'P']
VALUES = [1, 2, 3, 4, 5]
MAXHINTS = 8
STRIKES = 3

# Number of duplicates of a card with a particular value in a fresh deck
CARDCOUNTS = {1: 3,
              2: 2,
              3: 2,
              4: 2,
              5: 1}

# Number of cards each player has in their hand
HANDSIZE = {2: 5,
            3: 5,
            4: 4,
            5: 4}


def cardAsString(card):
    """
    Converts a card to printable string format for logging
    :param card: a tuple of the form (colour, value)
    :return: a string, e.g. "B5" for a card ('B', 5)
    """

    return '{}{}'.format(card[0], card[1])


class Pile:

    def __init__(self, colour):
        self.colour = colour
        self.pile = []

    def getNextCard(self):
        """
        Gets the colour and value of the next card to go on the pile
        :return: tuple: (colour, value)
        """
        nextCard = (self.colour, len(self.pile)+1)
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

class Hint:
    """
    Represents a hint given from one player to another.
    """

    def __init__(self, player, type, value):
        assert(type in ['colour', 'value'])
        if type == 'colour':
            assert(value in COLOURS)
        else:
            assert(value in VALUES)

        self.player = player
        self.type = type
        self.value = value

class Player:
    """
    Class to track the data available to a player.
    """

class GameState:

    def __init__(self, nPlayers=4, seed=0, deck=None):
        """
        Constructor for the gamestate class
        :param nPlayers: integer in the range [MINPLAYERS, MAXPLAYERS], the number of
                        players in the game
        :param seed: optional parameter, seed for the rng to shuffle the deck
        :param deck: optional parameter, a deck of cards as a list of tuples
                    (colour, value)
        """
        assert (nPlayers >= MINPLAYERS)
        assert (nPlayers <= MAXPLAYERS)
        assert (isinstance(seed, int))

        self.nPlayers = nPlayers
        self.rSeed = seed
        self.deck = deck

        self.nHints = MAXHINTS
        self.strikes = 0

        # setup player hands
        self.hands = [[] for _ in range(self.nPlayers)]

        # setup mapping of disc
        self.discarded = {}

        # initialise piles as dictionary, taking colours as keys
        self.piles = {}
        for colour in COLOURS:
            self.piles[colour] = Pile(colour)

        self.hints = []

    def playHint(self, hintFrom, hintTo, hint):
        """
        Player hintFrom hints player hintTo
        :param hintFrom: integer in [0, nPlayers - 1]
        :param hintTo: integer in [0, nPlayers - 1]
        :param hint: Hint object
        :return:
        """

        # Check that we have sufficient number of hints left
        if self.nHints < 1:
            return

        self.nHints -= 1
        self.hints.append(hint)
        logger.info('Player {} hints {} to player {}'.format(hintFrom, hint.value, hintTo))

    def playCard(self, playerID, idx, pile):
        """
        Player a card from playerIDs hand onto a pile
        :param playerID: integer in range [0, nPlayers-1]
        :param idx: index of the card to play, in the player's hand
        :param pile: a Pile
        :return:
        """
        # Check that this is a legal move
        card = self.hands[playerID][idx]
        if pile.getNextCard() == card:
            self.hands[playerID].remove(card)
            pile.pile.append(card)
            logger.info('Player {} successfully plays {}'.format(playerID, cardAsString(card)))
            if card[1] == 5:
                self.addHint()
        else:
            self.strikes += 1
            logger.info('Player {} fails to play {}. {} strikes'.format(playerID, cardAsString(card), self.strikes))
            self.discard(playerID, card, False)

    def discard(self, playerID, card, ismove):
        """
        Discard a card from a player's hand, then draw a new card from the deck.
        :param playerID: integer
        :param card: a tuple (c,v) representing a card
        :param ismove: boolean indicating whether this is a voluntary move,
        gaining a hint, or a forced discard.
        :return:
        """
        self.hands[playerID].remove(card)
        if card in self.discarded:
            self.discarded[card] += 1
        else:
            self.discarded[card] = 1
        logger.info('Player {} discarded {}'.format(playerID, cardAsString(card)))
        logger.debug('Discard pile: {}'.format(self.discarded))
        self.drawCard(playerID)

        if ismove:
            self.addHint()

    def drawCard(self, playerID):
        """
        Deals the top card of the deck to hand of playerID
        :param playerID: an integer in the range [0, nPlayers-1]
        :return:
        """
        if (self.deck):
            card = self.deck.pop()
            self.hands[playerID].append(card)
            logger.info(f'player {playerID} draws {cardAsString(card)}')

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
            - Dealing hands
        :return:
        """

        # Create a shuffled deck if no deck is provided
        if not self.deck:
            self.createDeck()
            self.shuffleDeck()

        # Deal from deck into hands
        self.dealHands()

    def createDeck(self):
        """
        Creates an deck of cards
        :return:
        """
        self.deck = [(colour, value) for colour in COLOURS
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
        for i in range(HANDSIZE[self.nPlayers]):
            for player in range(self.nPlayers):
                self.drawCard(player)