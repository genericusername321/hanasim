import hanasim.hanasim as hs

class Agent:
    """
    This agent cheats by looking at its own hand. It uses the following
    strategy:
        1. Plays first playable card in hand
        2. Discard first card
    """



    def __init__(self, playerID, game):

        self.playerID = playerID

    def find_move(self, game):
        """
        Computes move according to priorities set in class description

        :return: hanasim.Move type object encoding the selected move
        """

        # Cheat by accessing our own hand.
        my_hand = game.player_hands[self.playerID]
        my_cards = [game.deck[index] for index in my_hand]

        for index, card in enumerate(my_cards):
            colour, rank = card
            if game.fireworks[colour] + 1 == rank:
                action = (hs.PLAY, index, card[0])
                return action

        # Discard first card
        action = (hs.DISCARD, 0, None)
        return action
