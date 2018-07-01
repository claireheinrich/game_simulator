from gamesimulator.action import Action
from gamesimulator.player import Player

A, B = Action.A, Action.B


class Defector(Player):
    """A player who only ever defects.

    Names:

    - Defector: [Axelrod1984]_
    - ALLD: [Press2012]_
    - Always defect: [Mittal2009]_
    """

    name = 'Defector'


    @staticmethod
    def strategy(opponent: Player) -> Action:
        return B