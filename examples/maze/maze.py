#!/usr/bin/python3
import sys

"""
    A simple reactive system encoding a robot moving in a maze. The input is the Boolean updown,
    and the output is controllable_leftright, which together determine the position in which the robot moves.
    Try:

    python maze.py
    -- Step 0 (initial)
    State: x:0 y:2
    updown:false
    leftright:true
    -- Step 1
    State: x:1 y:3
    updown:true
    leftright:false
    -- Step 2
    State: x:0 y:2
    ...
"""

class Maze:
    """
    Robot moving in a 5x5 maze with initial state at (x=0,y=2).
    The robot idles at edges if forced to move towards walls.
    There is an obstacle at (2,2) which the robot must not cross.
    The user input determines whether it mvoes up (0) or down (1)
    The robot (program) itself determines left (0) or right (1).
    It thus moves diagonally at each step.
    """
    def __init__(self):
        self.x = 0
        self.y = 2
        self.k = 5
        # 0: up, 1: down
        self.input = None

        # 0: left, 1: right
        self.output = None

    def bool_to_str(self, b):
        if b:
            return "true"
        else:
            return "false"

    def print_state(self):
        print(f"State: x:{(self.x)} y:{self.y}")
        sys.stdout.flush()

    def print_output(self):
        print(f"leftright:{self.bool_to_str(self.output)}")
        sys.stdout.flush()

    def print_input(self):
        print(f"updown:{self.bool_to_str(self.input)}")
        sys.stdout.flush()

    def read_input(self):
        line = sys.stdin.readline()
        val = dict(map(lambda a: list(map(lambda s: s.strip(), a.split(":"))), line.split(" ")))
        if val["updown"] == 'false':
            self.input = False
        else:
            self.input = True

    def select_output(self):
        """
            Go right unless 1) x == k-1 or 2) we would hit the obstacle
        """
        x = self.x
        y = self.y
        if (x == 1 and y == 1 and self.input == 0):
            self.output = False
        elif (x == 1 and y == 3 and self.input == 1):
            self.output = False
        elif (x < self.k-1):
            self.output = True
        else:
            self.output = False

    def update_state(self):
        #print(f"input:{self.input}, output:{self.output}")
        # absorbing states:
        if (self.x == self.k - 1 and self.y < self.k-1):
            return
        if (not self.input and self.y < self.k-1):
            self.y += 1
        elif (self.input and self.y > 0):
            self.y -= 1
        
        if (not self.output and self.x > 0):
            self.x -= 1
        elif (self.output and self.x < self.k-1):
            self.x += 1

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


maze = Maze()
maze.run()