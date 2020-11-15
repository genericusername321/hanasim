from hanasim import GameState
import pytest

# Number of cards each player has in their hand
HANDSIZE = {2: 5,
            3: 5,
            4: 4,
            5: 4}

def test_init():

    nPlayers = 4
    handSize = 2
    seed = 0

    game = GameState(nPlayers, handSize, seed)

    assert game.nPlayers == nPlayers
    assert game.handSize == handSize
    assert game.nHints == 8
    assert game.strikes == 0
    assert game.score == 0
    
def test_init_exception():
    
    nPlayers = 3
    nPlayersLow = 1
    nPlayersHigh = 6
    handSize = 4
    handSizeLow = 0 
    handSizeType = 'l'
    seed = 0

    with pytest.raises(AssertionError):
        game = GameState(nPlayersLow, handSize, seed)
    
    with pytest.raises(AssertionError):
        game = GameState(nPlayersHigh, handSize, seed)

    with pytest.raises(AssertionError):
        game = GameState(nPlayers, handSizeLow, seed)

    with pytest.raises(AssertionError):
        game = GameState(nPlayers, handSizeType)


def test_setup(snapshot):

    nPlayers = 4
    handSize = 4
    seed = 0

    game = GameState(nPlayers, handSize, seed)
    game.setup()

    snapshot.assert_match(game.deck)
    assert len(game.hands) == nPlayers
    assert len(game.hands[0]) == handSize

def test_discard_fullhints(snapshot):

    nPlayers = 4
    handSize = 4
    seed = 0
    game = GameState(nPlayers, handSize, seed)
    game.setup()

    playerID = 0
    cardIndex = 0
    card = game.hands[playerID][cardIndex]
    game.discard(playerID, cardIndex)

    snapshot.assert_match(game.deck)
    snapshot.assert_match(game.hands[playerID])
    assert game.discarded[card] == 1
    assert game.nHints == 8

def test_discard_addhint(snapshot):

    nPlayers = 2
    handSize = 5
    seed = 0
    game = GameState(nPlayers, handSize, seed)
    game.setup()

    game.nHints = 0
    playerID = 0
    cardIndex = 0
    card = game.hands[playerID][cardIndex]
    game.discard(playerID, cardIndex)

    snapshot.assert_match(game.deck)
    snapshot.assert_match(game.hands[playerID])
    assert game.nHints == 1

def test_forced_discard(snapshot):
    nPlayers = 2
    handSize = 5
    seed = 0
    game = GameState(nPlayers, handSize, seed)
    game.setup()

    game.nHints = 0
    playerID = 0
    cardIndex = 0
    game.forcedDiscard(playerID, cardIndex)

    assert game.nHints == 0

def test_play_fail(snapshot):

    nPlayers = 2
    handSize = 5
    seed = 0
    game = GameState(nPlayers, handSize, seed)
    game.setup()

    game.nHints = 0
    playerID = 0
    cardID = 3
    card = game.hands[playerID][cardID]
    pile = game.piles['R']
    game.playCard(playerID, cardID, pile)

    snapshot.assert_match(game.deck)    # Verify that card was drawn
    assert len(game.hands[playerID]) == handSize
    snapshot.assert_match(game.hands[playerID])
    assert game.discarded[card] == 1    # Verify that the discarded card was counted
    assert game.strikes == 1            # Verify that a strike has been counted
    assert game.nHints == 0             # Verify that no hint was awarded
    assert game.score == 0              # Verify that no score was counted
    assert pile.getTopCard() is None    # Verify that card was not played
    assert len(game.hands[0]) == 5

def test_play_succeed(snapshot):

    nPlayers = 2
    handSize = 5
    seed = 0
    game = GameState(nPlayers, handSize, seed)
    game.setup()

    game.nHints = 0
    playerID = 0
    cardID = 3
    card = game.hands[playerID][cardID]
    pile = game.piles['Y']
    game.playCard(playerID, cardID, pile)

    nextCard = card
    nextCard.value += 1

    assert game.score == 1              # Verify that score was counted
    assert pile.getNextCard() == nextCard
    assert len(game.hands[0]) == 5
    snapshot.assert_match(game.deck)
    snapshot.assert_match(game.hands[playerID])


