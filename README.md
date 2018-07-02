# game_simulator
Description: A two action simplified game simulator based on the 4.1.0 Axelrod simulator built by Vince Knight, Owen Campbell, and Marc Harper.

Basics: This game simulator will be used by run-tournaments.py to use all students' game strategies in a round-robin tournament that will ouput updated results every 10 minutes. 

Installation: First make sure you have Python 3.5 or greater installed on your machine. Go into command line and type the command "pip3 install gamesimulator".

Changing the Game: This simulator works for any game theory example that only allows players to choose between two actions. To change the game to a different scoring system, go into python3 via command line and type the following instructions:
      >>>import gamesimulator as gs
      >>>new_game = gs.game.Game(r=1, s=3, p=5, t=7)
There can be duplicate point values assigned and keep in mind that [A, A] = [r, r], [B, B] = [p, p], [A, B] = [s, t], and 
[B, A] = [t, s]. To make this new game be run in the class tournament, change line 15 in run-tournaments.py from "tournament = gs.Tournament(players, turns=5, repetitions=1)" to "tournament = gs.Tournament(players, turns=5, repetitions=1, game=new_game)"

Changing the Tournament Structure: To change the amount of turns for each player in a given repetition, go to line 15 of run-tournaments.py and change the turns variable as desired. To change the number of repetitions done in each run of the tournament, go to the same line and change the repetitions variable accordingly.
