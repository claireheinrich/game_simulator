from gamesimulator.action import Action
from gamesimulator.player import Player

A, B = Action.A, Action.B


class Cooperator(Player):
    """A player who only ever cooperates.

    Names:

    - Cooperator: [Axelrod1984]_
    - ALLC: [Press2012]_
    - Always cooperate: [Mittal2009]_
    """

    name = 'Cooperator'


    @staticmethod
    def strategy(opponent: Player) -> Action:
        return A