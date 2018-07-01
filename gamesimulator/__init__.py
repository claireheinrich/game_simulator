DEFAULT_TURNS = 200

# The order of imports matters!
from .versions import version
from . import graph
from .action import Action
from .random_ import random_choice, seed, Pdf
from .plot import Plot
from .game import DefaultGame, Game
from .player import (
    get_state_distribution_from_history, 
    update_history, update_state_distribution, Player)
from .match import Match
from .strategies import *
from .match_generator import *
from .tournament import Tournament
from .result_set import ResultSet
from .interaction_utils import *


