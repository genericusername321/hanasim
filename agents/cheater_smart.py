import hanasim.hanasim as hs
from collections import Counter

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
        self.hand = self.game.hands[playerID]

    def getOtherHands(self):

        otherHands = [(index, hand) for (index, hand) in enumerate(self.game.hands) if index != self.playerID]
        return otherHands

    def throwAwayHint(self):
        """
        Create a throwaway hint
        """

        hint = hs.Hint(self.getNextPlayer(), 1)
        move = hs.Move(self.playerID, 'HINT', hint)
        return move

    def computeCardScore(self, card):
        """
        Assign a given card a play priority based on the board
        """

        if self.game.isUseless(card):
            return 0
        elif self.game.isCritical(card):
            return 10 - card.value
        else:
            return 1

    def computeHandScore(self, hand):
        """
        Compute sum of scores of all cards in hand
        """

        scores = [self.computeCardScore(card) for card in hand]
        return sum(scores)

    def computeCardPlayScore(self, card):

        otherHands = self.getOtherHands()

        myHandValue = self.computeHandScore(self.hand)

        for playerID, hand in otherHands:
            if self.game.hasCard(playerID, card):
                otherHandValue = self.computeHandScore(hand)
                if otherHandValue < myHandValue:
                    return 10 - card.value

        else:
            return 20 - card.value

    def findMove(self):
        """
        Computes move according to priorities set in class description

        :return: Move type object encoding the selected move
        """

        # 1. Attempt to play a card if any card can be played
        playableCards = [self.game.fireworks[colour].getNextCard() for colour in hs.COLOURS]
        playableHand = [card for card in self.hand if card in playableCards]
        if playableHand:
            # Compute scores for all playable cards, and play card with highest score.
            bestIndex = -1
            bestScore = -1
            bestCard = None
            for (index, card) in enumerate(playableHand):
                score = self.computeCardPlayScore(card)
                if score > bestScore:
                    bestIndex = self.hand.index(card)
                    bestScore = score
                    bestCard = card

            move = hs.Move(self.playerID, 'PLAY', hs.PlayCard(bestIndex, bestCard.colour))
            return move

        # 2. Discard dead or played card
        discardThreshold = self.game.TOTALCARDS - len(hs.COLOURS) * len(hs.VALUES) - \
                           self.game.handSize * self.game.nPlayers
        deadCards = self.game.discardPile.deadCards
        playedCards = self.game.playedCards
        if self.game.discardPile.total < discardThreshold:
            for index, card in enumerate(self.hand):
                if card in deadCards or card in playedCards:
                    move = hs.Move(self.playerID, 'DISCARD', index)
                    return move

        # 3. Give a hint
        if self.game.nHints > 0:
            hint = hs.Hint(self.getNextPlayer(), 1)
            move = hs.Move(self.playerID, 'HINT', hint)
            return move

        # 4. Discard dead or played card
        for index, card in enumerate(self.hand):
            if card in deadCards or card in playedCards:
                move = hs.Move(self.playerID, 'DISCARD', index)
                return move

        # 5. Discard duplicate card
        cts = Counter(self.hand)
        for card in cts:
            if cts[card] > 1:
                move = hs.Move(self.playerID, 'DISCARD', self.hand.index(card))
                return move

        otherPlayerHands = set()
        for i in range(self.game.nPlayers):
            if i != self.playerID:
                otherPlayerHands = otherPlayerHands.union(set(self.game.hands[i]))

        for index, card in enumerate(self.hand):
            if card in otherPlayerHands:
                move = hs.Move(self.playerID, 'DISCARD', index)
                return move

        # 6. Discard max dispensable card
        criticalCards = self.game.discardPile.getCriticalCards()
        dispensableCards = [card for card in self.hand if card not in criticalCards]
        if dispensableCards:
            move = hs.Move(self.playerID, 'DISCARD', self.hand.index(max(dispensableCards)))
            return move

        # 7. Discard first card
        i = self.findDiscard()
        move = hs.Move(self.playerID, 'DISCARD', i)
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
