"""
Python module listing the elected offices and their number of seats.
"""

from decimal import Decimal

# Maps office:str -> seats:int
OFFICES = {
    "president": {
        "num_seats": 1, # how many seats to fill for this office?
        "graduating_vote_weight": Decimal("1.0") # how are graduating votes weighted for this office?
    },
    "vice_president": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "treasurer": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "mens_workout_coordinator": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "womens_workout_coordinator": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "sprint_coordinator": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "meet_coordinator": {
        "num_seats": 2,
        "graduating_vote_weight": Decimal("1.0") 
    },
    "mens_social_chair": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "womens_social_chair": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("1.0") 
    },
    "fundraising_chair": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("0.5") # NB: as of fall 2020, any position that first-years are permitted to run for also have half-votes for graduating members
    },
    "webmaster": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("0.5") 
    },
    "mens_recruitment_chair": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("0.5") 
    },
    "womens_recruitment_chair": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("0.5") 
    },
    "secretary": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("0.5") 
    },
    "team_relations_chair": {
        "num_seats": 1, 
        "graduating_vote_weight": Decimal("0.5") 
    }
}