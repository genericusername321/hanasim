from hanasim import GameState, Move, PlayCard
import pytest

# Number of cards each player has in their hand
HANDSIZE = {2: 5,
            3: 5,
            4: 4,
            5: 4}

class TestGameState:

    def setup_method(self):
        self.nPlayers = 5
        self.handSize = 4
        self.seed = 0
        self.game = GameState(self.nPlayers, self.handSize, self.seed)
        self.game.setup()

    def teardown_method(self):
        del(self.game)

    @pytest.mark.parametrize("nPlayers", [2,3,4,5])
    def test_init(self, nPlayers):
        handSize = HANDSIZE[nPlayers]
        seed = 0

        game = GameState(nPlayers, handSize, seed)

        assert game.nPlayers == nPlayers
        assert game.handSize == handSize
        assert game.nHints == 8
        assert game.strikes == 0
        assert game.score == 0

    @pytest.mark.parametrize("nPlayers", [2,3,4,5])
    @pytest.mark.parametrize("handSize", [4,5])
    def test_setup(self, nPlayers, handSize, snapshot):
        seed = 0
        game = GameState(nPlayers, handSize, seed)
        game.setup()

        snapshot.assert_match(game.deck)
        assert (len(game.hands) == nPlayers)
        for i in range(nPlayers):
            assert (len(game.hands[i]) == handSize)

    @pytest.mark.parametrize("nPlayers", [1,6])
    def test_init_nPlayers(self, nPlayers):
        handSize = 4
        seed = 0

        with pytest.raises(AssertionError):
            game = GameState(nPlayers, handSize, seed)

    @pytest.mark.parametrize("handSize", [3,6])
    def test_init_handSize(self, handSize):
        nPlayers = 2
        seed = 0
        with pytest.raises(AssertionError):
            game = GameState(nPlayers, handSize, seed)

    def test_discard_fullhints(self, snapshot):

        game = self.game

        playerID = 0
        cardIndex = 0
        card = game.hands[playerID][cardIndex]
        game.discard(playerID, cardIndex)

        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])
        assert game.discarded[card] == 1
        assert game.nHints == 8

    def test_discard_addhint(self, snapshot):

        # Set number of hints to 0
        game = self.game
        game.nHints = 0

        playerID = 0
        cardIndex = 0
        card = game.hands[playerID][cardIndex]
        game.discard(playerID, cardIndex)

        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])
        assert game.nHints == 1
        assert game.discarded[card] == 1

    def test_force_discard(self, snapshot):

        # Set number of hints to 0
        game = self.game
        game.nHints = 0

        playerID = 0
        cardIndex = 0
        card = game.hands[playerID][cardIndex]
        game.forcedDiscard(playerID, cardIndex)
        
        assert game.nHints == 0
        assert game.discarded[card] == 1

    def test_play_fail(self, snapshot):

        # Set number of hints to 0
        game = self.game
        game.nHints = 0

        playerID = 0
        cardID = 3
        colour = 'R'
        card = game.hands[playerID][cardID]
        fireworks = game.fireworks[colour]
        
        game.playCard(playerID, cardID, colour)

        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])
        assert game.discarded[card] == 1
        assert game.strikes == 1
        assert game.nHints == 0
        assert game.score == 0
        assert fireworks.getTopCard() is None

    def test_play_succeed(self, snapshot):

        game = self.game
        game.nHints = 0

        playerID = 0
        cardID = 1
        colour = 'Y'
        fireworks = game.fireworks[colour]
        card = game.hands[playerID][cardID]
        
        game.playCard(playerID, cardID, colour) 

        nextCard = card
        nextCard.value += 1

        assert game.strikes == 0
        assert game.nHints == 0
        assert game.score == 1              
        assert fireworks.getNextCard() == nextCard
        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])

    def test_addhint(self):

        game = self.game
        game.addHint()
        assert game.nHints == 8
    
        game.nHints = 0
        game.addHint()
        assert game.nHints == 1

    def test_doMove_discard(self, snapshot):

        game = self.game
        game.nHints = 0

        playerID = 0
        moveType = 'DISCARD'
        index = 0
        move = Move(playerID, moveType, index)
        game.doMove(move)

        assert game.nHints == 1
        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])

    def test_doMove_play_success(self, snapshot):
        
        game = self.game
        game.nHints = 0

        moveType = 'PLAY'
        playerID = 0
        cardIndex = 1
        colour = 'Y'
        fireworks = game.fireworks[colour]
        card = game.hands[playerID][cardIndex]
        
        move = Move(playerID, moveType, PlayCard(cardIndex, colour))
        game.doMove(move)

        nextCard = card
        nextCard.value += 1

        assert game.strikes == 0
        assert game.nHints == 0
        assert game.score == 1              
        assert fireworks.getNextCard() == nextCard
        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])

    def test_doMove_play_fail(self, snapshot):

        game = self.game
        game.nHints = 0

        moveType = 'PLAY'
        playerID = 0
        cardIndex = 1
        colour = 'Y'
        card = game.hands[playerID][cardIndex]
        
        move = Move(playerID, moveType, PlayCard(cardIndex, colour))
        game.doMove(move)

        fireworks = game.fireworks[colour]
        assert fireworks.getNextCard() == nextCard
