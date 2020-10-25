"""
Python implementation of Single Transferable Vote (https://en.wikipedia.org/wiki/Single_transferable_vote), a kind of ranked choice voting that tries to minimize wasted votes and disincentivizes "strategic voting."

Written for UVa Club Running's Fall 2020 Exec elections.
"""

import offices
import config
import ballot
import sys
import argparse
import csv
import re
import random
from decimal import *

getcontext().prec = 5 # 5 digits of decimal precision

VERSION_STRING = "0.1"

parser = argparse.ArgumentParser(
    description=f"pystv v{VERSION_STRING} - ballot counter for Club Running's Fall 2020 Elections",
    epilog="Skyler Moon is a thoughtful guy."
)

parser.add_argument(
    "file",
    metavar="input_file",
    nargs="?",
    help="Google Form election results data to count, stored as a csv."
)

parser.add_argument(
    "office",
    nargs="?",
    metavar="office", 
    choices=offices.OFFICES.keys(),
    help="the office to run an election for. List offices with --list-offices."
)

parser.add_argument(
    "--list-offices",
    action="store_true",
    help="Lists the offices available to run an election for and quits."
)

parser.add_argument(
    "-y",
    action="store_true",
    help="Answers 'yes' to all of the confirmation questions automatically. Only use this if you're really confident!"
)

parser.add_argument(
    "--seed",
    action="store",
    default=None,
    type=int,
    help="Optional seed to use for the PRNG in case of a tie. If omitted, the seed will be selected based on system time."
)

parser.add_argument(
    "--pause",
    action="store_true",
    help="Pauses the ballot counting in between rounds."
)

args = parser.parse_args()

print(f"pystv v{VERSION_STRING}")
print("Built for Club Running by Joe Kerrigan")


if args.list_offices:
    # We should list offices and exit.
    print("Offices available for election:")
    for office in offices.OFFICES.keys():
        print(f"    {office}")
    sys.exit(0)
 
seed = args.seed
if seed is None:
    seed = random.randrange(sys.maxsize)

rng = random.Random(seed)
print(f"(Using random seed {seed})")
print()
print("Reproducibility:")
print("You should be able to reproduce these election results by running:")
print(f"    python {sys.argv[0]} -y --seed {seed} {args.file} {args.office}") 
print()


if args.file is None:
    print(f"FATAL: Input file is requried to run election (try {sys.argv[0]} --help)")
    sys.exit(1)

if args.office is None:
    print(f"FATAL: An office is required to run election (try {sys.argv[0]} --help)")
    sys.exit(1)

seats = offices.OFFICES[args.office]
print(f"Running an election for {args.office}, which has {seats} seat(s) up for election.")

def _confirm_yn(prompt: str):
    if args.y:
        return True
    else:
        return input(prompt + " [y/n] ") == "y"

CANDIDATE_REGEX = re.compile(r"^.+\[(.+)\]$") # Matches the response part of Google Forms header "Question [Response]"
ORDINAL_REGEX = re.compile(r"^(\d)+(?:st|nd|rd|th) choice$") # Matches the numeric parts of the ordinal "1st choice", "2nd choice," etc.

print("Reading election data...")
ballots = []
with open(args.file, "r") as csvfile:
    reader = csv.reader(csvfile)
    # Extract candidate names by looking at the column headers.
    headers = next(reader)
    # 0 - timestamp
    # 1 - On Your Honor... 4th Year Question
    # 2 to n - "Rank your choices" [Candidate Name]
    candidates = []
    print("Detecting candidates...")
    for i, col in enumerate(headers[2:]):
        match = CANDIDATE_REGEX.findall(col)
        if len(match) == 0:
            print(f"FATAL: Failed to extract candidate from header for column {i + 2}.")
            sys.exit(1)
        else:
            candidates.append(match[0])

    print(f"Detected {len(candidates)} candidates:")
    for i,candidate in enumerate(candidates):
        print(f"    {i+1}. ", candidate)
    confirm = _confirm_yn("Is this correct?")
    if not confirm:
        print("Exiting...")
        sys.exit(1)

    print("Initializing ballots...")
    for i, row in enumerate(reader):
        i += 1 # increment i because we skipped header
        timestamp = row[0] # extract the ballot timestamp

        weight = None
        is_graduating = row[1] # extract answer to "are you graduating?" question
        if is_graduating.startswith("Yes"):
            # Yes, they are fourth years
            weight = config.GRADUATING_VOTE_WEIGHT
        elif is_graduating.startswith("No"):
            weight = Decimal("1.0")
        else:
            print(f"FATAL: found invalid response to 'Are you graduating?' question. Expected something starting with 'Yes' or 'No', but got '{is_graduating}' (row {i})")
            sys.exit(1)

        ballot_choices = []
        for candidate_index, candidate_response in enumerate(row[2:]):
            if candidate_response.lower() == config.NO_PREFERENCE_RESPONSE.lower():
                continue # skip ranking this candidate

            match = ORDINAL_REGEX.findall(candidate_response)
            if len(match) == 0:
                print(f"FATAL: expected response like 'nth choice' but found '{candidate_response}' (row {i})")
            else:
                rank = int(match[0]) # convert their rank to a number
                ballot_choices.append((candidate_index, int(rank)))
        
        # sort ballot choices in ascending order
        ballot_choices.sort(key = lambda x: x[1]) # sort by second entry in tuple - their rank
        # we can now strip out the actual ranks, the ordering is all that matters
        ballot_choices = [x[0] for x in ballot_choices] # just get a list of candidate indices

        new_ballot = ballot.Ballot(timestamp, weight, ballot_choices)

        ballots.append(new_ballot)
    print(f"Created {len(ballots)} ballots.")
    confirm = _confirm_yn("Does this seem alright?")
    if not confirm:
        print("Exiting...")
        sys.exit(1)

print("Beginning ballot counting process...")
print()
remaining_candidates = list(range(len(candidates))) # if we have 3 candidates, this will be [0,1,2], corresponding to each candidate remaining.
count_round = 1
while len(remaining_candidates) > seats:
    print(f"Begin counting votes for round {count_round}...")
    # While there is still competition,
    # ...count the votes.
    votes = { x: Decimal("0") for x in remaining_candidates } # dict comprehension to create a dict of the form { candidate_id : num votes }
    for ballot in ballots:
        # Get the highest-ranked still-remaining candidate.
        for candidate in ballot.rankings:
            # Looking at the highest ranked candidates first,
            # See if they're still remaining.
            if candidate in remaining_candidates:
                # If so, give them a vote.
                votes[candidate] += ballot.weight
                break # And stop voting.
    print(f"Done counting votes for round {count_round}.")
    print("Here are the results:")
    votes_desc = sorted(votes.items(), key=lambda pair: pair[1], reverse=True)
    for i, (candidate_id, nvotes) in enumerate(votes_desc):
        print(f"  {i+1}. {candidates[candidate_id]} with {nvotes} votes.")

    # How many votes did the least popular candidate get?
    least_num_votes = votes_desc[-1][1]
    # Let's see how many candidates have this.
    last_place_candidates = [x for x in remaining_candidates if votes[x] == least_num_votes]

    eliminate = None
    
    if len(last_place_candidates) > 1:
        # Tie for last!
        print(f"There is a {len(last_place_candidates)}-way tie for last place.")
        print("We will choose one to eliminate by random chance.")
        eliminate = rng.choice(last_place_candidates)
    else:
        eliminate = last_place_candidates[0]

    print(f"The candidate chosen for elimination was {candidates[eliminate]}.")
    print("Removing them, and recounting votes...")
    remaining_candidates.remove(eliminate)
    count_round += 1
    if args.pause:
        input("Press enter to continue.")
    print()

print()
print("Done counting!")
print(f"There are {len(remaining_candidates)} winners. They are:")
for candidate_id in remaining_candidates:
    print(f"  ", candidates[candidate_id])