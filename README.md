# pystv
A simple Python implementation of Single-Transferable Vote, a kind of ranked choice voting system.
This system was developed by [Joe Kerrigan](https://github.com/joek13) for [Club Running](http://virginia.clubrunning.org)'s Fall 2020 elections.

### Using the tool
The ballot counter expects its inputs to follow a specific form. The Google form should have one question asking if voters are graduating in the next term (so we can appropriately reweight their votes), followed by a "Multiple Choice Grid" question. The rows of the grid are the candidates' names, and the columns are their rankings. A sample input `.csv` file for an election with only a single ballot cast looks like this:

```csv
Timestamp,ON YOUR HONOR: Do you intend to graduate at the end of Spring 2021?,Rank your choices for the office of Meet Coordinator. [Galen Rupp],Rank your choices for the office of Meet Coordinator. [Cav Man],Rank your choices for the office of Meet Coordinator. [Jim Ryan],Rank your choices for the office of Meet Coordinator. [Allen Groves],Rank your choices for the office of Meet Coordinator. [Ms. Cathy],Rank your choices for the office of Meet Coordinator. [Liz Magill]
10/23/2020 16:35:24,"Yes, I intend to graduate at the end of the Spring 2021 term.",6th choice,1st choice,3rd choice,2nd choice,4th choice,5th choice
```

To run an election for the office of meet coordinator, run the following command:
```
$ python election.py ./responses.csv meet_coordinator
```
### The algorithm
The algorithm is a simple implementation of the single-transferable vote, a kind of ranked choice voting scheme. The scheme has been modified to meet specific club needs and historical election minutiae.

Here's the general run-down of the algorithm:
1. **Parse command-line inputs.** This is done by Python's `argparse` module. You can run the script with `--help` to get a rundown of all of the options.
2. **Initialize the random number generator.** Occasionally, (such as in the case of a tie), random chance is required to run this algorithm. Because results should be reproducible, a seed is used. If no seed is specified with the `--seed` command line option, then one is generated at random. (The random seed is printed for reproducibility.)
3. **Read the office.** The algorithm checks the `office` command line argument, and verifies it against the offices defined in `offices.py`. `offices.py` lists the available offices, the number of seats each office has openings for, and how votes are weighted from graduating members.
4. **Begin reading ballots.** First, the program tries to extract which candidates are on the ballot by reading the headers. For the "multiple choice grid" that Google Forms uses, there is one header column per candidate. (See the sample input file above.) Each column is read, and candidates are extracted by matching the header with a regular expression. As a sanity check, the candidates' names are printed out and the user is prompted to verify them (unless `-y` is set).
5. **Build ballot objects.** Each row of the input file is read, and a `Ballot` object is initialized based on the data. The timestamp is pulled. The "are you graduating" question is converted to a boolean based on whether the voter selected "Yes" or "No." Their answer is used to assign the ballot a weight, usually 1.0 or 0.5 (in cases where graduating members get half a vote). Finally, the candidates are processed. An "ordinal" regular expression is used to turn answers like "5th choice" (which Google Forms outputs) into ranks, like the integer 5. Candidates are sorted by their rank and put into an array where the first candidate is this voters' most preferred and the last candidate is this voters' least preferred. At this point, we discard the actual ranks. The only thing that matters is the relative ordering of candidates on an individual ballot, from "most preferred" to "least preferred." (In this way, ranking candidate A 1st and candidate C 3rd is no different than ranking A 1st and C 2nd.) The ballot is stored in an array.
6. **Sanity-check the ballots.** A few sanity checks are performed: how many ballots were created? How many of them are empty (i.e., rank no candidates)? The "mass" of these ballots are printed, which is exactly the sum of the weights of each ballot. Mass can be understood as a kind of stand-in for voting power.
7. **If applicable, read exec's votes.** For the position of President, club election procedure dictates that exec gets "50% of the vote." Exec votes are counted separately in a different file. They are converted to ballot objects just like with regular ballots, except that their weight is deliberately left unset because it must be calculated later. (As a sanity check, the program aborts if the specific candidates on the exec ballot are smoehow different than the club's ballot.)
8. **If applicable, calculate the weight of each exec vote.** To give exec a voting power equal to the rest of the club, we have to do some simple math. If the voting mass of the club is `n`, and there are `k` exec ballots, each exec ballot should have a weight of `n / k`. That way, the total mass of exec's votes equals exactly the total voting mass of the club. Once calculated, this mass is applied to every exec ballot.
9. **If applicable, perform sanity checks on exec's ballots.** This includes printing and prompting the number of ballots, the number of empty ballots, and the total mass of exec votes. (Remember that the mass of exec votes should be exactly equal to the mass of the club's votes.)
10. **Perform any preemptive eliminations.** In Club Running elections, each office is elected in a prescribed order. If someone wins an election, they have to be eliminated from any successive elections they're running in. Candidates are specified for elimination, either by a yes/no prompt or the `--elim` command line option.
11. **Count the votes.** Vote counting is an iterative process. Here's how it works:
    - Initialize a list of viable candidates. Initially, this is all of the candidates minus those who have been preemptively eliminated.
    - While there are more viable candidates than seats available:
        - Initialize a table of votes for each candidate. Votes are re-counted every round.
        - Iterate through each ballot. For each ballot, find the highest-ranked still-viable candidate. Give that candidate a vote worth this ballot's weight.
            - If this ballot ranked no viable candidates, its vote goes to no one.
        - Find whichever candidate has the fewest votes this round and eliminate them (remove them from the list of viable candidates).
            - If two or more candidates tie for fewest votes, pick one to eliminate pseudorandomly (using the above RNG).
                - ...unless this is the final round of voting, in which case it is generally considered undesirable to allow random chance to choose between two equally favored candidates.
                - In this case, simply halt and print out the candidates who tied. (Unless `--break-ties` is set, in which case this tie is resolved by chance like any other,  non-final tie.)
    - Print out the remaining candidates, they are the winners.
12. **Print out reproducibility information.** Print out a command that, when run, should produce identical results. This is achieved by using the same random seed and input arguments.