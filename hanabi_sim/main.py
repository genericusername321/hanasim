import hanasim

if __name__ == "__main__":

    game = hanasim.GameState(5, 2)
    game.setup()
    game.discard(0, game.hands[0][3], True)
    game.playCard(0, 3, game.piles['R'])
    game.playCard(3, 2, game.piles['R'])
    hint = hanasim.Hint(1, 'colour', 'R')
    game.playHint(0, 1, hint)
