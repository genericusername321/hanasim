import time
import hanasim.hanasim as hs
import agents.cheater_discard_first as agent

import pandas as pd
import numpy as np


def play_game(num_players):

    game = hs.Board(num_players)
    game.generate_deck()
    game.deal()

    players = [agent.Agent(ii, game) for ii in range(num_players)]

    turn = 0
    while not game.game_over:
        player_id = turn % num_players
        action = players[player_id].find_move(game)
        game.resolve_move(player_id, action)

    return game.score

if __name__ == "__main__":
    N = 10
    scores = np.zeros(N)
    times = np.zeros(N)

    for i in range(N):
        tic = time.perf_counter()
        scores[i] = play_game(2)
        toc = time.perf_counter()
        times[i] = toc-tic


    df = pd.DataFrame({'Scores': scores})
    print(df.describe())

    dfTime = pd.DataFrame({'Time': times})
    print(dfTime.describe())

