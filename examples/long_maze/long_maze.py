#!/usr/bin/python3
import sys


class Maze:
    """
    Robot moving in a 50x50 maze with initial state at (x=0,y=25).
    """

    def __init__(self):
        self.k = 25
        #self.d = 20
        self.x = 0
        self.y = self.k/2
        # 0: up, 1: down
        # 0: left, 1: right
        self.iupdown = None
        self.ileftright = None

        # self.oupdown = None
        # self.oleftright = None

        self.zone = [False] * 7

        self.state = 0
        # number of consecutive steps where input was up
        # self.nb_of_iups = 0
        # self.nb_of_irights = 0

    def bool_to_str(self, b):
        if b:
            return "true"
        else:
            return "false"

    def str_to_bool(self, str):
        if str == "true":
            return True
        elif str == "false":
            return False
        raise Exception(f"Cannot parse bool {str}")

    def print_state(self):
        zones = ' '.join([f"zone{i}:{self.bool_to_str(self.zone[i])}" for i in range(1,len(self.zone))])
        print(f"State: x:{(self.x)} y:{self.y} state:{self.state} {zones}")
        sys.stdout.flush()

    def print_output(self):
        zones = ' '.join([f"zone{i}:{self.bool_to_str(self.zone[i])}" for i in range(1,len(self.zone))])
        #print(f"oupdown:{self.bool_to_str(self.oupdown)} oleftright:{self.bool_to_str(self.oleftright)} {zones}")
        print(f"{zones}")
        sys.stdout.flush()

    def print_input(self):
        print(
            f"iupdown:{self.bool_to_str(self.iupdown)} ileftright:{self.bool_to_str(self.ileftright)}")
        sys.stdout.flush()

    def read_input(self):
        line = sys.stdin.readline()
        val = dict(
            map(lambda a: list(map(lambda s: s.strip(), a.split(":"))), line.split(" ")))
        self.iupdown = self.str_to_bool(val["iupdown"])
        self.ileftright = self.str_to_bool(val["ileftright"])

    def select_output(self):
        """
            Go right unless agent has been going right for more than 3 steps
            Gp up unless agent has been going up for more than 3 steps
        """
        x = self.x
        y = self.y
        #
        # |6|   |
        # | |1|2|
        # |5|4|3|
        #
        d = self.k / 3
        self.zone[6] = x < d and y >= 2*d

        self.zone[1] = x >= d   and x < 2*d   and y >= d and y < 2*d
        self.zone[2] = x >= 2*d and x < 3*d and y >= d and y < 2*d

        self.zone[5] = x < d and y < d
        self.zone[4] = x >= d   and x < 2*d and y < d
        self.zone[3] = x >= 2*d and x < 3*d and y < d


    def update_state(self):
        dx = (1 if self.ileftright else -1)
        dy = (-1 if self.iupdown else 1)
        self.x = self.x + dx
        self.y = self.y + dy
        if (self.x < 0):
            self.x = 0
        if (self.x >= self.k):
            self.x = self.k-1
        if (self.y < 0):
            self.y = 0
        if (self.y >= self.k):
            self.y = self.k-1

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
