# A cheating hanabi agent

import hanasim.hanasim as hs

class Agent:
    """
    This agent cheats by inspecting its own
    hand to find a card that can be played, eliminating the need 
    to be hinted, as such it also does not hint other players. It 
    performs actions with the following priority:
        1. Finds card to play in own hand
        2. If no card is playable, discard

    If no card can be played, it will discard the first card in its
    hand.
    """



    def __init__(self, playerID, game):

        self.playerID = playerID
        self.game = game

    def findMove(self):
        """
        Computes move according to priorities set in class description

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




