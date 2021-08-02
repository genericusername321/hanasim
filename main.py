import logging
import time
import hanasim.hanasim as hs
# import agents.cheater_discard_first as agent
# import agents.cheater_smart as agent
import agents.cheat_tobin as agent

import pandas as pd
import numpy as np

# Number of cards each player has in their hand
HANDSIZE = {2: 5,
            3: 5,
            4: 4,
            5: 4}

# Configure logger
logLevel = logging.DEBUG

formatter = logging.Formatter('%(levelname)s:%(message)s')
fh = logging.FileHandler(filename='hanabi.log', mode='w')
fh.setLevel(logLevel)
fh.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logLevel)
logger.addHandler(fh)

# Set up game
nPlayers = 5
handSize = HANDSIZE[nPlayers]
seed = 0
game = hs.GameState(nPlayers, handSize, seed, logger=logger)

N = 1000
scores = np.zeros(N)
times = np.zeros(N)
for i in range(N):

    # Setup game
    game.setup()

    # Setup players
    players = [agent.Agent(ii, game) for ii in range(nPlayers)]

    # Simulate game
    ply = 0
    tic = time.perf_counter()
    while (not game.isOver):
        turn = ply % nPlayers
        ply += 1
        move = players[turn].findMove()
        game.doMove(move)

    # Record statistics and re-set the game state
    toc = time.perf_counter()
    scores[i] = game.score
    times[i] = toc-tic
    game.reset()

df = pd.DataFrame({'Scores': scores})
print(df.describe())

dfTime = pd.DataFrame({'Time': times})
print(dfTime.describe())

