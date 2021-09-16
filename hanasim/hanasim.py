""" hanasim

hanasim aims to be a fast hanabi engine to run simulations for player agents
that implement hanabi strategies.
"""

import json
import random
from typing import List, Tuple, Set
from collections import namedtuple

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
RANKCOUNTS = {ONE: 3, TWO: 2, THREE: 2, FOUR: 2, FIVE: 1}
CARDCOUNTS = {(colour, rank): RANKCOUNTS[rank] for colour in COLOURS for rank in RANKS}

Card = namedtuple("Card", ["colour", "rank"])
Hint = namedtuple("Hint", ["colour", "rank"])


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

        # game constants
        self.num_hints = self.MAXHINTS
        self.num_strikes = 0
        self.num_players = num_players
        self.handsize = HANDSIZE[self.num_players]
        self.bonus_turns = num_players
        self.num_cards = 0

        # initialize game state data
        self.strikes = 0
        self.score = 0
        self.turn = 0
        self.index = 0
        self.deck = deck
        self.fireworks = [0 for _ in COLOURS]
        self.discard_pile = {
            Card(colour, rank): 0 for colour in COLOURS for rank in RANKS
        }

        # initialize player hands and hint data
        self.player_hands = [[] for _ in range(self.num_players)]
        self.player_hints = []

        # data for faster bookkeeping
        self.action_history = []
        self.played_cards = set()
        self.dead_cards = set()
        self.critical_cards = set()
        self.num_discarded = 0

    def setup(self) -> None:
        """Generate deck and deal cards"""

        if not self.deck:
            self.generate_deck()
        card_deck = [self.deck[i] for i in range(len(self.deck))]

        # Find all critical cards
        self.critical_cards = {card for card in card_deck if CARDCOUNTS[card] == 1}

        # Create card hints
        self.player_hints = [(None, None) for _ in range(len(self.deck))]

        self.deal()

    def generate_deck(self) -> None:
        """Generate a shuffled deck of Hanabi cards"""

        deck = [
            Card(colour, rank)
            for colour in COLOURS
            for rank in RANKS
            for _ in range(CARDCOUNTS[(colour, rank)])
        ]
        random.shuffle(deck)
        self.deck = deck

    def deal(self) -> None:
        """Deal cards from deck into player hands at start of game"""

        for j in range(self.num_players):
            for _ in range(self.handsize):
                self.draw(j)

    def draw(self, player: int) -> None:
        """Draw a card for player"""

        if self.index == len(self.deck):
            self.bonus_turns -= 1
            if self.bonus_turns == 0:
                self.game_over = True
                self.action_history.append((ENDGAME, player, 1))
            return

        self.player_hands[player].append(self.index)
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

    def play(self, player: int, target: int, colour: int) -> Action:
        """Play a card"""

        card_index = self.player_hands[player][target]
        card = self.deck[card_index]
        action = (PLAY, card_index, 0)

        # If card is illegal, discard with strike
        if card.colour != colour or card.rank != self.fireworks[colour] + 1:
            # Discard the card without hint
            self.discard(player, target)
            self.strikes += 1
            return action

        # Play the card
        self.player_hands[player].pop(target)
        self.fireworks[colour] += 1
        self.played_cards.add(card)
        self.score += 1
        self.draw(player)
        if card in self.critical_cards:
            self.critical_cards.remove(card)

        # A hint is obtained if the firework is completed
        if self.fireworks[colour] == FIVE and self.num_hints < 8:
            self.num_hints += 1

        if self.score == 25:
            self.game_over = True

        return action

    def discard(self, player: int, target: int) -> Action:
        """Discard a card"""

        # remove card from hand
        card_index = self.player_hands[player][target]
        self.player_hands[player].pop(target)

        # move card onto discard pile
        card = self.deck[card_index]
        self.discard_pile[card] += 1
        self.draw(player)
        self.num_discarded += 1

        num_discarded = self.discard_pile[card]
        num_left = CARDCOUNTS[card] - num_discarded
        if num_left == 1:
            self.critical_cards.add(card)

        if num_left == 0:
            colour, rank = card
            for r in range(rank, RANKS[-1]+1):
                self.critical_cards.discard(Card(colour, r))
                self.dead_cards.add(Card(colour, r))

        return (DISCARD, card_index, 0)

    def hint_colour(self, player: int, value: int) -> None:
        """Provide a colour hint to a player"""

        self.num_hints -= 1
        for index in self.player_hands[player]:
            card = self.deck[index]
            if card.colour == value:
                _, rank = self.player_hints[index]
                self.player_hints[index] = Hint(value, rank)

    def hint_rank(self, player: int, value: int) -> None:
        """Provide a rank hint to a player

        :param player: index of player receiving hint
        :param value: rank to hint
        """

        self.num_hints -= 1
        for index in self.player_hands[player]:
            card = self.deck[index]
            if card.rank == value:
                colour, _ = self.player_hints[index]
                self.player_hints[index] = Hint(colour, value)

    @property
    def playable_cards(self) -> Set[namedtuple]:
        """Returns a set of all playable cards"""

        playable_cards = set()
        for colour, rank in enumerate(self.fireworks):
            if rank + 1 <= FIVE:
                playable_cards.add((colour, rank + 1))

        return playable_cards

    def save_log(self) -> None:
        """Save the game to a JSON file that can be visualized on hanab.live.
        Example of the JSON file format can be found on:
        https://raw.githubusercontent.com/Zamiell/hanabi-live/master/misc/example_game_with_comments.jsonc
        """

        log = dict()
        log["players"] = list()
        for player_id in range(self.num_players):
            log["players"].append("player" + str(player_id))

        log["deck"] = list()
        for card in self.deck:
            log["deck"].append({"suitIndex": card.colour, "rank": card.rank})

        log["actions"] = list()
        for actions in self.action_history:
            log["actions"].append(
                {"type": actions[0], "target": actions[1], "value": actions[2]}
            )

        log["options"] = {"emptyClues": True}

        with open("log.json", "w") as outfile:
            outfile.write(json.dumps(log, indent=4))
