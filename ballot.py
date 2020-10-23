from decimal import Decimal 

class Ballot:
    """
    Class representing a single ballot submitted by someone.
    """
    timestamp = ""
    """
    Timestamp this ballot was submitted, as reported by Google Forms.
    """
    weight = Decimal(1.0)
    """
    How is this ballot weighted?
    """
    rankings = []
    """
    Array of candidate indices, in descending order.

    A ballot that ranks candidates 1 before 0 before 2 would be encoded as [1, 0, 2].
    """
    def __init__(self, timestamp, weight, rankings):
        self.timestamp = timestamp
        self.weight = weight
        self.rankings = rankings