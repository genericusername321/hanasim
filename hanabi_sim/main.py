import pytest
import logging
import hanasim as hs
import cheatingAgent as agent

import pandas as pd
import numpy as np

# Number of cards each player has in their hand
HANDSIZE = {2: 5,
            3: 5,
            4: 4,
            5: 4}

logLevel = logging.INFO

formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
fh = logging.FileHandler(filename='hanabi.log', mode='w')
fh.setLevel(logLevel)
fh.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logLevel)
logger.addHandler(fh)

# Set up game
nPlayers = 2
handSize = HANDSIZE[nPlayers]
seed = 0
game = hs.GameState(nPlayers, handSize, seed, logger = logger);
game.setup()

# Set up players
players = [agent.Agent(ii, game) for ii in range(nPlayers)]

N = 2
scores = np.zeros(N)
for i in range(N):
    ply = 0
    while (not game.isOver):
        turn = ply % nPlayers
        ply=ply+1
        move = players[turn].findMove()
        game.doMove(move)

    scores[i] = game.score;
    game.reset()
    game.setup()

df = pd.DataFrame({'Scores' : scores})
print(df.describe())
hist = df.plot.hist(bins=10)

