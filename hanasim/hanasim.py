"""
hanasim is a simulator for the card game Hanabi.
"""

import random
import logging

# Constants
COLOURS = ['R', 'G', 'B', 'Y', 'P']
VALUES = [1, 2, 3, 4, 5]

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
        if (self.colour == other.colour) and (self.value == other.value):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.value < other.value:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.value > other.value:
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.colour, self.value))

    def __str__(self):
        return '{}{}'.format(self.colour, self.value)

    def __repr__(self):
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
        return Card(self.colour, len(self.pile) + 1)

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

    def __repr__(self):
        """
        Represent firework by its top card
        """

        if self.pile:
            return self.pile[-1].__repr__()
        else:
            return self.colour


class Hint:
    """
    Represents a hint given from one player to another.
    """

    def __init__(self, receivingPlayerID, value):
        """
        :param receivingPlayerID:  integer representing the receiving player
        :param value:   integer or char representing the hint value. Must be a
                        in VALUE or COLOURS
        """
        assert (value in COLOURS or value in VALUES)
        self.playerID = receivingPlayerID
        self.value = value


class PlayCard:

    def __init__(self, index, colour):
        assert (isinstance(index, int))
        assert (colour in COLOURS)

        self.index = index
        self.colour = colour


class Move:
    """
    Represents a move performed by a player in a single turn.
    """

    def __init__(self, playerID, moveType, moveDescription):
        """

        @rtype: object
        """
        allowedMoveTypes = ['DISCARD', 'PLAY', 'HINT']
        assert (isinstance(playerID, int))
        assert (moveType in allowedMoveTypes)
        assert (isinstance(moveDescription, int) or
                isinstance(moveDescription, Hint) or
                isinstance(moveDescription, PlayCard))

        self.playerID = playerID
        self.moveType = moveType
        self.moveDescription = moveDescription


class DiscardPile:

    def __init__(self, maxCardCounts):
        """
        Constructor for the DiscardPile class
        :param maxCardCounts: dictionary mapping the value of a card to the number
                            of occurrences of that card in the deck
        """
        self.maxCardCounts = maxCardCounts
        self.cardCounts = {}
        self.deadCards = set()
        self.setup()
        self.total = 0

    def setup(self):
        """
        Initiate the discard pile to empty
        """

        cards = [Card(colour, value) for colour in COLOURS for value in VALUES]
        self.cardCounts = {card: 0 for card in cards}
        self.deadCards = set()
        self.total = 0

    def getMaxScore(self):
        """
        Compute the maximum possible score, without considering the number of turns
        left.
        """

        maxScore = 0
        for colour in COLOURS:
            for value in VALUES:
                card = Card(colour, value)
                if self.cardCounts.get(card) < self.maxCardCounts.get(value):
                    maxScore += 1
                else:
                    break

        return maxScore

    def discard(self, card):
        """
        Add card to discard pile, and if all copies have been discarded, add to set of dead
        cards
        """

        assert (card in self.cardCounts)
        self.cardCounts[card] += 1
        self.total += 1

        if self.cardCounts[card] == self.maxCardCounts.get(card.value):
            # Add all cards of same colour with greater value
            deadCards = [Card(card.colour, value) for value in VALUES if value >= card.value]
            for c in deadCards:
                self.deadCards.add(c)

    def remove(self, card):
        """
        Remove a card from discard pile
        """

        assert (card in self.cardCounts)
        assert (self.cardCounts[card] > 0)

        self.cardCounts[card] -= 1

    def getCriticalCards(self):
        """
        Retrieve a list of cards of which only 1 copy is left in the game
        """

        criticalCards = [card for card in self.cardCounts if \
                         self.cardCounts[card] == self.maxCardCounts[card.value] - 1]
        return criticalCards


class GameState:
    # Class constants
    MINPLAYERS = 2
    MAXPLAYERS = 5
    MINHAND = 4
    MAXHAND = 5
    MAXHINTS = 8
    MAXSTRIKES = 3
    HANDSIZE = {
        2: 5,
        3: 5,
        4: 4,
        5: 4}
    TOTALCARDS = 50

    def __init__(self, nPlayers, handSize, seed=0, deck=None, logger=None):
        """
        Constructor for the GameState class
        :param nPlayers: integer in the range [MINPLAYERS, MAXPLAYERS], the number of
                        players in the game
        :param handSize: number of cards in each player's hand
        :param seed: optional parameter, seed for the rng to shuffle the deck
        :param deck: optional parameter, a deck of cards as a list of tuples
                    (colour, value)
        """

        assert (isinstance(nPlayers, int))
        assert (isinstance(handSize, int))
        assert (isinstance(seed, int))

        assert (self.MINPLAYERS <= nPlayers <= self.MAXPLAYERS)
        assert (self.MINHAND <= handSize <= self.MAXHAND)

        self.isOver = False

        self.nHints = self.MAXHINTS
        self.strikes = 0
        self.score = 0

        self.turn = 0
        self.playerTurn = 0
        self.turnAfterEmpty = nPlayers

        self.nPlayers = nPlayers
        self.handSize = handSize
        self.deck = deck

        self.random = random
        self.random.seed(seed)

        if logger:
            self.logger = logger
        else:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.CRITICAL)
            self.logger = logger

        # List of moves
        self.moveHistory = []

        # Player hands
        self.hands = [[] for _ in range(self.nPlayers)]

        # Discard pile
        self.discardPile = DiscardPile(CARDCOUNTS)

        self.playedCards = set()

        # Fireworks
        self.fireworks = {}
        for colour in COLOURS:
            self.fireworks[colour] = Firework(colour)

    def getPlayerHand(self, requestPlayerID, targetPlayerID):
        """
        Get a player hand
        :param requestPlayerID: player ID of target
        :param targetPlayerID: player ID of requester
        :return hand: List of cards, representing the playerIdTarget's hand.
        """

        if requestPlayerID == targetPlayerID:
            raise ValueError("Player cannot request their own hand!")

        return self.hands[targetPlayerID]

    def doMove(self, move):
        """
        Perform a player move
        :param move: object of class Move
        """

        assert (isinstance(move, Move))
        moveType = move.moveType

        self.logger.info(f'Turn {self.turn}: Player {self.turn % self.nPlayers}')
        self.logger.debug(f'Hand: {self.hands[self.turn % self.nPlayers]}')
        self.logger.debug(f'Fireworks: {self.fireworks}')

        # Correct player trying to make the move
        assert move.playerID == self.playerTurn

        # Resolve move depending on movetype
        if moveType == 'DISCARD':
            self.discard(move.playerID, move.moveDescription)
        elif moveType == 'PLAY':
            self.playCard(move.playerID, move.moveDescription.index, move.moveDescription.colour)
        elif moveType == 'HINT':
            assert self.nHints > 0
            self.nHints -= 1
        else:
            raise ValueError('Illegal move type')

        self.moveHistory.append(move)
        self.turn += 1
        self.playerTurn = self.turn % self.nPlayers

        if self.strikes == self.MAXSTRIKES:
            self.isOver = True
            return

        if not self.deck:
            self.turnAfterEmpty -= 1
            self.logger.info(f'Deck is empty, {self.turnAfterEmpty} turns left!')

        if self.turnAfterEmpty == 0:
            self.isOver = True
            self.logger.info(f'Game is over! Score: {self.score}')

    def playCard(self, playerID, idx, colour):
        """
        Player a card from playerIDs hand onto a pile
        :param playerID: integer in range [0, nPlayers-1]
        :param idx: index of the card to play, in the player's hand
        :param colour: a colour firework to play the card on
        :return:
        """
        # Check that the index refers to a valid card
        assert (idx < len(self.hands[playerID]))

        # Pop the card from the player hand
        card = self.hands[playerID][idx]
        playedSuccess = self.fireworks[colour].addCard(card)
        if playedSuccess:
            self.playedCards.add(card)
            self.hands[playerID].pop(idx)
            self.score += 1
            self.logger.info('Player {} successfully plays {}'.format(playerID, str(card)))
            if card.value == 5:
                self.addHint()

            self.drawCard(playerID)
        else:
            self.strikes += 1
            self.logger.info('Player {} fails to play {}. {} strikes'.format(
                playerID, card.asString(), self.strikes))
            self.forcedDiscard(playerID, idx)

    def forcedDiscard(self, playerID, index):
        """
        Discard a card from a player's hand without awarding a hint.
        :param playerID: integer
        :param index: the index of the card to be discardPile
        """

        card = self.hands[playerID].pop(index)
        self.discardPile.discard(card)
        self.logger.info('Player {} discards {}'.format(playerID, card.asString()))
        self.logger.debug(f'{self.discardPile.cardCounts}')
        self.drawCard(playerID)

    def discard(self, playerID, index):
        """
        Discard a card from a player's hand, then draw a new card from the deck.
        :param playerID: integer
        :param index: the index of the card to be discardPile
        :return:
        """
        self.forcedDiscard(playerID, index)
        self.addHint()

    def drawCard(self, playerID):
        """
        Deals the top card of the deck to hand of playerID
        :param playerID: an integer in the range [0, nPlayers-1]
        :return:
        """
        assert (len(self.hands[playerID]) < self.handSize)

        if self.deck:
            card = self.deck.pop()
            self.hands[playerID].append(card)
            self.logger.info(f'player {playerID} draws {card.asString()}')

    def addHint(self):
        """
        Increment the number of hints
        :return:
        """
        if self.nHints < self.MAXHINTS:
            self.nHints += 1

        self.logger.info('A hint has been added. There are {} hints available'.format(self.nHints))

    def reset(self):
        """
        Reset the game state to the original state.
        :return:
        """

        self.logger.info('Resetting game state')

        self.nHints = 8
        self.strikes = 0
        self.turn = 0
        self.playerTurn = 0
        self.turnAfterEmpty = self.nPlayers

        self.deck = None
        self.score = 0
        self.moveHistory = []

        self.hands = [[] for _ in range(self.nPlayers)]

        self.discardPile.setup()

        for colour in COLOURS:
            self.fireworks[colour] = Firework(colour)

        self.isOver = False

    def setup(self):
        """
        Setup the game by:
            - Creating a sorted deck
            - Setup discardPile pile
            - Dealing hands
        :return:
        """

        self.logger.info('Setting up a new game')

        # Create a shuffled deck if no deck is provided
        if self.deck is None:
            self.createDeck()
            self.shuffleDeck()

        # Deal from deck into hands
        self.hands = [[] for _ in range(self.nPlayers)]
        self.dealHands()
        self.logger.info(f'Game setup complete. Game starting now...')

    def createDeck(self):
        """
        Creates a deck of cards
        :return:
        """
        self.deck = [Card(colour, value) for colour in COLOURS
                     for value in VALUES for _ in range(CARDCOUNTS[value])]
        self.logger.info('Creating deck...')

    def shuffleDeck(self):
        """
        Shuffles the deck
        :return:
        """
        self.logger.debug('Shuffling deck...')
        self.random.shuffle(self.deck)

    def dealHands(self):
        """
        Deal initial hands
        :return:
        """
        for i in range(self.handSize):
            for player in range(self.nPlayers):
                self.drawCard(player)

    def getMaxScore(self):
        """
        Compute maximum achievable score
        @return:
        """

        return self.discardPile.getMaxScore()

    def computePace(self):
        """
        Compute the pace, which is the maximum number of discards allowed to
        achieve maximum score
        """

        maxScore = self.discardPile.getMaxScore()
        return self.score + len(self.deck) + self.nPlayers - maxScore

    def getPlayableCards(self):
        """
        Get a list of all currently playable cards
        @return: list of Cards
        """

        playableCards = [firework.getNextCard() for (colour, firework) in self.fireworks.items()]
        return playableCards

    def isUseless(self, card):
        """
        Check whether a given card is a dead card
        """

        return card in self.playedCards or card in self.discardPile.deadCards

    def isCritical(self, card):
        """
        Check whether there is only 1 left of the given card
        """

        if card in self.discardPile.getCriticalCards():
            return True
        else:
            return False

    def hasCard(self, playerID, card):
        """
        Query whether player playerID has a given card
        """

        return card in self.hands[playerID]

