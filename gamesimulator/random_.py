import random
import numpy
from gamesimulator.action import Action


def random_choice(p: float = 0.5) -> Action:
    """
    Return A with probability `p`, else return B

    No random sample is carried out if p is 0 or 1.

    Parameters
    ----------
    p : float
        The probability of picking A

    Returns
    -------
    gamesimulator.Action
    """
    if p == 0:
        return Action.B

    if p == 1:
        return Action.A

    r = random.random()
    if r < p:
        return Action.A
    return Action.B


def randrange(a: int, b: int) -> int:
    """Python 2 / 3 compatible randrange. Returns a random integer uniformly
    between a and b (inclusive)"""
    c = b - a
    r = c * random.random()
    return a + int(r)


def seed(seed_):
    """Sets a seed"""
    random.seed(seed_)
    numpy.random.seed(seed_)


class Pdf(object):
    """A class for a probability distribution"""
    def __init__(self, counter):
        """Take as an instance of collections.counter"""
        self.sample_space, self.counts = zip(*counter.items())
        self.size = len(self.sample_space)
        self.total = sum(self.counts)
        self.probability = list([v / self.total for v in self.counts])

    def sample(self):
        """Sample from the pdf"""
        index = numpy.random.choice(a=range(self.size), p=self.probability)
        # Numpy cannot sample from a list of n dimensional objects for n > 1,
        # need to sample an index.
        return self.sample_space[index]

