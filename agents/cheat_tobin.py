import hanasim.hanasim as hs


class Agent:
    """
    Cheating Hanasim player that applies the following strategy:
        1. Play a card
        2. Discard dead card, conditional on pace
        3. Hint
        4. Discard dead card
        5. Discard duplicate
        6. Discard non-critical
        7. Discard first

    This player cheats by inspecting its own hand.
    """

    def __init__(self, player_id, game):
        self.player_id = player_id

    def find_move(self, game):

        indices = game.player_hands[self.player_id]
        hand = [game.deck[i] for i in indices]

        # Try to play a card
        playable_cards = game.playable_cards
        for index, card in enumerate(hand):
            if card in playable_cards:
                action = (hs.PLAY, index, card.colour)
                return action

        # Hint if num hints are full
        if game.num_hints == 8:
            action = (hs.HINTCOLOUR, (self.player_id + 1) % game.num_players, 0)
            return action

        # Try to discard given sufficient velocity
        discard_threshold = (
            game.NUMCARDS
            - len(hs.COLOURS) * len(hs.RANKS)
            - (game.num_players * game.handsize)
        )

        if game.num_discarded < discard_threshold or game.num_hints == 0:
            action = self.find_useless_card(game, hand)
            if action:
                return action

        # Hint if there are hints left
        if game.num_hints > 0:
            action = (hs.HINTCOLOUR, (self.player_id + 1) % game.num_players, 0)
            return action

        # Discard a duplicate if it exists
        action = self.find_duplicate(game, hand)
        if action:
            return action

        # Discard non-critical
        action = self.find_non_critical(game, hand)
        if action:
            return action

        action = (hs.DISCARD, 0, None)
        return action

    def find_useless_card(self, game, hand):
        """Find a card that is has been played or is otherwise dead"""
        for index, card in enumerate(hand):
            if card in game.played_cards or card in game.dead_cards:
                return (hs.DISCARD, index, None)

        return None

    def find_non_critical(self, game, hand):
        for index, card in enumerate(hand):
            if card not in game.critical_cards:
                return (hs.DISCARD, index, None)

        return None
    
    def find_duplicate(self, game, hand):
        """ Find a card held by another player """
        other_hands = [game.player_hands[player] for player in 
                range(game.num_players) if player is not self.player_id]
        other_cards = set([game.deck[i] for hand in other_hands for i in hand])

        for index, card in enumerate(hand):
            if card in other_cards:
                return (hs.DISCARD, index, None)

        return None



