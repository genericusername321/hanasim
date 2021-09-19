""" 
hanasim aims to be a fast hanabi engine to run simulations for player agents
that implement hanabi strategies.
"""


import json
import random
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import List, Tuple, Set

# Define player action types
ActionType = int
ACTION_TYPES = [PLAY, DISCARD, HINTCOLOUR, HINTRANK, ENDGAME] = range(5)
Action = Tuple[ActionType, int, int]

# Define card colours and ranks
COLOURS = [WHITE, YELLOW, GREEN, BLUE, RED] = range(5)
RANKS = [ONE, TWO, THREE, FOUR, FIVE] = range(1, 6)

# Map number of card in hand to number of players in game
HANDSIZE = {2: 5, 3: 5, 4: 4, 5: 4}

# Number of copies in deck for each card
Card = namedtuple("Card", ["colour", "rank"])
RANKCOUNTS = {ONE: 3, TWO: 2, THREE: 2, FOUR: 2, FIVE: 1}
CARDCOUNTS = {
    Card(colour, rank): RANKCOUNTS[rank] for colour in COLOURS for rank in RANKS
}


class AbstractAgent(ABC):
    """
    AbstractAgent is an abstract class defining the interface a player agent
    for the hanasim class must implement.
    """

    @abstractmethod
    def draw(self, card: Card):
        """draw a card from the deck and add it to the end of the hand"""

    @abstractmethod
    def remove(self, index: int) -> Card:
        """remove a card from the hand. The card may be discarded or played"""

    @abstractmethod
    def receive_colour_hint(self, colour: int):
        """receive a colour hint"""

    @abstractmethod
    def receive_rank_hint(self, rank: int):
        """receive a rank hint"""


class Board:
    """
    The board represents the Hanabi game state. The game state initializes empty,
    and should be initialized for before the game start.
    """

    MAXHINTS = 8
    MAXSTRIKES = 3
    NUMCARDS = 50

    def __init__(self, num_players: int, deck: List[Card] = None) -> None:
        """Constructor for the Board class"""

        self.game_over = False

        # global game state
        self.players = [0] * num_players
        self.num_players = num_players
        self.handsize = HANDSIZE[self.num_players]
        self.bonus_turns = num_players

        # initialize game state data
        self.num_hints = self.MAXHINTS
        self.num_strikes = 0
        self.score = 0
        self.turn = 0
        self.index = 0
        self.deck = deck
        self.fireworks = [0] * len(COLOURS)
        self.discard_pile = {
            Card(colour, rank): 0 for colour in COLOURS for rank in RANKS
        }

        # data for faster bookkeeping
        self.action_history = []
        self.played_cards = set()
        self.dead_cards = set()
        self.critical_cards = set()
        self.total_discarded = 0

    def set_player(self, player: AbstractAgent, player_id: int) -> None:
        """Assign a player to the player list"""
        self.players[player_id] = player

    def setup(self) -> None:
        """Generate deck and deal cards"""

        if not self.deck:
            self.generate_deck()

        # Find all critical cards
        self.critical_cards = {card for card in self.deck if CARDCOUNTS[card] == 1}

        # Deal cards to players
        self.deal()

    def generate_deck(self) -> None:
        """Generate a shuffled deck of Hanabi cards"""

        deck = [
            Card(colour, rank)
            for colour in COLOURS
            for rank in RANKS
            for _ in range(RANKCOUNTS[rank])
        ]
        random.shuffle(deck)
        self.deck = deck

    def deal(self) -> None:
        """Deal cards from deck into player hands at start of game"""

        for j in range(self.num_players):
            for _ in range(self.handsize):
                self.draw(j)

    def draw(self, player_id: int) -> None:
        """Draw a card for player"""

        if self.index == len(self.deck):
            self.bonus_turns -= 1
            if self.bonus_turns == 0:
                self.game_over = True
                self.action_history.append((ENDGAME, player_id, 1))
            return

        card = self.deck[self.index]
        self.players[player_id].draw(card)
        self.index += 1

    def resolve_move(self, player: int, action_attempt: Action) -> Action:
        """Play out one move by a given player"""

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
            action = (HINTCOLOUR, target, value)

        elif action_type == HINTRANK:
            assert player != target
            assert self.num_hints > 0
            self.hint_rank(target, value)
            action = (HINTRANK, value)

        else:
            raise ValueError("Invalid action type")

        self.action_history.append(action)
        if self.num_strikes == self.MAXSTRIKES:
            self.action_history.append((ENDGAME, player, 2))
            self.game_over = True

        self.turn += 1

    def play(self, player_id: int, target: int, colour: int) -> Action:
        """Resolve a move where player_id plays a card from its hand."""

        # Remove card from player's hand
        card = self.players[player_id].remove(target)
        self.draw(player_id)
        action = (PLAY, card, colour)

        # If card is illegal, discard with strike
        if card.colour != colour or card.rank != self.fireworks[colour] + 1:
            self.num_strikes += 1
            self.discard_pile[card] += 1
            return action

        # Play the card
        self.fireworks[colour] += 1
        self.played_cards.add(card)
        self.score += 1

        if self.score == 25:
            self.game_over = True

        # If the played card was critical, remove it from the critical card stack
        if card in self.critical_cards:
            self.critical_cards.remove(card)

        # A hint is obtained if the firework is completed
        if self.fireworks[colour] == FIVE and self.num_hints < self.MAXHINTS:
            self.num_hints += 1

        return action

    def discard(self, player_id: int, target: int) -> Action:
        """Discard a card"""

        # remove card from player hand and draw new card
        card = self.players[player_id].remove(target)
        self.draw(player_id)

        # move card onto discard pile
        self.discard_pile[card] += 1
        self.total_discarded += 1

        # account for critical and dead cards after discount
        num_discarded = self.discard_pile[card]
        num_left = CARDCOUNTS[card] - num_discarded
        if num_left == 1:
            self.critical_cards.add(card)

        if num_left == 0:
            colour, rank = card
            for r in range(rank, RANKS[-1] + 1):
                self.critical_cards.discard(Card(colour, r))
                self.dead_cards.add(Card(colour, r))

        return (DISCARD, card, 0)

    def hint_colour(self, player_id: int, value: int) -> None:
        """Provide a colour hint to a player"""

        self.num_hints -= 1
        self.players[player_id].receive_colour_hint(value)

    def hint_rank(self, player_id: int, value: int) -> None:
        """Provide a rank hint to a player

        :param player: index of player receiving hint
        :param value: rank to hint
        """

        self.num_hints -= 1
        self.players[player_id].receive_rank_hint(value)

    @property
    def playable_cards(self) -> Set[namedtuple]:
        """Returns a set of all playable cards"""

        playable_cards = set()
        for colour, rank in enumerate(self.fireworks):
            if rank + 1 <= FIVE:
                playable_cards.add((colour, rank + 1))

        return playable_cards
