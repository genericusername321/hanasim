from hanasim import GameState
import pytest

def test_init():

    nPlayers = 4
    seed = 0

    game = GameState(nPlayers, seed)

    assert game.nPlayers == nPlayers
    assert game.nHints == 8
    assert game.strikes == 0
    
def test_init_exception():

    nPlayersLow = 1
    seed = 0

    with pytest.raises(AssertionError):
        game = GameState(nPlayersLow, seed)
    
    nPlayersHigh = 6
    with pytest.raises(AssertionError):
        game = GameState(nPlayersHigh, seed)

def test_setup(snapshot):

    nPlayers = 4
    seed = 0

    game = GameState(nPlayers, seed)
    game.setup()

    snapshot.assert_match(game.deck)

def test_discard_fullhints(snapshot):

    nPlayers = 4
    seed = 0
    game = GameState(nPlayers, seed)
    game.setup()

    playerId = 0
    cardIndex = 0
    card = game.hands[playerId][cardIndex]
    game.discard(playerId, cardIndex)

    snapshot.assert_match(game.deck)
    snapshot.assert_match(game.hands[playerId])
    assert game.discarded[card] == 1
    assert game.nHints == 8

def test_discard_addhint(snapshot):

    nPlayers = 2
    seed = 0
    game = GameState(nPlayers, seed)
    game.setup()

    game.nHints = 0
    playerId = 0
    cardIndex = 0
    card = game.hands[playerId][cardIndex]
    game.discard(playerId, cardIndex)

    snapshot.assert_match(game.deck)
    snapshot.assert_match(game.hands[playerId])
    assert game.nHints == 1

def test_forced_discard(snapshot):
    nPlayers = 2
    seed = 0
    game = GameState(nPlayers, seed)
    game.setup()

    game.nHints = 0
    playerId = 0
    cardIndex = 0
    game.discard(playerId, cardIndex, False)

    assert game.nHints == 0

def test_play_fail(snapshot):

    nPlayers = 2
    seed = 0
    game = GameState(nPlayers, seed)
    game.setup()

    game.nHints = 0
    playerId = 0
    cardId = 3
    card = game.hands[playerId][cardId]
    pile = game.piles['R']
    game.playCard(playerId, cardId, pile)

    snapshot.assert_match(game.deck)    # Verify that card was drawn
    snapshot.assert_match(game.hands[playerId])
    assert game.discarded[card] == 1    # Verify that the discarded card was counted
    assert game.strikes == 1            # Verify that a strike has been counted
    assert game.nHints == 0             # Verify that no hint was awarded
    assert pile.getTopCard() == None    # Verify that card was not played

def test_play_succeed(snapshot):

    nPlayers = 2
    seed = 0
    game = GameState(nPlayers, seed)
    game.setup()

    game.nHints = 0
    playerId = 0
    cardId = 3
    card = game.hands[playerId][cardId]
    pile = game.piles['Y']
    game.playCard(playerId, cardId, pile)

    snapshot.assert_match(game.deck)
    nextCard = card
    nextCard.value += 1
    assert pile.getNextCard() == card
    assert nextCard == card




