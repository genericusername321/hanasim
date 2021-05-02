# A cheating hanabi agent

import hanasim.hanasim as hs

class Agent:

    def __init__(self, playerID, game):

        self.playerID = playerID
        self.game = game

    def findMove(self):
        """
        Finds a move to play
        :return: hanasim.Move type object encoding the selected move
        """

        # Cheat by accessing our own hand.
        hand = self.game.hands[self.playerID]

        # Check whether we have any card that can be played
        for colour in hs.COLOURS:
            nextCard = self.game.fireworks[colour].getNextCard()

            try:
                cardIndex = hand.index(nextCard)
            except ValueError:
                cardIndex = None

            if cardIndex is not None:
                move = hs.Move(self.playerID, 'PLAY', hs.PlayCard(cardIndex, colour))
                return move

        # Discard the first card.
        move = hs.Move(self.playerID, 'DISCARD', 0)
        return move




