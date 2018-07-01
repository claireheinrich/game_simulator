"""
Defines the core actions for the Two-Player Game:
* Action A
* Action B

Uses the enumeration, Action.A and Action.B. For convenience you can use:

from gamesimulator import Action
A, B = Action.A, Action.B
"""

from enum import Enum
from typing import Iterable


class UnknownActionError(ValueError):
    def __init__(self, *args):
        super(UnknownActionError, self).__init__(*args)


class Action(Enum):

    A = 1
    B = 0

    def __bool__(self):
        return bool(self.value)

    def __repr__(self):
        return '{}'.format(self.name)

    def __str__(self):
        return '{}'.format(self.name)

    def flip(self):
        """Returns the opposite Action. """
        if self == Action.A:
            return Action.B
        if self == Action.B:
            return Action.A

    @classmethod
    def from_char(cls, character):
        """Converts a single character into an Action. `Action.from_char('A')`
        returns `Action.A`. `Action.from_char('BB')` raises an error. Use
        `str_to_actions` instead."""
        if character == 'A':
            return cls.A
        elif character == 'B':
            return cls.B
        else:
            raise UnknownActionError('Character must be "A" or "B".')


def str_to_actions(actions: str) -> tuple:
    """Takes a string like 'AABB' and returns a tuple of the appropriate
    actions."""
    return tuple(Action.from_char(element) for element in actions)


def actions_to_str(actions: Iterable[Action]) -> str:
    """Takes any iterable of Action and returns a string of 'A's
    and 'B's.  ex: (B, B, A) -> 'BBA' """
    return "".join(map(repr, actions))

