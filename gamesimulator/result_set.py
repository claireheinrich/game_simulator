from collections import namedtuple, Counter
from multiprocessing import cpu_count
import csv
import itertools

import numpy as np
import tqdm

import dask as da
import dask.dataframe as dd

from gamesimulator.action import Action, str_to_actions
import gamesimulator.interaction_utils as iu
from .game import Game


A, B = Action.A, Action.B


def update_progress_bar(method):
    """A decorator to update a progress bar if it exists"""
    def wrapper(*args, **kwargs):
        """Run the method and update the progress bar if it exists"""
        output = method(*args, **kwargs)

        try:
            args[0].progress_bar.update(1)
        except AttributeError:
            pass

        return output
    return wrapper


class ResultSet():
    """
    A class to hold the results of a tournament. Reads in a CSV file produced
    by the tournament class.
    """

    def __init__(self, filename,
                 players, repetitions,
                 processes=None, progress_bar=True):
        """
        Parameters
        ----------
            filename : string
                the file from which to read the interactions
            players : list
                A list of the names of players. If not known will be efficiently
                read from file.
            repetitions : int
                The number of repetitions of each match. If not know will be
                efficiently read from file.
            processes : integer
                The number of processes to be used for parallel processing
        """
        self.filename = filename
        self.players, self.repetitions = players, repetitions
        self.num_players = len(self.players)

        if progress_bar:
            self.progress_bar = tqdm.tqdm(total=25,
                                          desc="Analysing")

        df = dd.read_csv(filename)
        dask_tasks = self._build_tasks(df)

        if processes == 0:
            processes = cpu_count()

        out = self._compute_tasks(tasks=dask_tasks, processes=processes)

        self._reshape_out(*out)

        if progress_bar:
            self.progress_bar.close()

    def _reshape_out(self,
                     mean_per_reps_player_opponent_df,
                     sum_per_player_opponent_df,
                     sum_per_player_repetition_df,
                     normalised_scores_series,
                     interactions_count_series):
        """
        Reshape the various pandas series objects to be of the required form and
        set the corresponding attributes.
        """

        # self.payoffs = self._reshape_three_dim_list(
#                 mean_per_reps_player_opponent_df["Score per turn"],
#                 first_dimension=range(self.num_players),
#                 second_dimension=range(self.num_players),
#                 third_dimension=range(self.repetitions),
#                 key_order=[2, 0, 1])

        self.score_diffs = self._reshape_three_dim_list(
                mean_per_reps_player_opponent_df["Score difference per turn"],
                first_dimension=range(self.num_players),
                second_dimension=range(self.num_players),
                third_dimension=range(self.repetitions),
                key_order=[2, 0, 1],
                alternative=0)

        self.match_lengths = self._reshape_three_dim_list(
                mean_per_reps_player_opponent_df["Turns"],
                first_dimension=range(self.repetitions),
                second_dimension=range(self.num_players),
                third_dimension=range(self.num_players),
                alternative=0)

        self.wins = self._reshape_two_dim_list(sum_per_player_repetition_df["Win"])
        self.scores = self._reshape_two_dim_list(sum_per_player_repetition_df["Score"])
        self.normalised_scores = self._reshape_two_dim_list(normalised_scores_series)

        columns = ["AA count", "AB count", "BA count", "BB count"]
        self.state_distribution = self._build_state_distribution(sum_per_player_opponent_df[columns])
        self.normalised_state_distribution = self._build_normalised_state_distribution()

        # columns = ["AA to A count",
#                    "AA to B count",
#                    "AB to A count",
#                    "AB to B count",
#                    "BA to A count",
#                    "BA to B count",
#                    "BB to A count",
#                    "BB to B count"]
#         self.state_to_action_distribution = self._build_state_to_action_distribution(sum_per_player_opponent_df[columns])
#         self.normalised_state_to_action_distribution = self._build_normalised_state_to_action_distribution()

        self.ranking = self._build_ranking()
        self.ranked_names = self._build_ranked_names()

        # self.payoff_matrix = self._build_summary_matrix(self.payoffs)
#         self.payoff_stddevs = self._build_summary_matrix(self.payoffs,
#                                                          func=np.std)

        # self.payoff_diffs_means = self._build_payoff_diffs_means()

    @update_progress_bar
    def _reshape_three_dim_list(self, series,
                                first_dimension,
                                second_dimension,
                                third_dimension,
                                alternative=None,
                                key_order=[0, 1, 2]):
        """
        Parameters
        ----------

            payoffs_series : pandas.Series
            first_dimension : iterable
            second_dimension : iterable
            third_dimension : iterable
            alternative : int
                What to do if there is no entry at given position
            key_order : list
                Indices re-ording the dimensions to the correct keys in the
                series

        Returns:
        --------
            A three dimensional list across the three dimensions
        """
        series_dict = series.to_dict()
        output = []
        for first_index in first_dimension:
            matrix = []
            for second_index in second_dimension:
                row = []
                for third_index in third_dimension:
                    key = (first_index, second_index, third_index)
                    key = tuple([key[order] for order in key_order])
                    if key in series_dict:
                        row.append(series_dict[key])
                    elif alternative is not None:
                        row.append(alternative)
                matrix.append(row)
            output.append(matrix)
        return output

    @update_progress_bar
    def _reshape_two_dim_list(self, series):
        """
        Parameters
        ----------

            series : pandas.Series

        Returns:
        --------
            A two dimensional list across repetitions and opponents
        """
        series_dict = series.to_dict()
        out = [[series_dict.get((player_index, repetition), 0)
                  for repetition in range(self.repetitions)]
                 for player_index in range(self.num_players)]
        return out


    @update_progress_bar
    def _build_summary_matrix(self, attribute, func=np.mean):
        matrix = [[0 for opponent_index in range(self.num_players)]
                  for player_index in range(self.num_players)]

        pairs = itertools.product(range(self.num_players), repeat=2)

        for player_index, opponent_index in pairs:
            utilities = attribute[player_index][opponent_index]
            if utilities:
                matrix[player_index][opponent_index] = func(utilities)

        return matrix

    # @update_progress_bar
#     def _build_payoff_diffs_means(self):
#         payoff_diffs_means = [[np.mean(diff) for diff in player]
#                                for player in self.score_diffs]
# 
#         return payoff_diffs_means

    @update_progress_bar
    def _build_state_distribution(self, state_distribution_series):
        state_key_map = {'AA count': (A, A),
                         'AB count': (A, B),
                         'BA count': (B, A),
                         'BB count': (B, B)}
        state_distribution = [[create_counter_dict(state_distribution_series,
                                                   player_index,
                                                   opponent_index,
                                                   state_key_map)
                               for opponent_index in range(self.num_players)]
                              for player_index in range(self.num_players)]
        return state_distribution

    @update_progress_bar
    def _build_normalised_state_distribution(self):
        """
        Returns:
        --------
            norm : list

            Normalised state distribution. A list of lists of counter objects:

            Dictionary where the keys are the states and the values are a
            normalized counts of the number of times that state occurs.
        """
        normalised_state_distribution = []
        for player in self.state_distribution:
            counters = []
            for counter in player:
                total = sum(counter.values())
                counters.append(Counter({key: value / total for
                                         key, value in counter.items()}))
            normalised_state_distribution.append(counters)
        return normalised_state_distribution

    # @update_progress_bar
#     def _build_state_to_action_distribution(self,
#                                             state_to_action_distribution_series):
#         state_to_action_key_map = {"AA to A count": ((A, A), A),
#                                    "AA to B count": ((A, A), B),
#                                    "AB to A count": ((A, B), A),
#                                    "AB to B count": ((A, B), B),
#                                    "BA to A count": ((B, A), A),
#                                    "BA to B count": ((B, A), B),
#                                    "BB to A count": ((B, B), A),
#                                    "BB to B count": ((B, B), B)}
#         state_to_action_distribution = [[
#                 create_counter_dict(state_to_action_distribution_series,
#                                     player_index,
#                                     opponent_index,
#                                     state_to_action_key_map)
#                                  for opponent_index in range(self.num_players)]
#                                 for player_index in range(self.num_players)]
#         return state_to_action_distribution

   #  @update_progress_bar
#     def _build_normalised_state_to_action_distribution(self):
#         """
#         Returns:
#         --------
#             norm : list
# 
#             A list of lists of counter objects.
# 
#             Dictionary where the keys are the states and the values are a
#             normalized counts of the number of times that state goes to a given
#             action.
#         """
#         normalised_state_to_action_distribution = []
#         for player in self.state_to_action_distribution:
#             counters = []
#             for counter in player:
#                 norm_counter = Counter()
#                 for state in [(A, A), (A, B), (B, A), (B, B)]:
#                     total = counter[(state, A)] + counter[(state, B)]
#                     if total > 0:
#                         for action in [A, B]:
#                             if counter[(state, action)] > 0:
#                                 norm_counter[(state, action)] = counter[(state, action)] / total
#                 counters.append(norm_counter)
#             normalised_state_to_action_distribution.append(counters)
#         return normalised_state_to_action_distribution


    @update_progress_bar
    def _build_ranking(self):
        ranking = sorted(
                range(self.num_players),
                key=lambda i: -np.nanmedian(self.normalised_scores[i]))
        return ranking

    @update_progress_bar
    def _build_ranked_names(self):
        ranked_names = [str(self.players[i]) for i in self.ranking]
        return ranked_names


    def _compute_tasks(self, tasks, processes):
        """
        Compute all dask tasks
        """
        if processes is None:
            out = da.compute(*tasks, get=da.get)
        else:
            out = da.compute(*tasks, num_workers=processes)
        return out

    def _build_tasks(self, df):
        """
        Returns a tuple of dask tasks
        """
        groups = ["Repetition", "Player index", "Opponent index"]
        columns = ["Turns", "Score per turn", "Score difference per turn"]
        mean_per_reps_player_opponent_task = df.groupby(groups)[columns].mean()

        groups = ["Player index", "Opponent index"]
        columns = ["AA count",
                   "AB count",
                   "BA count",
                   "BB count"]
        sum_per_player_opponent_task = df.groupby(groups)[columns].sum()

        ignore_self_interactions_task = df["Player index"] != df["Opponent index"]
        adf = df[ignore_self_interactions_task]

        groups = ["Player index", "Repetition"]
        columns = ["Win", "Score"]
        sum_per_player_repetition_task = adf.groupby(groups)[columns].sum()

        groups = ["Player index", "Repetition"]
        column = "Score per turn"
        normalised_scores_task = adf.groupby(groups)[column].mean()


        interactions_count_task = adf.groupby("Player index")["Player index"].count()


        return (mean_per_reps_player_opponent_task,
                sum_per_player_opponent_task,
                sum_per_player_repetition_task,
                normalised_scores_task,
                interactions_count_task)

    def __eq__(self, other):
        """
        Check equality of results set

        Parameters
        ----------

            other : axelrod.ResultSet
                Another results set against which to check equality
        """
        return all([self.wins == other.wins,
                    self.match_lengths == other.match_lengths,
                    self.scores == other.scores,
                    self.normalised_scores == other.normalised_scores,
                    self.ranking == other.ranking,
                    self.ranked_names == other.ranked_names,
                    #self.payoffs == other.payoffs,
                    #self.payoff_matrix == other.payoff_matrix,
                    #self.payoff_stddevs == other.payoff_stddevs,
                    self.score_diffs == other.score_diffs])
                    #self.payoff_diffs_means == other.payoff_diffs_means])

    def __ne__(self, other):
        """
        Check inequality of results set

        Parameters
        ----------

            other : gamesimulator.ResultSet
                Another results set against which to check inequality
        """
        return not self.__eq__(other)

    def summarise(self):
        """
        Obtain summary of performance of each strategy:
        ordered by rank, including median normalised score and cooperation
        rating.

        Output
        ------

            A list of the form:

            [[player name, median score],...]

        """

        median_scores = map(np.nanmedian, self.normalised_scores)
        median_wins = map(np.nanmedian, self.wins)

        self.player = namedtuple("Player", ["Rank", "Name", "Median_score", 
        									"Wins", "AA_rate",
                                            "AB_rate", "BA_rate", "BB_rate"])

        states = [(A, A), (A, B), (B, A), (B, B)]
        state_prob = []
        for i, player in enumerate(self.normalised_state_distribution):
            counts = []
            for state in states:
                p = sum([opp[state] for j, opp in enumerate(player) if i != j])
                counts.append(p)
            try:
                counts = [c / sum(counts) for c in counts]
            except ZeroDivisionError:
                counts = [0 for c in counts]
            state_prob.append(counts)

        # state_to_A_prob = []
#         for player in self.normalised_state_to_action_distribution:
#             rates = []
#             for state in states:
#                 counts = [counter[(state, A)] for counter in player
#                           if counter[(state, A)] > 0]
# 
#                 if len(counts) > 0:
#                     rate = np.mean(counts)
#                 else:
#                     rate = 0
# 
#                 rates.append(rate)
#             state_to_A_prob.append(rates)

        summary_measures = list(zip(self.players, median_scores, median_wins))

        summary_data = []
        for rank, i in enumerate(self.ranking):
            data = list(summary_measures[i]) + state_prob[i] 
            summary_data.append(self.player(rank, *data))

        return summary_data

    def write_summary(self, filename):
        """
        Write a csv file containing summary data of the results of the form:

            "Rank", "Name", "Median-score-per-turn", "Wins", "CC-Rate", "CD-Rate", "DC-Rate", "DD-rate","CC-to-C-Rate", "CD-to-C-Rate", "DC-to-C-Rate", "DD-to-C-rate"


        Parameters
        ----------
            filename : a filepath to which to write the data
        """
        summary_data = self.summarise()
        with open(filename, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            writer.writerow(self.player._fields)
            for player in summary_data:
                writer.writerow(player)


def create_counter_dict(df, player_index, opponent_index, key_map):
    """
    Create a Counter object mapping states (corresponding to columns of df) for
    players given by player_index, opponent_index. Renaming the variables with
    `key_map`. Used by `ResultSet._reshape_out`

    Parameters
    ----------
        df : a multiindex pandas df
        player_index: int
        opponent_index: int
        key_map : a dict
            maps cols of df to strings

    Returns
    -------
        A counter dictionary
    """
    counter = Counter()
    if player_index != opponent_index:
        if (player_index, opponent_index) in df.index:
            for key, value in df.loc[player_index, opponent_index].items():
                if value > 0:
                    counter[key_map[key]] = value
    return counter

