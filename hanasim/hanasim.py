""" hanasim is a hanabi game engine

hanasim aims to be a fast hanabi engine to run simulations for user agents
that implement hanabi strategies.
"""

import random

# Constants
PLAY = 0
DISCARD = 1
HINTCOLOUR = 2
HINTRANK = 3


class Board:
    """Board implements Hanabi game logic"""

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
        self.handsize = self.HANDSIZE[self.num_players]

        # board data
        self.strikes = 0
        self.score = 0
        self.turn = 0
        self.bonus_turns = num_players
        self.index = 0
        self.deck = deck
        self.fireworks = [0 for _ in range(self.MAXCOLOUR + 1)]
        self.discard_pile = {
            (colour, rank): 0
            for colour in range(self.MAXCOLOUR + 1)
            for rank in range(1, self.MAXRANK + 1)
        }

        # player hands contain the index to the card in the deck
        self.player_hands = [[] for _ in range(self.num_players)]
        self.player_hints = [[None, None] for _ in range(self.NUMCARDS)]

        # data for faster bookkeeping
        self.action_history = []
        self.played_cards = set()
        self.dead_cards = set()
        self.critical_cards = set()
        self.num_discarded = 0
        self.cards_on_table = {
            (colour, rank): self.CARDCOUNTS[rank]
            for colour in range(self.MAXCOLOUR + 1)
            for rank in range(1, self.MAXRANK + 1)
        }

    def setup(self):
        """Generate deck and deal cards"""
        if not self.deck:
            self.generate_deck()

        # Find all critical cards
        card_deck = [self.deck[i] for i in range(len(self.deck))]

        for card in card_deck:
            if self.CARDCOUNTS[card[1]] == 1:
                self.critical_cards.add(card)

        self.deal()

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
            assert player != target
            assert self.num_hints > 0
            self.hint_colour(target, value)
            action = (HINTCOLOUR, value)

        elif action_type == HINTRANK:
            assert player != target
            assert self.num_hints > 0
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
        if card[0] != value or card[1] != self.fireworks[value] + 1:
            # Discard the card without hint
            self.discard(player, target)
            self.strikes += 1
            return action

        # Play the card
        self.player_hands[player].pop(target)
        self.fireworks[value] += 1
        self.played_cards.add(card)
        self.score += 1
        self.draw(player)
        if card in self.critical_cards:
            self.critical_cards.remove(card)

        # A hint is obtained if the firework is completed
        if self.fireworks[value] == self.MAXRANK and self.num_hints < 8:
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
        self.num_discarded += 1

        num_discarded = self.discard_pile[card]
        num_left = self.CARDCOUNTS[card[1]] - num_discarded
        if num_left == 1:
            self.critical_cards.add(card)

        if num_left == 0:
            self.critical_cards.remove(card)
            self.dead_cards.add(card)

        return (DISCARD, card_index)

    def hint_any(self, player, value, hint_type):
        """Provide a hint to a player

        :param player: player to receive hint
        :param value: the colour or rank to hint
        :hint type: 0 indicates colour hint, 1 indicates rank hint
        """
        self.num_hints -= 1

        for index in self.player_hands[player]:
            card = self.deck[index]
            if card[hint_type] == value:
                self.player_hints[index][hint_type] = value

    def hint_colour(self, player, value):
        """Provide a colour hint to a player

        :param player: index of player receiving hint
        :param value: colour to hint
        """
        self.hint_any(player, value, 0)

    def hint_rank(self, player, value):
        """Provide a rank hint to a player

        :param player: index of player receiving hint
        :param value: rank to hint
        """
        self.hint_any(player, value, 1)

    @property
    def playable_cards(self):
        """Returns a set of all playable cards"""

        playable_cards = set()
        for colour, rank in enumerate(self.fireworks):
            if rank + 1 <= self.MAXRANK:
                playable_cards.add((colour, rank + 1))

        return playable_cards
