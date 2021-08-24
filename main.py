import time
import random
import multiprocessing
import pandas as pd
import numpy as np
import hanasim.hanasim as hs

# import agents.cheater_discard_first as agent
import agents.cheat_tobin as agent


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
    N = 100000
    num_players = 5

    pool_obj = multiprocessing.Pool()
    scores = np.array(
        pool_obj.map(play_game, [num_players for _ in range(N)], chunksize=100)
    )

    df = pd.DataFrame({"Scores": scores})
    print(df.describe())
