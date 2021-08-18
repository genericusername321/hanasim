""" hanasim is a hanabi game engine

hanasim aims to be a fast hanabi engine to run hanabi simulations for user agents
implementing various hanabi strategies. To be fast, datatypes are implemented
as follows:
    - Cards are represented as tuples (colour, rank). Colours can range from
      0 to 4 and the rank varies from 1 to 5, following hanabi-live convention.

    - Fireworks are represented as a tuple (colour, rank), where the rank is the
      rank of the highest card currently on the firework.

    - Actions are presented as a tuple (type, target, value). List of actions
      types:
        0. Play: target refers to the index of the card to be played, in the
           hand of the player whose turn it is. Value indicates the colour.
        1. Discard: target refers to the card that is being discarded. Value
           is true if voluntary discard, false for a strike
        2. Colour clue: target refers to receiving player, 0 - 1st player, 1 - 2nd
           player etc. Value refers to the colour in [0..4]
        3. Value clue: target refers to receiving player, value in [1..5]
        4. Game end: target refers to player ending game, value corresponds to
           end game reason:
            1: for normal end (deck empty / completed all fireworks?)
            2: strikeout
            3: timeout

For visualisation purposes, hanasim can write a JSON dump compatible with the
hanabi-live replay viewer.

"""

import random

# Constants
PLAY = 0
DISCARD = 1
HINTCOLOUR = 2
HINTRANK = 3


class Board:
    """Board implements the game logic for a game of Hanabi"""

    MAXHINTS = 8
    MAXSTRIKES = 3
    MAXCOLOUR = 4
    MAXRANK = 5
    NUMCARDS = 50

    # Map number of card in hand to number of players in game
    HANDSIZE = {2: 5, 3: 5, 4: 4, 5: 4}

    # Map number of duplicates of a card for each given rank
    CARDCOUNTS = {1: 3, 2: 2, 3: 2, 4: 2, 5: 1}

    def __init__(self, num_players, deck=None):
        """
        Constructor for the GameState class
        :param num_players: integer indicating the number of players in this game
        :param deck: optional parameter, a deck of cards as a list of tuples
        """

        self.game_over = False

        # game constants
        self.num_hints = self.MAXHINTS
        self.num_players = num_players

        # board data
        self.strikes = 0
        self.score = 0
        self.turn = 0
        self.bonus_turns = num_players
        self.index = 0
        self.deck = deck
        self.fireworks = {i: [i, 0] for i in range(self.MAXCOLOUR + 1)}
        self.discard_pile = {
            (colour, rank): 0
            for colour in range(self.MAXCOLOUR + 1)
            for rank in range(1, self.MAXRANK + 1)
        }

        # player hands contain the index to the card in the deck
        self.player_hands = [[] for _ in range(self.num_players)]
        self.player_hints = [[] for _ in range(self.num_players)]

        # data for faster bookkeeping
        self.action_history = []
        self.played_cards = set()
        self.cards_on_table = {
            (colour, rank): self.CARDCOUNTS[rank]
            for colour in range(self.MAXCOLOUR + 1)
            for rank in range(1, self.MAXRANK + 1)
        }
        self.critical_cards = set()

    def generate_deck(self):
        """Generate a shuffled deck of Hanabi cards"""
        deck = [
            (colour, rank)
            for colour in range(self.MAXCOLOUR + 1)
            for rank in range(1, self.MAXRANK + 1)
            for _ in range(self.CARDCOUNTS[rank])
        ]
        random.shuffle(deck)
        self.deck = deck

    def deal(self):
        """Deal cards from deck into player hands at start of game"""
        for _ in range(self.HANDSIZE[self.num_players]):
            for j in range(self.num_players):
                self.draw(j)

    def draw(self, player):
        """Draw a card for player"""
        if self.index == self.NUMCARDS:
            self.bonus_turns -= 1
            if self.bonus_turns == 0:
                self.game_over = True
            return

        self.player_hands[player].append(self.index)
        self.player_hints[player].append([None, None])
        self.index += 1

    def resolve_move(self, player, action_attempt):
        """Play out one move by a given player
        :param action_attempt: This is the action that the player at move
                intends to play.
        """

        action_type, target, value = action_attempt

        if action_type == PLAY:
            action = self.play(player, target, value)

        elif action_type == DISCARD:
            if self.num_hints < 8:
                self.num_hints += 1
            action = self.discard(player, target)

        elif action_type == HINTCOLOUR:
            self.hint_colour(target, value)
            action = (HINTCOLOUR, value)

        elif action_type == HINTRANK:
            self.hint_rank(target, value)
            action = (HINTRANK, value)

        else:
            raise ValueError("Invalid action type")

        self.action_history.append(action)
        if self.strikes == self.MAXSTRIKES:
            self.game_over = True

        self.turn += 1

    def play(self, player, target, value):
        """Play a card

        Parameters:
            - player int: player id
            - target int: index of card in player's hand
            - value  int: colour of firework
        """

        card_index = self.player_hands[player][target]
        card = self.deck[card_index]
        action = (PLAY, card_index, None)

        # If card is illegal, discard with strike
        if card[0] != value or card[1] != self.fireworks[value][1] + 1:
            # Discard the card without hint
            self.discard(player, target)
            self.strikes += 1
            return action

        # Play the card
        self.player_hands[player].pop(target)  # Remove card from hand
        self.fireworks[value][1] += 1  # Add card to firework
        self.draw(player)

        # A hint is obtained if the firework is completed
        if self.fireworks[value][1] == self.MAXRANK and self.num_hints < 8:
            self.num_hints += 1

        return action

    def discard(self, player, target):
        """Discard a card

        :param player: player id
        :param target: index of card in player's hand
        """

        # remove card from hand
        card_index = self.player_hands[player][target]
        self.player_hands[player].pop(target)

        # move card onto discard pile
        card = self.deck[card_index]
        self.discard_pile[card] += 1

        self.draw(player)
        return (DISCARD, card_index)

    def hint_colour(self, player, value):
        """Provide a colour hint to a player

        :param player: index of player receiving hint
        :param value: colour to hint

        We can probably make the hint_colour and hint_rank methods smarter
        by implementing a hash table that maps deck index to colours or
        rank respectively. That would avoid iterating over the cards.
        Perhaps we should use a mutable datastructure to hold the information?
        """

        card_colours = [self.deck[index][0] for index in self.player_hands[player]]
        for i, colour in enumerate(card_colours):
            if colour == value:
                self.player_hints[i][0] = value

    def hint_rank(self, player, value):
        """Provide a rank hint to a player

        :param player: index of player receiving hint
        :param value: rank to hint
        """

        card_ranks = [self.deck[index][1] for index in self.player_hands[player]]
        for i, rank in enumerate(card_ranks):
            if rank == value:
                self.player_hints[i][1] = value
