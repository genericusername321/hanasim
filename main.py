import time
import random
import pandas as pd
import numpy as np
import hanasim.hanasim as hs
import agents.cheater_discard_first as agent


def play_game(num_players):

    game = hs.Board(num_players)
    game.generate_deck()
    game.setup()


    players = [agent.Agent(ii, game) for ii in range(num_players)]

    while not game.game_over:
        player_id = game.turn % num_players
        action = players[player_id].find_move(game)
        game.resolve_move(player_id, action)

    return game.score


if __name__ == "__main__":
    random.seed(0)
    N = 10000
    num_players = 2
    scores = np.zeros(N)
    times = np.zeros(N)

    for i in range(N):
        tic = time.perf_counter()
        scores[i] = play_game(num_players)
        toc = time.perf_counter()
        times[i] = toc - tic

    df = pd.DataFrame({"Scores": scores})
    print(df.describe())

    dfTime = pd.DataFrame({"Time": times})
    print(dfTime.describe())
