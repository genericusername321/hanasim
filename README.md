# hanasim

Hanabi is a card game of incomplete information where players work together to attempt to play a set of cards in the right order. The catch is that any individual player can see everyone else's hand, but not their own. This project implements a python module to write and simulate hanabi strategies.

TODO:
- [ ] Implement game logic
    - [ ] Make player_hands private and implement get_hand() method.
        The get_hand method should check that a player cannot request 
        their own hand!
    - [x] Implement JSON dump of action history to visualize games on
        Hanab.live
    - [x] Expand scope of unit tests and introduce test coverage statistics
    - [ ] Get more statistics from game and visualize statistics in Jupyter notebook
    - [x] Implement main script
    - [x] Fix critical and dead cards calculator

- [ ] Bots:
    - [ ] Implement Hanabi bot using Hyphen-ated conventions
    - [ ] Implement bot with some hat-guessing strategy
    - [ ] Train agent with neural network?
    - [x] Implement Tobin strategy cheating agent

- [ ] Infrastructure:
    - [ ] Unit tests on commit

