
class MatchGenerator(object):

    def __init__(self, players, repetitions, turns=None, game=None, match_attributes=None):
        """
        A class to generate matches. This is used by the Tournament class which
        is in charge of playing the matches and collecting the results.

        Parameters
        ----------
        players : list
            A list of gamesimulator.Player objects
        turns : integer
            The number of turns per match
        game : gamesimulator.Game
            The game object used to score the match
        repetitions : int
            The number of repetitions of a given match
        match_attributes : dict
            Mapping attribute names to values which should be passed to players.
            The default is to use the correct values for turns, game and noise
            but these can be overridden if desired.
        """
        self.players = players
        self.turns = turns
        self.game = game
        self.repetitions = repetitions
        self.opponents = players
        self.match_attributes = match_attributes

        n = len(self.players)
        self.size = int(n * (n - 1) // 2 + n)

    def __len__(self):
        return self.size

    def build_match_chunks(self):
        """
        A generator that returns player index pairs and match parameters for a
        round robin tournament.

        Yields
        -------
        tuples
            ((player1 index, player2 index), match object)
        """
        edges = complete_graph(self.players)
     
        for index_pair in edges:
            match_params = self.build_single_match_params()
            yield (index_pair, match_params, self.repetitions)

    def build_single_match_params(self):
        """
        Creates a single set of match parameters.
        """
        return {"turns": self.turns, "game": self.game,
                "match_attributes": self.match_attributes}


def complete_graph(players):
    """
    Return generator of edges of a complete graph on a set of players
    """
    for player1_index, _ in enumerate(players):
        for player2_index in range(player1_index, len(players)):
            yield (player1_index, player2_index)


def graph_is_connected(edges, players):
    """
    Test if the set of edges defines a graph in which each player is connected
    to at least one other player. This function does not test if the graph is
    fully connected in the sense that each node is reachable from every other
    node.

    Parameters:
    -----------
    edges : a list of 2 tuples
    players : a list of player names

    Returns:
    --------
    boolean : True if the graph is connected as specified above.
    """
    # Check if all players are connected.
    player_indices = set(range(len(players)))
    node_indices = set()
    for edge in edges:
        for node in edge:
            node_indices.add(node)

    return player_indices == node_indices

