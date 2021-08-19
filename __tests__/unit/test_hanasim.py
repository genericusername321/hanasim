import pytest
import random
import hanasim.hanasim as hs


@pytest.fixture()
def setup():
    """Create a pre-defined deck where the cards are in known order"""

    deck = [
        (colour, rank)
        for rank in range(1, hs.Board.MAXRANK + 1)
        for colour in range(hs.Board.MAXCOLOUR + 1)
    ]

    for _ in range(hs.Board.NUMCARDS - (hs.Board.MAXCOLOUR + 1) * hs.Board.MAXRANK):
        deck.append((0, 1))

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
    assert len(game.deck) == game.NUMCARDS
    assert len(game.player_hands) == num_players
    assert len(game.player_hints) == game.NUMCARDS
    assert game.index == num_players * hand_size[num_players]
    for i in range(num_players):
        assert len(game.player_hands[i]) == hand_size[num_players]


def test_init_deck(setup):
    """Test that game initializes correctly for a given deck"""

    my_deck = setup
    reference = my_deck[:]
    game = hs.Board(2, my_deck)
    assert game.deck == reference


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
    game = hs.Board(5, setup)
    game.deal()
    game.num_hints = 4

    # Each player plays a card
    for rank in range(1, hs.Board.MAXRANK + 1):
        for colour in range(hs.Board.MAXCOLOUR + 1):
            action = (hs.PLAY, 0, colour)
            game.resolve_move(colour, action)

            assert len(game.player_hands[colour]) == 4
            assert game.fireworks[colour][1] == rank
            assert game.turn == (rank - 1) * (hs.Board.MAXCOLOUR + 1) + colour + 1

    assert game.num_hints == 8


def test_play_fail(setup):
    """Test that a strike is issued when playing an illegal card"""

    game = hs.Board(5, setup)
    game.num_hints = 0
    game.deal()

    action = (hs.PLAY, 1, 0)
    game.resolve_move(0, action)

    assert game.fireworks[0] == [0, 0]
    assert game.strikes == 1
    assert game.player_hands[0] == [0, 10, 15, 20]
    assert game.discard_pile[(0, 2)] == 1
    assert game.num_hints == 0


def test_discard(setup):
    """Test discard method"""

    game = hs.Board(5, setup)
    game.num_hints = 0
    game.deal()

    action = (hs.DISCARD, 0, None)
    game.resolve_move(0, action)

    assert game.num_hints == 1
    assert game.player_hands[0] == [5, 10, 15, 20]
    assert game.discard_pile[(0, 1)] == 1


def test_discard_maxhints(setup):
    """Test that no hint is given at maximum number of hints"""

    game = hs.Board(5, setup)
    game.deal()

    action = (hs.DISCARD, 0, None)
    game.resolve_move(0, action)

    assert game.num_hints == 8
    assert game.player_hands[0] == [5, 10, 15, 20]
    assert game.discard_pile[(0, 1)] == 1

def test_hint_colour(setup):
    """Test hint_colour method"""

    game = hs.Board(5, setup)
    game.deal()

    action = (hs.HINTCOLOUR, 0, 0)
    game.resolve_move(1, action)

    assert game.num_hints == 7
    for i in range(game.NUMCARDS):
        card = game.deck[i]
        if i in game.player_hands[0] and card[0] == 0:
            assert game.player_hints[i] == [0, None]
        else:
            assert game.player_hints[i] == [None, None]

def test_hint_rank(setup):
    """Test hint_rank method"""

    game = hs.Board(5, setup)
    game.deal()
    
    action = (hs.HINTRANK, 0, 1)
    game.resolve_move(1, action)

    assert game.num_hints == 7
    for i in range(game.NUMCARDS):
        card = game.deck[i]
        if i in game.player_hands[0] and card[1] == 1:
            assert game.player_hints[i] == [None, 1]
        else:
            assert game.player_hints[i] == [None, None]
    
