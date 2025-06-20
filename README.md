# Black-Box Testing w.r.t. Automata Requirements using Reinforcement Learning
This tool tests black-box reactive systems with Boolean input/output variables w.r.t. requirements given in Verilog.
These systems under test (SUT) receive a valuation, and answers immediately by an output valuation, and repeat this infinitely. There are examples in the `examples` directry.

Requirements are expressed as Verilog modules which are seen as finite-state machines which accept sequences of input / output valuations. 
We use the following encoding. All input and outputs to the SUT must be inputs of the Verilog module with the following convention:
each input v of the SUT is named `v`, and each output v of the SUT is named `controllable_v`.

The directory `examples/maze/` contains two requirements and two implementations of a simple program guiding a robot in a 5x5 maze.
Moreover, positions (4,0), (4,1), (4,2), (4,3) are sink states. (4,4) is not.
Here, `updown` is an input (false means up; true means down), and `leftright` is an output (false means left; true means right).

Run `examples/maze/maze.py` to try the program. When prompted for input, write `updown:true` or `updown:false` and press enter.

The requirements file `examples/maze/maze_req.v` is a Verilog module with inputs `updown`, `controllable_leftright`.
Furthermore, it has an output `objective` which is 1 iff the sequence read so far satisfies the tst objective; and an output `error`
which is 1 iff the sequence is a violation of the requirement. Here, `maze_req.v` raises an error when the robot enters position (2,2) (which means collision with an obstacle), 
and defines the objective of reaching a position with x=2. `maze_req2.v` raises an error at position (4,4) and has the objective of reaching (4,4).

Testing is done in two phases: 1) Offline computation of test strategies 2) Online testing, which are detailed below.

# Installation
## Manual installation
This program is written in Python 3. We use the following libraries and external programs.

The following two Python packages are needed
- [py-aiger](https://github.com/mvcisback/py-aiger)
- [`dd`](https://pypi.org/project/dd/)

and can be installed by

        pip3 install -r requirements.txt

- A custom [version](https://github.com/osankur/abssynthe/tree/reach_synth) of the [Abssynthe](https://github.com/gaperez64/AbsSynthe/) game solver.
You can clone with:

        git clone -b reach_synt git@github.com:osankur/abssynthe.git

and follow compilation instructions. The binary executable `abssynthe` must be on path.

- A custom [version](https://github.com/osankur/aiger) of the [Aiger library](https://github.com/arminbiere/aiger). The `scripts` directory also contains a modified copy of one of the aiger modules.

        git clone git@github.com:osankur/aiger.git

The executables must be on path.

- Executables of [yosys](https://github.com/YosysHQ/yosys) and [berkeley-abc](https://github.com/berkeley-abc/abc) which can be installed by cloning these repositories or using a package manager.

Once these are installed, run `make` in this directory. This will compile some scripts in the `scripts` directory.

## Automatic Installation / Artifact
The script `artifact/install-packages.sh` installs all requirements and sets environment variables for an Ubuntu system (tested on 20.04 and 22.04).
For other distributions, you just need to change the `apt` command. The program just needs executables of yosys and berkeley-abc.

If you don't have a matching system or if the above script fails, you can use a Ubuntu VM. Download the following image from TACAS23 to run this program in a virtual machine with Oracle VirtualBox:

https://zenodo.org/record/7113223#.Y4oKBDPMLMM

The image contains Ubuntu 22.04 LTS. The username and password is tacas23.
Then `artifact/install-packages.sh` will successfully install all dependencies.

# Testing

## 1. Offline computation of test strategies
The script `test_generator.py` takes as argument a list of requirements given as Verilog modules,
combines them into one requirement state machine, analyzes it, and produces information for the testing phase.

Here is the interpretation of the outputs:
- any output that contains "error" in its name is an error monitor 
- any output that contains "objective" in its name is a test objective (i.e. defines a coverage criterion)
There can be several such outputs in each Verilog module.

The program produces a separate test strategy file for each objective. One of these files is to be used in the online testing phase
according to the test objective.

For example, one can run

```
python test_generator.py -r examples/maze/maze_req.v examples/maze/maze_req2.v -o examples/maze/
INFO:root:Found following error monitors: {'maze_req_error', 'maze_req2_error'}
INFO:root:Found following test objectives: {'maze_req2_objective', 'maze_req_objective'}
DEBUG:root:Product written to /tmp/all_reqs.aag
INFO:root:Synthesizing strategy for maze_req2_objective...
INFO:root:Successful. Test strategy written to examples/maze/teststrategy_maze_req2_objective.aag
INFO:root:Synthesizing strategy for maze_req_objective...
INFO:root:Successful. Test strategy written to examples/maze/teststrategy_maze_req_objective.aag
```
The program displays the errors and objectives found in the two Verilog requirements file, and produced the two test strategies, one for each objective.
Each test strategy file can be used for online testing and will guide the test towards that objective, while errors from all requirement files are always monitored.


## 2. Online Testing
The script `tester.py` tests a given SUT using a test strategy computed as above.

There are three test algorithms detailed in the paper.
- uniform: input valuations are chosen uniformly at random
- greedy: input valuations are restricted to greedy inputs. If epsilon is set, then at each step, run uniform with probability epsilon, and run greedy otherwise.
- mcts: The MCTS algorithm with the greedy heuristic

The `--max-steps` option bounds the number of input-output steps of each execution. 

The `-r` option sets the number of runs, that is, the number of executions to be made.

The `-tpgb` option sets, for the MCTS algorithm, the number of steps during which the tree policy is greedy at each node.

The `-rs` option sets whether to use greedy or uniform rollout policy in MCTS.

### Example
The `examples/maze/` directory contains two examples: `maze.py` is a correct implementation for `maze_req.v` (it never enters (2,2)),
while `maze_fault.py` is an incorrect one. Both implementations violate `maze_req2.v`.

To run tests with the test objective defined by `maze_req.v`, run:

    python3 tester.py -e greedy --epsilon 25 -i examples/maze/maze.py -s examples/maze/teststrategy_maze_req_objective.aag
****
This applies the epsilon-greedy strategy with epsilon=0.25.
This will print the generated trace and end with "Objective reached: maze_req_objective".
In fact, the requirement contains the output 'objective', which was renamed as 'maze_req_objective'.

The trace currently shows the positions of the robot in human readable format (x,y). This is ad hoc and for demonstration only. It will be removed or replaced with a custom Python module to visualize traces.

To check `maze_req2.v`, run

    python3 tester.py -e greedy --epsilon 25 -i examples/maze/maze.py -s examples/maze/teststrategy_maze_req2_objective.aag

This will identify a trace leading to an error, so the output ends with "Requirement violation: State satisfies maze_req2_error".
In fact, the requirement contains the output 'error', which was renamed as 'maze_req2_error'.

Each run generates a possibly different trace due to randomization.

To check `maze_faulty.py`, run

    python3 tester.py -e greedy --epsilon 25 -i examples/maze/maze_faulty.py -s examples/maze/teststrategy_maze_req_objective.aag
    python3 tester.py -e greedy --epsilon 25 -i examples/maze/maze_faulty.py -s examples/maze/teststrategy_maze_req2_objective.aag

Both ends with a violation of one of the two monitors. Note that the second one can also end with the violation of
'maze_req_error' since in all cases the tester monitors for all errors and stops at the first one.

# License
This is distributed under the 3-Clause BSD License (see [LICENSE](LICENSE)).