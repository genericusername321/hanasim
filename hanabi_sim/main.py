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

logLevel = logging.CRITICAL

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
player1 = agent.Agent(0, game)
player2 = agent.Agent(1, game)

N = 2000
scores = np.zeros(N)
for i in range(N):
    nTurn = 0
    while (not game.isOver):
        playerToPlay = nTurn % nPlayers

        if playerToPlay == 0:
            move = player1.findMove()
        else:
            move = player2.findMove()

        game.doMove(move)

    scores[i] = game.score;
    game.reset()
    game.setup()

df = pd.DataFrame({'Scores' : scores})
print(df.describe())
hist = df.plot.hist(bins=10)

