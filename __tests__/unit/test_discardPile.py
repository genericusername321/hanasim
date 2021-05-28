import pytest
import hanasim.hanasim as hs


class TestDiscardPile:

    def setup_method(self):

        self.discardPile = hs.DiscardPile(hs.CARDCOUNTS)

    def test_discard(self):

        for card in self.discardPile.cardCounts:
            assert self.discardPile.cardCounts[card] == 0

        card = hs.Card('R', 1)
        self.discardPile.discard(card)

        assert self.discardPile.cardCounts[card] == 1

    def test_remove(self):

        card = hs.Card('R', 1)
        self.discardPile.discard(card)
        assert self.discardPile.cardCounts[card] == 1

        self.discardPile.remove(card)
        assert self.discardPile.cardCounts[card] == 0

    def test_getMaxScore(self):

        assert self.discardPile.getMaxScore() == 25

        card = hs.Card('R', 2)
        for i in range(self.discardPile.maxCardCounts[card.value]):
            self.discardPile.discard(card)

        assert self.discardPile.getMaxScore() == 21

    def test_getCriticalCards(self):

        card = hs.Card('R', 2)
        self.discardPile.discard(card)
        actual = self.discardPile.getCriticalCards()
        expected = [card]
        expected.extend([hs.Card(colour, 5) for colour in hs.COLOURS])

        assert actual == expected



