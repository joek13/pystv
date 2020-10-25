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