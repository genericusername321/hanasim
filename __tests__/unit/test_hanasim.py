import hanasim.hanasim as hs
import agents.cheater_discard_first as agent
import pytest
import logging

# Number of cards each player has in their hand
HANDSIZE = {2: 5,
            3: 5,
            4: 4,
            5: 4}

class TestGameState:

    def setup_method(self):

        # Configure logger
        self.nPlayers = 5
        self.handSize = 4
        self.seed = 0
        self.game = hs.GameState(self.nPlayers, self.handSize, self.seed, deck=None)
        self.game.setup()

    def teardown_method(self):
        del self.game

    @pytest.mark.parametrize("nPlayers", [2, 3, 4, 5])
    def test_init(self, nPlayers):
        """
        Test that game initializes successfully
        @param nPlayers: Number of players in the game
        @return: None
        """
        handSize = HANDSIZE[nPlayers]
        seed = 0

        game = hs.GameState(nPlayers, handSize, seed)

        assert game.nPlayers == nPlayers
        assert game.handSize == handSize
        assert game.nHints == 8
        assert game.strikes == 0
        assert game.score == 0

    @pytest.mark.parametrize("nPlayers", [1, 6])
    @pytest.mark.parametrize("handSize", [3, 6])
    def test_init_fail(self, nPlayers, handSize):
        """
        Verify that game setup raises exception for invalid inputs of
        number of players or hand sizes
        @param nPlayers: Number of players in game
        @param handSize: Number of cards per player hand
        @return:
        """
        with pytest.raises(AssertionError):
            hs.GameState(nPlayers, handSize)

    @pytest.mark.parametrize("nPlayers", [2, 3, 4, 5])
    @pytest.mark.parametrize("handSize", [4, 5])
    def test_setup(self, nPlayers, handSize, snapshot):
        seed = 0
        game = hs.GameState(nPlayers, handSize, seed)
        game.setup()

        snapshot.assert_match(game.deck)
        assert (len(game.hands) == nPlayers)
        for i in range(nPlayers):
            assert (len(game.hands[i]) == handSize)

    def test_discard_fullhints(self, snapshot):

        game = self.game
        playerID = 0
        cardIndex = 0
        card = game.hands[playerID][cardIndex]
        game.discard(playerID, cardIndex)

        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])
        assert game.discardPile.cardCounts[card] == 1
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
        assert game.discardPile.cardCounts[card] == 1

    def test_force_discard(self):

        # Set number of hints to 0
        game = self.game
        game.nHints = 0

        playerID = 0
        cardIndex = 0
        card = game.hands[playerID][cardIndex]
        game.forcedDiscard(playerID, cardIndex)

        assert game.nHints == 0
        assert game.discardPile.cardCounts[card] == 1

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
        assert game.discardPile.cardCounts[card] == 1
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

        nextCard = hs.Card(card.colour, card.value+1)

        assert game.strikes == 0
        assert game.nHints == 0
        assert game.score == 1
        assert fireworks.getNextCard() == nextCard
        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])

        print(game.playedCards)

        assert game.playedCards == {hs.Card('Y', 1)}

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
        move = hs.Move(playerID, moveType, index)
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

        move = hs.Move(playerID, moveType, hs.PlayCard(cardIndex, colour))
        game.doMove(move)

        nextCard = card
        nextCard.value += 1

        assert game.strikes == 0
        assert game.nHints == 0
        assert game.score == 1
        assert fireworks.getNextCard() == nextCard
        snapshot.assert_match(game.deck)
        snapshot.assert_match(game.hands[playerID])
        snapshot.assert_match(game.playedCards)

    def test_doMove_play_fail(self):

        game = self.game
        game.nHints = 0

        moveType = 'PLAY'
        playerID = 0
        cardIndex = 1
        colour = 'Y'
        card = game.hands[playerID][cardIndex]

        move = hs.Move(playerID, moveType, hs.PlayCard(cardIndex, colour))
        game.doMove(move)

        nextCard = card
        nextCard.value += 1

        fireworks = game.fireworks[colour]
        assert fireworks.getNextCard() == nextCard

    def test_doMove_hint(self):

        game = self.game
        assert game.nHints == game.MAXHINTS

        hint = hs.Hint(1, 1)
        move = hs.Move(0, 'HINT', hint)
        game.doMove(move)

        assert game.nHints == game.MAXHINTS - 1

    def test_doMove_hint_fail(self):

        game = self.game
        game.nHints = 0

        hint = hs.Hint(1, 1)
        move = hs.Move(0, 'HINT', hint)

        with pytest.raises(Exception):
            game.doMove(move)

    def test_getHands(self):

        game = self.game

        requestPlayerID = 0
        targetPlayerID = 1

        hand = game.getPlayerHand(requestPlayerID, targetPlayerID)
        assert hand == game.hands[targetPlayerID]

        with pytest.raises(ValueError):
            game.getPlayerHand(0, 0)

    def test_reset(self):

        game = self.game

        # Play a game
        players = [agent.Agent(playerID, game) for playerID in range(game.nPlayers)]

        ply = 0
        while not game.isOver:
            turn = ply % game.nPlayers
            ply = ply + 1
            move = players[turn].findMove()
            game.doMove(move)

        print("The final score is: {}".format(game.score))

        game.reset()

        # Verify that game is in original state
        assert game.isOver is False
        assert game.nHints == 8
        assert game.strikes == 0
        assert game.turn == 0
        assert game.playerTurn == 0
        assert game.turnAfterEmpty == game.nPlayers
        assert not game.deck
        assert not game.moveHistory

        for hand in game.hands:
            assert not hand

        for card in game.discardPile.cardCounts:
            assert game.discardPile.cardCounts[card] == 0

    def test_getMaxScore(self):

        game = self.game
        assert game.getMaxScore() == 25

        game.discard(0, 1)
        game.discard(1, 1)
        game.discard(4, 1)

        assert game.getMaxScore() == 20

    def test_getPlayableCards(self, snapshot):

        playableCards = self.game.getPlayableCards()
        snapshot.assert_match(playableCards)

    def test_computePace(self):

        game = self.game
        pace = game.computePace()

        assert pace == 10

        # Discard something
        game.doMove(hs.Move(0, 'DISCARD', 0))
        pace = game.computePace()
        assert pace == 9

