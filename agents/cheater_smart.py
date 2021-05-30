import hanasim.hanasim as hs

class Agent:
    """
    This agent finds a move by inspecting its own hand to find a card
    that can be played, eliminating the need to be hinted. As
    such it also does not hint other players. It performs actions
    with the following priority:
        1. Play card with lowest value
        2. Discard dead card
        3. Discard duplicate
        4. Discard dispensable card with highest value
        5. Hint another player
        6. Discard indispensable card that leaves maximum attainable score after discard
    """

    def __init__(self, playerID, game):
        self.playerID = playerID
        self.game = game

    def findMove(self):
        """
        Computes move according to priorities set in class description

        :return: hanasim.Move type object encoding the selected move
        """

        # Cheat by accessing our own hand
        hand = self.game.hands[self.playerID]

        # 1. Attempt to play a card if any card can be played
        playableCards = [self.game.fireworks[colour].getNextCard() for colour in hs.COLOURS]
        playableHand = [card for card in hand if card in playableCards]
        if playableHand:
            minCard = min(playableHand)
            cardIndex = hand.index(minCard)
            move = hs.Move(self.playerID, 'PLAY', hs.PlayCard(cardIndex, minCard.colour))
            return move

        # 3. Give a hint
        if self.game.nHints == 8:
            hint = hs.Hint(self.getNextPlayer(), 1)
            move = hs.Move(self.playerID, 'HINT', hint)
            return move


        # 2. Discard dead or played card, if there are pace is sufficiently high
        if self.game.discardPile.total < 5:
            deadCards = self.game.discardPile.deadCards
            playedCards = self.game.playedCards
            for index, card in enumerate(hand):
                if card in deadCards or card in playedCards:
                    move = hs.Move(self.playerID, 'DISCARD', index)
                    return move

        # 3. Give a hint
        if self.game.nHints > 0:
            hint = hs.Hint(self.getNextPlayer(), 1)
            move = hs.Move(self.playerID, 'HINT', hint)
            return move

        # 4. Discard dead or played card
        deadCards = self.game.discardPile.deadCards
        playedCards = self.game.playedCards
        for index, card in enumerate(hand):
            if card in deadCards or card in playedCards:
                move = hs.Move(self.playerID, 'DISCARD', index)
                return move

        # 5. Discard duplicate card
        otherPlayerHands = set()
        for i in range(self.game.nPlayers):
            if i != self.playerID:
                otherPlayerHands.union(set(self.game.hands[i]))

        for index, card in enumerate(hand):
            if card in otherPlayerHands:
                move = hs.Move(self.playerID, 'DISCARD', index)
                return move

        # 6. Discard first dispensable card
        criticalCards = self.game.discardPile.getCriticalCards()
        dispensableCards = [card for card in hand if card not in criticalCards]
        if dispensableCards:
            move = hs.Move(self.playerID, 'DISCARD', hand.index(dispensableCards[0]))
            return move

        # 7. Discard first card
        move = hs.Move(self.playerID, 'DISCARD', 0)
        return move

    def findDiscard(self):
        """
        Computes optimal card to discard from hand

        :return: index of card to discard
        """

        hand = self.game.hands[self.playerID]
        discardPile = self.game.discardPile

        # Compute scores
        scores = [self.computeMaxAfterDiscard(discardPile, card) for card in hand]

        # Find index of max score
        return scores.index(max(scores))

    def getNextPlayer(self):
        """
        Get player whose turn is after this player
        """

        return (self.playerID + 1) % self.game.nPlayers

    @staticmethod
    def computeMaxAfterDiscard(discardPile, card):
        """
        Computes max score after discarding card
        """

        discardPile.discard(card)
        maxScore = discardPile.getMaxScore()
        discardPile.remove(card)
        return maxScore
