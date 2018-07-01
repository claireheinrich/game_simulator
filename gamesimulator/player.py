from collections import defaultdict
import copy
import inspect
import itertools
import random

import numpy as np

from gamesimulator.action import Action
from .game import DefaultGame

import types
from typing import Dict, Any

A, B = Action.A, Action.B


def update_history(player, move):
    """Updates histories and cooperation / defections counts following play."""
    # Update histories
    player.history.append(move)
    # Update player counts of action A and action B
    if move == A:
        player.action_a += 1
    elif move == B:
        player.action_b += 1


def get_state_distribution_from_history(player, history_1, history_2):
    """Gets state_distribution from player's and opponent's histories."""
    for action, reply in zip(history_1, history_2):
        update_state_distribution(player, action, reply)


def update_state_distribution(player, action, reply):
    """Updates state_distribution following play. """
    last_turn = (action, reply)
    player.state_distribution[last_turn] += 1


class Player(object):
    """A class for a player in the tournament.

    This is an abstract base class, not intended to be used directly.
    """

    name = "Player"


    def __new__(cls, *args, **kwargs):
        """Caches arguments for Player cloning."""
        obj = super().__new__(cls)
        obj.init_kwargs = cls.init_params(*args, **kwargs)
        return obj

    @classmethod
    def init_params(cls, *args, **kwargs):
        """
        Return a dictionary containing the init parameters of a strategy
        (without 'self').
        Use *args and *kwargs as value if specified
        and complete the rest with the default values.
        """
        sig = inspect.signature(cls.__init__)
        # The 'self' parameter needs to be removed or the first *args will be
        # assigned to it
        self_param = sig.parameters.get('self')
        new_params = list(sig.parameters.values())
        new_params.remove(self_param)
        sig = sig.replace(parameters=new_params)
        boundargs = sig.bind_partial(*args, **kwargs)
        boundargs.apply_defaults()
        return boundargs.arguments

    def __init__(self):
        """Initiates an empty history and 0 score for a player."""
        self.history = []
        self.action_a = 0
        self.action_b = 0
        self.state_distribution = defaultdict(int)
        self.set_match_attributes()

    def __eq__(self, other):
        """
        Test if two players are equal.
        """
        if self.__repr__() != other.__repr__():
            return False

        for attribute in set(list(self.__dict__.keys()) +
                             list(other.__dict__.keys())):

            value = getattr(self, attribute, None)
            other_value = getattr(other, attribute, None)

            if isinstance(value, np.ndarray):
                if not (np.array_equal(value, other_value)):
                    return False

            elif isinstance(value, types.GeneratorType) or \
                 isinstance(value, itertools.cycle):

                # Split the original generator so it is not touched
                generator, original_value = itertools.tee(value)
                other_generator, original_other_value = itertools.tee(other_value)

                if isinstance(value, types.GeneratorType):
                    setattr(self, attribute,
                            (ele for ele in original_value))
                    setattr(other, attribute,
                            (ele for ele in original_other_value))
                else:
                    setattr(self, attribute,
                            itertools.cycle(original_value))
                    setattr(other, attribute,
                            itertools.cycle(original_other_value))

                for _ in range(200):
                    try:
                        if next(generator) != next(other_generator):
                            return False
                    except StopIteration:
                        break

            # Code for a strange edge case where each strategy points at each
            # other
            elif value is other and other_value is self:
                pass
            else:
                if value != other_value:
                    return False
        return True

    def receive_match_attributes(self):
        # Overwrite this function if your strategy needs
        # to make use of match_attributes such as
        # the game matrix, the number of rounds or the noise
        pass

    def set_match_attributes(self, length=-1, game=None):
        if not game:
            game = DefaultGame
        self.match_attributes = {
            "length": length,
            "game": game
        }
        self.receive_match_attributes()

    def __repr__(self):
        """The string method for the strategy.
        Appends the `__init__` parameters to the strategy's name."""
        name = self.name
        prefix = ': '
        gen = (value for value in self.init_kwargs.values() if value is not None)
        for value in gen:
            try:
                if issubclass(value, Player):
                    value = value.name
            except TypeError:
                pass
            name = ''.join([name, prefix, str(value)])
            prefix = ', '
        return name

    def strategy(self, opponent):
        """This is a placeholder strategy."""
        raise NotImplementedError()

    def play(self, opponent, noise=0):
        """This pits two players against each other."""
        s1, s2 = self.strategy(opponent), opponent.strategy(self)
        update_history(self, s1)
        update_history(opponent, s2)
        update_state_distribution(self, s1, s2)
        update_state_distribution(opponent, s2, s1)

    def clone(self):
        """Clones the player without history, reapplying configuration
        parameters as necessary."""

        # You may be tempted to re-implement using the `copy` module
        # Note that this would require a deepcopy in some cases and there may
        # be significant changes required throughout the library.
        # Override in special cases only if absolutely necessary
        cls = self.__class__
        new_player = cls(**self.init_kwargs)
        new_player.match_attributes = copy.copy(self.match_attributes)
        return new_player

    def reset(self):
        """Resets a player to its initial state

        This method is called at the beginning of each match (between a pair
        of players) to reset a player's state to its initial starting point.
        It ensures that no 'memory' of previous matches is carried forward.
        """
        self.history = []
        self.action_a = 0
        self.action_b = 0
        self.state_distribution = defaultdict(int)
        self.__init__(**self.init_kwargs)

