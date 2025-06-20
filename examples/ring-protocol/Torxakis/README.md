# Testing with Torxakis
Run

    torxakis Ring.txs

To run a few steps where both IO are chosen randomly:

    stepper Ring
    step 10

The tester interacts with SUT via sockets. The following Java adapter launches the SUT and communicates with torxakis:

    javac TxsAdapter
    java TxsAdapter 7890

Then inside torxakis command line:

    tester Ring TP Sut
    test 250

# Test Script
These steps are automatized to reproduce the experiments.
The following script executes 50000 runs of tests, each with 250 steps. The output is written to /tmp/o.
The script stops if a violation is found.
    
    ./run_torx.sh