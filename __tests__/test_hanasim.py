import pytest
import random
from hanasim import hanasim as hs
from unittest.mock import Mock, patch, call


@pytest.fixture()
def game():
    """Setup a game of 5-player hanabi with a pre-defined deck"""

    # Create deck with cards in known order
    deck = [hs.Card(colour, rank) for colour in hs.COLOURS for rank in hs.RANKS]
    for _ in range(50 - len(hs.COLOURS) * len(hs.RANKS)):
        deck.append(hs.Card(0, 1))

    num_players = 3
    game = hs.Board(num_players, deck)
    for i in range(num_players):
        game.set_player(Mock(), i)

    game.setup()
    return game


@pytest.mark.parametrize("num_players", [2, 3, 4, 5])
def test_init_random_deck(num_players):
    """Test that game initializes correctly for a random deck"""

    hand_size = {2: 5, 3: 5, 4: 4, 5: 4}

    game = hs.Board(num_players)
    for i in range(num_players):
        game.set_player(Mock(), i)
    game.setup()

    assert game.num_players == num_players
    assert game.bonus_turns == num_players
    assert game.num_hints == 8
    assert game.num_strikes == 0
    assert len(game.players) == num_players

    # Check that deck has been correctly dealt
    assert len(game.deck) == 50
    assert game.index == num_players * hand_size[num_players]
    for i in range(num_players):
        cards = game.deck[i * game.handsize : (i + 1) * game.handsize]
        calls = [call.draw(card) for card in cards]
        game.players[i].draw.assert_has_calls(calls)

    for colour in hs.COLOURS:
        assert hs.Card(colour, 5) in game.critical_cards


def test_draw_empty(game):
    """Test drawing a card from the deck with empty deck"""

    # Empty deck by setting index to end of deck
    game.index = 50
    for i in range(5):
        game.draw(0)
        assert game.index == 50
        assert game.bonus_turns == game.num_players - 1 - i
        game.players[0].assert_not_called()

    assert game.game_over


def test_play_success(game):
    """Test playing a card"""
    num_players = game.num_players
    game.num_hints = 0

    # Each player plays a card
    index = game.index
    for colour in range(num_players):
        for rank in hs.RANKS:
            card = game.deck[colour * len(hs.RANKS) + rank-1]
            game.players[colour].remove.return_value = card
            action = (hs.PLAY, 0, colour)
            game.resolve_move(colour, action)

            # Verify that card has been played
            assert game.fireworks[colour] == rank
            assert game.turn == colour * len(hs.RANKS) + rank
            game.players[colour].remove.assert_called()
            
            # Verify that new card has been drawn
            game.players[colour].draw.assert_called_with(game.deck[index])
            index += 1


    assert game.num_hints == 3


def test_play_fail(game):
    """Test that a strike is issued when playing an illegal card"""

    # Setup mock
    player_id = 0
    game.players[player_id].remove.return_value = hs.Card(0,2)

    # Play illegal card
    game.num_hints = 0
    action = (hs.PLAY, 1, 0)
    game.resolve_move(0, action)

    assert game.fireworks[0] == 0
    assert game.num_strikes == 1
    assert game.discard_pile[hs.Card(0, 2)] == 1
    assert game.num_hints == 0
    assert game.turn == 1


def test_discard(game):
    """Test discard method"""

    # Setup mock
    player_id = 0
    game.players[player_id].remove.return_value = hs.Card(0,1)

    # Discard a card
    game.num_hints = 0
    cur_index = game.index
    action = (hs.DISCARD, 0, None)
    game.resolve_move(0, action)

    assert game.num_hints == 1
    assert game.discard_pile[hs.Card(0, 1)] == 1
    assert game.index == cur_index + 1


def test_discard_maxhints(game):
    """Test that no hint is given at maximum number of hints"""

    # Setup mock discard behaviour
    player_id = 0
    game.players[player_id].remove.return_value = game.deck[0]

    action = (hs.DISCARD, 0, None)
    game.resolve_move(0, action)

    assert game.num_hints == 8
    assert game.discard_pile[(0, 1)] == 1
    assert game.turn == 1


def test_hint_colour(game):
    """Test hint_colour method"""

    action = (hs.HINTCOLOUR, 0, 0)
    game.resolve_move(1, action)

    assert game.num_hints == 7
    assert game.turn == 1
    game.players[0].receive_colour_hint.assert_called()

def test_hint_rank(game):
    """Test hint_rank method"""

    action = (hs.HINTRANK, 0, 1)
    game.resolve_move(1, action)

    assert game.num_hints == 7
    assert game.turn == 1
    game.players[0].receive_rank_hint.assert_called()


def test_critical_cards_discard(game):
    """Test critical_cards
    - Verify that cards are added to critical cards when only one copy
      remains
    """

    game.players[0].remove.return_value = hs.Card(0,2)
    action = (hs.DISCARD, 1, None)
    game.resolve_move(0, action)
    assert (0, 2) in game.critical_cards

    game.players[0].remove.return_value = hs.Card(0,5)
    action = (hs.DISCARD, 3, None)
    game.resolve_move(0, action)
    assert (0, 5) in game.dead_cards
    assert (0, 5) not in game.critical_cards

    for rank in hs.RANKS:
        game.players[1].remove.return_value = hs.Card(1, rank)
        action = (hs.PLAY, 0, 1)
        game.resolve_move(1, action)

    assert (1, 5) not in game.critical_cards


def test_dead_cards():
    """Test critical cards
    - Verify that cards are added to dead card set when smaller cards are dead
    """
    # Prepare deck
    deck = [
        hs.Card(colour, rank)
        for colour in hs.COLOURS
        for rank in hs.RANKS
        for _ in range(hs.CARDCOUNTS[hs.Card(colour, rank)])
    ]

    num_players = 3
    game = hs.Board(num_players, deck)
    for i in range(num_players):
        game.set_player(Mock(), i)
    game.setup()

    action = (hs.DISCARD, 0, 0)
    for _ in range(3):
        game.players[0].remove.return_value = hs.Card(0,1)
        game.resolve_move(0, action)

    for rank in hs.RANKS:
        assert hs.Card(0, rank) in game.dead_cards


def test_critical_cards_play(game):
    """Test critical_cards
    - Verify that cards are removed when played
    """

    for _ in hs.RANKS:
        game.players[0].remove.return_value = hs.Card(0,2)
        action = (hs.DISCARD, 0, 1)
        game.resolve_move(0, action)

    assert hs.Card(0, 5) not in game.critical_cards


def test_playable_cards(game):
    """Test playable_cards property"""

    for colour in hs.COLOURS:
        assert (colour, 1) in game.playable_cards

    game.players[0].remove.return_value = hs.Card(0,1)
    action = (hs.PLAY, 0, 0)
    game.resolve_move(0, action)
    assert (0, 2) in game.playable_cards
