#!/usr/bin/python3
import sys

"""
    A simple ring topology trying to elect a leader.
    The process with the lower ID send its id to its clockwise neighbor.
    At each step, an input determines if the network is 'reset' (starting over),
    if some sent messages is 'loss' or not.
    In case loss is true, the network does not make progress.
    The state shows how many processes have been stabilized so far.
    The output 'stable' is true iff a leader was elected.

    python ring.py
    -- Step 0 (initial)
    State: 1
    reset:false
    loss:false
    -- Step 1
    State: 2
    reset:false
    loss:true
    -- Step 3
    State: 2
    reset:true
    loss:false
    -- Step 4
    State: 1
    ...
"""

class Ring:
    def __init__(self, n : int):
        assert(n >= 2)
        self.n: int = n
        self.prg : int= 0
        self.leaders :list[int] = [0] * n
        self.reset()
        self.input_reset : bool = False
        self.input_loss : bool = False
        self.output_stable : bool = False

    def reset(self):
        self.leaders = [i for i in range(self.n)]
        self.leaders[0] = 0
        self.prg = 0

    def bool_to_str(self, b):
        if b:
            return "true"
        else:
            return "false"

    def print_state(self) -> None:
        # print(f"{self.leaders} (prg: {self.prg} vs {self.n-1})")
        print(f"{self.leaders}")
        sys.stdout.flush()

    def print_output(self):
        print(f"stable:{self.bool_to_str(self.output_stable)}")
        sys.stdout.flush()

    def print_input(self) -> None:
        print(f"reset:{self.bool_to_str(self.input_reset)} loss:{self.bool_to_str(self.input_loss)}")
        sys.stdout.flush()

    def read_input(self) -> None:
        line = sys.stdin.readline()
        val = dict(map(lambda a: list(map(lambda s: s.strip(), a.split(":"))), line.split(" ")))
        self.input_reset = val["reset"] == 'true'
        self.input_loss = val["loss"] == 'true'

    def select_output(self) -> None:
        self.output_stable = all(map(lambda x : x == 0, self.leaders))

    def update_state(self) -> None:
        if self.input_reset:
            self.reset()
        elif self.input_loss:
            pass
        else:
            new_leaders: list[int] = [min(i, self.leaders[i-1 if i > 0 else self.n-1]) for i in range(self.n)]
            self.leaders = new_leaders
            self.prg += 1

    def run(self):
        # Print initial state
        step = 0
        print(f"-- Step {step} (initial)")
        sys.stdout.flush()
        self.print_state()
        while True:
            self.read_input()
            self.select_output()
            self.update_state()
            self.print_output()
            step += 1
            print(f"-- Step {step}")
            sys.stdout.flush()
            self.print_state()

ring = Ring(8)
ring.run()