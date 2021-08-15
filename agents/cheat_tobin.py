import hanasim.hanasim as hs

class Agent:
    """
    Cheating Hanasim player that applies the following strategy:
        1. Play card with lowest value
        2. Discard dead card, conditional on pace
        3. Hint
        4. Discard dead card
        5. Discard duplicate
        6. Discard non-critical
        7. Discard first

    This player cheats by inspecting its own hand.
    """

    def __init__(self, playerID, game):
        self.playerID = playerID
        self.game = game

    def findMove(self):
        """
        Computes move according to given priorities
        """

        myHand = self.game.hands[self.playerID]

        # 1. Attempt to play smallest card
        legalCards = self.game.getPlayableCards()
        playableCards = [card for card in myHand if card in legalCards]
        if playableCards:
            bestCard = min(playableCards)
            bestIndex = myHand.index(bestCard)
            move = hs.Move(self.playerID, 'PLAY', hs.PlayCard(bestIndex, bestCard.colour))
            return move

        # 2. Attempt to discard dead card, conditional on pace
        discardThreshold = self.game.TOTALCARDS - len(hs.COLOURS) * len(hs.VALUES) - \
                           self.game.handSize * self.game.nPlayers

        deadCard = self.findDeadCard()
        if self.game.discardPile.total < discardThreshold and \
                self.game.nHints < self.game.MAXHINTS:

            if deadCard:
                move = hs.Move(self.playerID, 'DISCARD', deadCard)
                return move

        # 3. Give a hint
        if self.game.nHints > 0:
            hint = hs.Hint(self.getNextPlayer(), 1)
            move = hs.Move(self.playerID, 'HINT', hint)
            return move

        # 4. Discard dead card
        if deadCard:
            return hs.Move(self.playerID, 'DISCARD', deadCard)

        # 5. Discard duplicate
        otherCards = self.getOtherHands()
        duplicateCounts = {card : otherCards.count(card) for card in myHand}
        card = max(duplicateCounts)
        if duplicateCounts[card] > 0:
            return hs.Move(self.playerID, 'DISCARD', myHand.index(card))

        # 6. Discard non-critical
        criticalCards = self.game.getCriticalCards()
        for (index, card) in enumerate(myHand):
            if card not in criticalCards:
                return hs.Move(self.playerID, 'DISCARD', index)

        # 7. Discard first
        return hs.Move(self.playerID, 'DISCARD', 0)


    def findDeadCard(self):
        deadCards = self.game.getUsedCards()
        for index, card in enumerate(self.game.hands[self.playerID]):
            if card in deadCards:
                return index

        return None

    def getOtherHands(self):
        otherCards = []
        for i in range(self.game.nPlayers):
            if i != self.playerID:
                otherCards += self.game.hands[i]

        return otherCards

    def getNextPlayer(self):
        return (self.playerID + 1) % self.game.nPlayers

    def throwAwayHint(self):
        hint = hs.Hint(self.getNextPlayer(), 1)
