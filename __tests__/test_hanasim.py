import pytest
import random
from ..hanasim import hanasim as hs


@pytest.fixture()
def setup():
    """Create a pre-defined deck where the cards are in known order"""

    deck = [hs.Card(colour, rank) for colour in hs.COLOURS for rank in hs.RANKS]

    for _ in range(50 - len(hs.COLOURS) * len(hs.RANKS)):
        deck.append(hs.Card(0, 1))

    yield deck


@pytest.mark.parametrize("num_players", [2, 3, 4, 5])
def test_init_random_deck(num_players):
    """Test that game initializes correctly for a random deck"""

    hand_size = {2: 5, 3: 5, 4: 4, 5: 4}

    game = hs.Board(num_players)
    game.generate_deck()
    game.deal()

    assert game.num_players == num_players
    assert game.bonus_turns == num_players
    assert game.num_hints == 8
    assert game.strikes == 0

    # Check that deck has been correctly dealt
    assert len(game.deck) == 50
    assert len(game.player_hands) == num_players
    assert game.index == num_players * hand_size[num_players]
    for i in range(num_players):
        assert len(game.player_hands[i]) == hand_size[num_players]


def test_init_deck(setup):
    """Test that game initializes correctly for a given deck"""

    my_deck = setup
    reference = my_deck[:]
    game = hs.Board(2, my_deck)
    assert game.deck == reference


def test_setup():
    """Test that setup method
    - generates a deck in case there is none
    - correctly finds critical cards
    - deals cards to players
    """

    game = hs.Board(5)
    assert game.deck is None

    game.setup()
    assert len(game.deck) == 50

    for colour in hs.COLOURS:
        assert (colour, 5) in game.critical_cards


def test_draw(setup):
    """Test drawing a card from the deck"""

    game = hs.Board(2, setup)
    game.draw(0)

    assert game.player_hands[0] == [0]
    assert game.index == 1


def test_draw_empty(setup):
    """Test drawing a card from the deck with empty deck"""

    game = hs.Board(2, setup)
    assert game.bonus_turns == 2

    game.index = 50
    game.draw(0)
    assert game.index == 50
    assert game.player_hands[0] == []
    assert game.bonus_turns == 1

    game.index = 50
    game.draw(0)
    assert game.index == 50
    assert game.player_hands[0] == []
    assert game.bonus_turns == 0
    assert game.game_over


def test_play_success(setup):
    """Test playing a card"""
    # Setup game
    game = hs.Board(3, setup)
    game.setup()
    game.num_hints = 4

    # Each player plays a card
    for rank in hs.RANKS:
        for colour in range(3):
            action = (hs.PLAY, 0, colour)
            game.resolve_move(colour, action)

            assert len(game.player_hands[colour]) == game.handsize
            assert game.fireworks[colour] == rank
            assert game.turn == (rank - 1) * 3 + colour + 1

    assert game.num_hints == 7


def test_play_fail(setup):
    """Test that a strike is issued when playing an illegal card"""

    game = hs.Board(5, setup)
    game.num_hints = 0
    game.deal()

    action = (hs.PLAY, 1, 0)
    game.resolve_move(0, action)

    assert game.fireworks[0] == 0
    assert game.strikes == 1
    assert game.player_hands[0] == [0, 2, 3, 20]
    assert game.discard_pile[(0, 2)] == 1
    assert game.num_hints == 0
    assert game.turn == 1


def test_discard(setup):
    """Test discard method"""

    game = hs.Board(5, setup)
    game.num_hints = 0
    game.deal()

    action = (hs.DISCARD, 0, None)
    game.resolve_move(0, action)

    assert game.num_hints == 1
    assert game.player_hands[0] == [1, 2, 3, 20]
    assert game.discard_pile[(0, 1)] == 1


def test_discard_maxhints(setup):
    """Test that no hint is given at maximum number of hints"""

    game = hs.Board(5, setup)
    game.setup()

    action = (hs.DISCARD, 0, None)
    game.resolve_move(0, action)

    assert game.num_hints == 8
    assert game.player_hands[0] == [1, 2, 3, 20]
    assert game.discard_pile[(0, 1)] == 1
    assert game.turn == 1


def test_hint_colour(setup):
    """Test hint_colour method"""

    game = hs.Board(5, setup)
    game.setup()

    action = (hs.HINTCOLOUR, 0, 0)
    game.resolve_move(1, action)

    assert game.num_hints == 7
    assert game.turn == 1
    for i in range(len(game.deck)):
        card = game.deck[i]
        if i in game.player_hands[0] and card[0] == 0:
            assert game.player_hints[i] == (0, None)
        else:
            assert game.player_hints[i] == (None, None)


def test_hint_rank(setup):
    """Test hint_rank method"""

    game = hs.Board(5, setup)
    game.setup()

    action = (hs.HINTRANK, 0, 1)
    game.resolve_move(1, action)

    assert game.num_hints == 7
    assert game.turn == 1
    for i in range(len(game.deck)):
        card = game.deck[i]
        if i in game.player_hands[0] and card[1] == 1:
            assert game.player_hints[i] == (None, 1)
        else:
            assert game.player_hints[i] == (None, None)


def test_critical_cards_discard(setup):
    """Test critical_cards
    - Verify that cards are added to critical cards when only one copy
      remains
    """

    game = hs.Board(3, setup)
    game.setup()

    action = (hs.DISCARD, 1, None)
    game.resolve_move(0, action)
    assert (0, 2) in game.critical_cards

    action = (hs.DISCARD, 1, None)
    game.resolve_move(1, action)
    assert hs.Card(1, 2) in game.critical_cards

    action = (hs.DISCARD, 3, None)
    game.resolve_move(0, action)
    assert (0, 5) in game.dead_cards
    assert (0, 5) not in game.critical_cards

    for _ in hs.RANKS:
        action = (hs.PLAY, 0, 1)
        game.resolve_move(1, action)

    assert (1, 5) not in game.critical_cards


def test_dead_cards(setup):
    """Test critical cards
    - Verify that cards are added to dead card set when smaller cards are dead
    """
    deck = [
        hs.Card(colour, rank)
        for colour in hs.COLOURS
        for rank in hs.RANKS
        for _ in range(hs.CARDCOUNTS[hs.Card(colour, rank)])
    ]
    game = hs.Board(3, deck)
    game.setup()

    action = (hs.DISCARD, 0, 0)
    for _ in range(3):
        game.resolve_move(0, action)

    for rank in hs.RANKS:
        assert hs.Card(0, rank) in game.dead_cards


def test_critical_cards_play(setup):
    """Test critical_cards
    - Verify that cards are removed when played
    """
    game = hs.Board(3, setup)
    game.setup()

    for _ in hs.RANKS:
        action = (hs.PLAY, 0, 1)
        game.resolve_move(0, action)

    assert hs.Card(0, 5) not in game.critical_cards


def test_playable_cards(setup):
    """Test that playable_cards property"""

    game = hs.Board(5, setup)
    game.setup()

    for colour in hs.COLOURS:
        assert (colour, 1) in game.playable_cards


def test_log(setup):
    """Test that log is generated correctly"""

    game = hs.Board(5)
    game.setup()

    game.save_log()
