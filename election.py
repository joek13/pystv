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

getcontext().prec = 5  # 5 digits of decimal precision

VERSION_STRING = "1.2"  # Version string.

parser = argparse.ArgumentParser(
    description=f"pystv v{VERSION_STRING} - ballot counter for some Club Running elections",
    epilog="Skyler Moon is a thoughtful guy."
)

# argument for the csv file we'll read in containing all of the votes
parser.add_argument(
    "file",
    metavar="input_file",
    nargs="?",
    help="Google Form election results data to count, stored as a csv."
)

# argument for the office we're running this election on
parser.add_argument(
    "office",
    nargs="?",
    metavar="office",
    choices=offices.OFFICES.keys(),
    help="the office to run an election for. List offices with --list-offices."
)

# flag indicating we should list offices and exit
parser.add_argument(
    "--list-offices",
    action="store_true",
    help="Lists the offices available to run an election for and quits."
)

# flag indicating we should skip all confirm y/n prompts
parser.add_argument(
    "-y",
    action="store_true",
    help="Answers 'yes' to all of the confirmation questions automatically. (Or 'no', when appropriate to make sure no user input is required.) Only use this if you're really confident!"
)

# argument allowing user to set the random seed the program should use
parser.add_argument(
    "--seed",
    action="store",
    default=None,
    type=int,
    help="Optional seed to use for the PRNG in case of a tie. If omitted, the seed will be selected based on system time."
)

# argument that makes us pause ballot counting between rounds
parser.add_argument(
    "--pause",
    # Ryan Torbic suggested that the code was too fast and therefore unlike other ballot counting. This option enhances the realism significantly, and makes you really feel like you are in the great state of Nevada.
    "--ryan-mode",
    action="store_true",
    help="Pauses the ballot counting in between rounds."
)

# allows preemptive elimination for candidates that are out of the race
parser.add_argument(
    "--elim",
    action="store",
    nargs="+",
    metavar="candidate",
    default=None,
    type=int,
    help="The identifiers of the candidates, if any, that should be eliminated preemptively."
)

# is it permissible for a tie in the final round to be broken by chance? default: No.
parser.add_argument(
    "--break-ties",
    action="store_true",
    help="Allows for final-round ties to be settled using random chance."
)

parser.add_argument(
    "--exec-votes",
    action="store",
    metavar="exec-input-file",
    default=None,
    type=str,
    # need to escape the % since argparse is formatting our help string >:(
    # see https://thomas-cokelaer.info/blog/2014/03/python-argparse-issues-with-the-help-argument-typeerror-o-format-a-number-is-required-not-dict/
    help="Path to file containing exec votes. When specified, exec's votes will represent 50%% of the votes."
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
    # if the user hasn't specified a seed, just come up with one randomly
    seed = random.randrange(sys.maxsize)

rng = random.Random(seed)  # initialize an rng using this seed
print(f"(Using random seed {seed})")


if args.file is None:
    print(
        f"FATAL: Input file is requried to run election (try {sys.argv[0]} --help)")
    sys.exit(1)

if args.office is None:
    print(
        f"FATAL: An office is required to run election (try {sys.argv[0]} --help)")
    sys.exit(1)

seats = int(offices.OFFICES[args.office]["num_seats"])
assert isinstance(seats, int)

print(f"Running an election for {args.office}, which has {seats} seat(s) up for election.")


def _confirm_yn(prompt: str, invert_flag: bool = False):
    """
    Helper function for confirm y/n-style prompts.
    Will automatically approve if args.y is set.

    invert_flag : bool := whether to return No when -y is set, instead of yes.
    """
    if args.y:
        # if invert_flag is false, return True. else, return False
        return (not invert_flag)
    else:
        return input(prompt + " [y/n] ") == "y"


# Matches the response part of Google Forms header "Question [Response]"
CANDIDATE_REGEX = re.compile(r"^.+\[(.+)\]$")
# Matches the numeric parts of the ordinal "1st choice", "2nd choice," etc.
ORDINAL_REGEX = re.compile(r"^(\d+)(?:st|nd|rd|th) choice$")

print("Reading election data...")
ballots = []
with open(args.file, "r") as csvfile:
    reader = csv.reader(csvfile)
    # Extract candidate names by looking at the column headers.
    headers = next(reader)
    # 0 - timestamp
    # 1 to n - "Rank your choices" [Candidate Name]
    candidates = []
    print("Detecting candidates...")
    for i, col in enumerate(headers[1:]):  # skip first col
        # find matches for this column w the candidate regex
        match = CANDIDATE_REGEX.findall(col)
        if len(match) == 0:
            print(
                f"FATAL: Failed to extract candidate from header for column {i}.")
            sys.exit(1)
        else:
            candidates.append(match[0])

    print(f"Detected {len(candidates)} candidates:")
    for i, candidate in enumerate(candidates):
        print(f"    {i+1}. ", candidate)
    confirm = _confirm_yn("Is this correct?")
    if not confirm:
        print("Exiting...")
        sys.exit(1)

    print("Initializing ballots...")
    for i, row in enumerate(reader):
        i += 1  # increment i because we skipped header
        timestamp = row[0]  # extract the ballot timestamp

        weight = Decimal("1.0")

        ballot_choices = []  # populate their ballot ranking
        for candidate_index, candidate_response in enumerate(row[1:]):
            # if they specified no preference, then it's no big deal
            if candidate_response.lower() == config.NO_PREFERENCE_RESPONSE.lower():
                continue  # skip ranking this candidate

            match = ORDINAL_REGEX.findall(candidate_response)
            if len(match) == 0:
                # this candidate was not ranked
                # (or there was an error in how the form was processed)
                continue  # skip ranking this candidate
            else:
                rank = int(match[0])  # convert their rank to a number
                # append like (candidate_id, ranking)
                ballot_choices.append((candidate_index, int(rank)))

        # sort ballot choices in ascending order by rank
        # sort by second entry in tuple - their rank
        ballot_choices.sort(key=lambda x: x[1])

        # toDONE: Python sort is stable, so if two candidates A and B are ranked equally, they will always
        # end up receiving votes preferring whoever is listed first on the ballot.
        # Of course, having two candidates ranked "2" is an invalid way to fill out the ballot.
        # But we should prepare for this. Probably should consistently shuffle equally-ranked candidates.

        # Update: it is possible to limit "one response per column" on Google Forms. This will avoid the
        # issue entirely, as these kinds of invalid ballots are impossible to submit.
        # I am leaving the above comment for posterity in case that option is not selected.

        # NB: Let's talk about "funky ballots." There are a few ways we might fill out a ballot to make it
        # "funky:"
        # - Leave it empty (rank no candidates)
        # - Fill it out partially (rank some subset of the candidates)
        # - Fill it out discontinuously (rank candidates 1,2,4 instead of 1,2,3, or any variation_)
        # - Fill it out partiall and discontinuously
        # The code should be able to handle all of these.

        # Empty ballots will never count towards anyone's vote total. There is, however, a warning
        # that tells you *how* many empty ballots there are, because many empty ballots could
        # potentially mean the form is misconfigured. (Real ballots being mistakenly counted as empty.)

        # Partially ranked ballots are also not an issue for a similar reason. A partially ranked
        # ballot will only ever count towards one of the candidates that are included in its rank.

        # Discontinuous ballots are also not an issue. We really care about the *order* of preference
        # rather than the number itself. So, ranking A at 1 and B at 3 is no different than ranking A
        # at 2 and at 4. Or A - 1 and B - 2. We only care that A comes before B ordinally.

        # we can now strip out the actual ranks, the ordering is all that matters
        # just get a list of candidate indices
        ballot_choices = [x[0] for x in ballot_choices]

        # initialize our ballot object
        new_ballot = ballot.Ballot(timestamp, weight, ballot_choices)

        ballots.append(new_ballot)  # add ballot to list
    print(f"Created {len(ballots)} ballots.")
    confirm = _confirm_yn("Does this seem alright?")
    if not confirm:
        print("Exiting...")
        sys.exit(1)

    # check for empty ballots
    empty_ballots = len([x for x in ballots if len(x.rankings) == 0])
    if empty_ballots > 0:
        print(f"WARNING: Detected {empty_ballots} empty ballots.")
        confirm = _confirm_yn("Does this seem alright?")
        if not confirm:
            print("Exiting...")
            sys.exit(1)

# "mass" is the sum of the weights of non-empty ballots
# represents the total voting power of the club, used for computing exec's vote weight
# count of non-empty ballots
real_mass = sum([x.weight for x in ballots if len(x.rankings) > 0])

print(f"Detected a total club 'voting mass' of {real_mass}")

# should we count special exec supervotes?
if args.exec_votes != None:
    print("Reading exec data...")
    # we need to count exec votes
    with open(args.exec_votes, "r") as exec_csv:
        reader = csv.reader(exec_csv)
        # get the headers from the google forms responses
        headers = next(reader)

        exec_candidates = []
        print("Detecting candidates in exec ballot...")
        for i, col in enumerate(headers[1:]):  # skip first col (timestamp)
            match = CANDIDATE_REGEX.findall(col)
            if len(match) == 0:
                print(
                    f"FATAL: Failed to extract candidate from header for column {i + 2}.")
                sys.exit(1)
            else:
                exec_candidates.append(match[0])

        if exec_candidates != candidates:
            print("FATAL: Exec file's candidates do not match input file's candidates")
            sys.exit(1)

        exec_ballots = []
        for i, row in enumerate(reader):
            i += 1  # increment i because we skipped the header
            timestamp = row[0]  # extract the ballot timestamp

            ballot_choices = []  # populate their ballot ranking
            for candidate_index, candidate_response in enumerate(row[1:]):
                # if they specified no preference, then it's no big deal
                if candidate_response.lower() == config.NO_PREFERENCE_RESPONSE.lower():
                    continue  # skip ranking this candidate

                match = ORDINAL_REGEX.findall(candidate_response)
                if len(match) == 0:
                    # this candidate was not ranked
                    # (or there was an error in how the form was processed)
                    continue  # skip ranking this candidate
                else:
                    rank = int(match[0])  # convert their rank to a number
                    # append like (candidate_id, ranking)
                    ballot_choices.append((candidate_index, int(rank)))

            # sort ballot choices in ascending order by rank
            # sort by second entry in tuple - their rank
            ballot_choices.sort(key=lambda x: x[1])

            # we can now strip out the actual ranks, the ordering is all that matters
            # just get a list of candidate indices
            ballot_choices = [x[0] for x in ballot_choices]

            # NOTE: temporarily setting ballot weight to 0.0, as we need to calculate later
            # initialize our ballot object
            new_ballot = ballot.Ballot(timestamp, 0.0, ballot_choices)

            # add to list of exec ballots
            exec_ballots.append(new_ballot)

        print(f"Created {len(exec_ballots)} exec superballots.")
        confirm = _confirm_yn("Does this seem alright?")
        if not confirm:
            print("Exiting...")
            sys.exit(1)

        empty_exec_ballots = len([x for x in ballots if len(x.rankings) == 0])
        if empty_exec_ballots > 0:
            print(
                f"WARNING: Detected {empty_exec_ballots} empty exec ballots.")
            confirm = _confirm_yn("Does this seem alright?")
            if not confirm:
                print("Exiting...")
                sys.exit(1)

        print("Calculating exec vote weight...")
        # calculate the "boost" exec votes should get
        # if we have k exec votes and "regular" vote mass of n, then exec gets
        # a weight of n / k. That way, the total mass of exec votes
        # is equal to that of the club.
        exec_votes = Decimal(len(exec_ballots))
        exec_weight = real_mass / exec_votes
        print(f"Calculated exec vote weight of {exec_weight}")

        for exec_ballot in exec_ballots:
            exec_ballot.weight = exec_weight

        exec_mass = sum([x.weight for x in exec_ballots])
        print(f"Exec votes have mass of {exec_mass}.")

        # add exec votes to general pool
        ballots = ballots + exec_ballots

to_eliminate = args.elim if args.elim is not None else []

# check if any candidates need to be preemptively eliminated.
# context: in Club Running electoral process, the races happen in
# a defined order. If someone is running in two races,
# and they win the earlier race, they are automatically
# withdrawn from subsequent races.
if args.elim is None:
    eliminate = _confirm_yn(
        "Do any candidates need to be eliminated?", invert_flag=True)
    if eliminate:
        candidate_indices = input("Enter their numbers: ")
        candidate_indices = [x.strip() for x in candidate_indices.split(",")]
        for candidate_index in candidate_indices:
            candidate_index = int(candidate_index) - 1
            to_eliminate.append(candidate_index)
        print("Candidates to be eliminated:")
        for i in to_eliminate:
            print(f"    - {candidates[i]}")
        confirm_elim = _confirm_yn("Is this correct?")
        if not confirm_elim:
            print("Exiting...")
            sys.exit(1)
else:
    to_eliminate = [x - 1 for x in args.elim]  # 1-indexed
    print("Candidates to be eliminated:")
    for i in to_eliminate:
        print(f"    - {candidates[i]}")
    confirm_elim = _confirm_yn("Is this correct?")
    if not confirm_elim:
        print("Exiting...")
        sys.exit(1)

print("Beginning ballot counting process...")
print()
# if we have 3 candidates, this will be [0,1,2], corresponding to each candidate remaining.
remaining_candidates = set(range(len(candidates))) - set(to_eliminate)
count_round = 1
while len(remaining_candidates) > seats:
    print(f"Begin counting votes for round {count_round}...")
    # While there is still competition,
    # ...count the votes.
    # dict comprehension to create a dict of the form { candidate_id : num votes }
    votes = {x: Decimal("0.0") for x in remaining_candidates}
    for ballot in ballots:
        # Get the highest-ranked still-remaining candidate.
        for candidate in ballot.rankings:
            # Looking at the highest ranked candidates first,
            # See if they're still remaining.
            if candidate in remaining_candidates:
                # If so, give them a vote.
                votes[candidate] += ballot.weight
                break  # And stop voting.
    print(f"Done counting votes for round {count_round}.")
    print("Here are the results:")
    votes_desc = sorted(votes.items(), key=lambda pair: pair[1], reverse=True)
    for i, (candidate_id, nvotes) in enumerate(votes_desc):
        print(f"  {i+1}. {candidates[candidate_id]} with {nvotes} votes.")

    # How many votes did the least popular candidate get?
    least_num_votes = votes_desc[-1][1]
    # Let's see how many candidates have this.
    last_place_candidates = [
        x for x in remaining_candidates if votes[x] == least_num_votes]

    eliminate = None

    if len(last_place_candidates) > 1:
        # Tie for last!
        print(
            f"There is a {len(last_place_candidates)}-way tie for last place.")
        # if there are more than (num_seats+1) candidates left, just break by chance.
        # alternatively, always break by chance if user specified.
        # basically, it's undesirable to have a final round decided by chance.
        if len(remaining_candidates) > (seats + 1) or args.break_ties:
            print("We will choose one to eliminate by random chance.")
            eliminate = rng.choice(last_place_candidates)
        else:
            # uh oh!
            # breaking ties is disabled.
            # and the last round has a tie.
            print()
            print("!!! THE ELECTION ENDED IN A TIE. !!!")
            print(
                "  (Because --break-ties is not set, there is no way to resolve this tie.)")
            print("The count stands as follows:")
            # print the count
            for i, (candidate_id, nvotes) in enumerate(votes_desc):
                print(
                    f"  {i+1}. {candidates[candidate_id]} with {nvotes} votes.")

            # no more counting
            break
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

# only print winners if we didn't end in a tie
if len(remaining_candidates) <= seats:
    print(f"There are {len(remaining_candidates)} winner(s). They are:")
    for candidate_id in remaining_candidates:
        print(f"  ", candidates[candidate_id])

    print(f"Congratulations to our new {args.office}(s)!")

print()
print("Reproducibility:")
print("You should be able to reproduce these election results by running:")

to_eliminate_disp = [str(x + 1)
                     for x in to_eliminate]  # make to_eliminate 1-indexed
# don't show --elim flag if no one was eliminated
elim_disp = f"--elim {' '.join(to_eliminate_disp)}" if len(
    to_eliminate) > 0 else ""

exec_disp = f"--exec-votes \"{args.exec_votes}\"" if args.exec_votes != None else ""

print(
    f"    python {sys.argv[0]} -y --seed {seed} \"{args.file}\" {args.office} {elim_disp} {exec_disp}")
print()
