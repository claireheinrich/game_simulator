from math import ceil, log
import random

from gamesimulator.action import Action
from gamesimulator.game import Game
from gamesimulator import DEFAULT_TURNS
import gamesimulator.interaction_utils as iu


A, B = Action.A, Action.B



class Match(object):
    """The Match class conducts matches between two players."""

    def __init__(self, players, turns=None,
                 game=None, match_attributes=None):
        """
        Parameters
        ----------
        players : tuple
            A pair of gamesimulator.Player objects
        turns : integer
            The number of turns per match
        game : gamesimulator.Game
            The game object used to score the match
        match_attributes : dict
            Mapping attribute names to values which should be passed to players.
            The default is to use the correct values for turns, game and noise
            but these can be overridden if desired.
        """

        defaults = {(True): (DEFAULT_TURNS),
                    (False): (turns)}
        self.turns = defaults[(turns is None)]

        self.result = []

        if game is None:
            self.game = Game()
        else:
            self.game = game

        if match_attributes is None:
            known_turns = self.turns
            self.match_attributes = {
                'length': known_turns,
                'game': self.game
            }
        else:
            self.match_attributes = match_attributes

        self.players = list(players)

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, players):
        """Ensure that players are passed the match attributes"""
        newplayers = []
        for player in players:
            player.set_match_attributes(**self.match_attributes)
            newplayers.append(player)
        self._players = newplayers


    def play(self):
        """
        The resulting list of actions from a match between two players.

        This method calls the play method for player1 and returns the list from there.

        Returns
        -------
        A list of the form:

        e.g. for a 2 turn match between Cooperator and Defector:

            [(A, A), (A, B)]

        i.e. One entry per turn containing a pair of actions.
        """
        turns = self.turns
        
        for p in self.players:
            p.reset()
            p.set_match_attributes(**self.match_attributes)
        for _ in range(turns):
            self.players[0].play(self.players[1])
        result = list(
            zip(self.players[0].history, self.players[1].history))


        self.result = result
        return result

    def scores(self):
        """Returns the scores of the previous Match plays."""
        return iu.compute_scores(self.result, self.game)

    def final_score(self):
        """Returns the final score for a Match."""
        return iu.compute_final_score(self.result, self.game)

    def final_score_per_turn(self):
        """Returns the mean score per round for a Match."""
        return iu.compute_final_score_per_turn(self.result, self.game)

    def winner(self):
        """Returns the winner of the Match."""
        winner_index = iu.compute_winner_index(self.result, self.game)
        if winner_index is False:  # No winner
            return False
        if winner_index is None:  # No plays
            return None
        return self.players[winner_index]


    def state_distribution(self):
        """
        Returns the count of each state for a set of interactions.
        """
        return iu.compute_state_distribution(self.result)

    def normalised_state_distribution(self):
        """
        Returns the normalized count of each state for a set of interactions.
        """
        return iu.compute_normalised_state_distribution(self.result)


    def __len__(self):
        return self.turns



