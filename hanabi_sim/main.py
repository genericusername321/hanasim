import pytest
import logging
import hanasim as hs
import cheatingAgent as agent

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

nTurn = 0
while (game.isOver is False):
    playerToPlay = nTurn % nPlayers

    if playerToPlay == 0:
        move = player1.findMove()
    else:
        move = player2.findMove()

    game.doMove(move)

print("The final score is: {}".format(game.score))


