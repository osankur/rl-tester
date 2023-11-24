#!/usr/bin/python3
import sys
import re

"""
    A reactive system encoding a robot moving in a passageway. The inputs are Booleans iup, iright determining the
    next cell to move to, while to outputs are Booleans open, doorstep, fault, z0, ..., z9.
    This case study is described in the paper.

    Example execution:

    python passageway.py
    -- Step 0 (initial)
    State: x:0 y:2.0 state:0
    iup:false iright:false
    doorstep:false open:false fault:true zone0:true zone1:false zone2:false zone3:false zone4:false zone5:false zone6:false zone7:false zone8:false zone9:false
    -- Step 1
    State: x:0 y:1.0 state:0
    iup:true iright:true
    doorstep:false open:false fault:true zone0:true zone1:false zone2:false zone3:false zone4:false zone5:false zone6:false zone7:false zone8:false zone9:false
    -- Step 2
    State: x:1 y:2.0 state:0
"""


class Corridor:

    def __init__(self):
        # self.k = 8
        self.k = 4
        self.x = 0
        self.y = self.k/2
        # 0: up, 1: down
        # 0: left, 1: right
        self.iup = None
        self.iright = None


        self.state = 0
        self.doorstep = False
        self.open = False
        # number of consecutive steps where input was up
        self.nb_rooms = 10
        self.zone = [False] * self.nb_rooms
        self.fault = False

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
        #zones = ' '.join([f"zone{i}:{self.bool_to_str(self.zone[i])}" for i in range(1,len(self.zone))])
        print(f"State: x:{(self.x)} y:{self.y} state:{self.state}")
        sys.stdout.flush()

    def print_output(self):
        zones = f"doorstep:{self.bool_to_str(self.doorstep)} open:{self.bool_to_str(self.open)} fault:{self.bool_to_str(self.fault)} " + ' '.join([f"zone{i}:{self.bool_to_str(self.zone[i])}" for i in range(0,len(self.zone))])
        #print(f"oupdown:{self.bool_to_str(self.oupdown)} oleftright:{self.bool_to_str(self.oleftright)} {zones}")
        print(f"{zones}")
        sys.stdout.flush()

    def print_input(self):
        print(
            f"iup:{self.bool_to_str(self.iup)} iright:{self.bool_to_str(self.iright)}")
        sys.stdout.flush()

    def read_input(self):
        line = sys.stdin.readline()
        val = dict(
            map(lambda a: list(map(lambda s: s.strip(), a.split(":"))), line.split(" ")))
        self.iup = self.str_to_bool(val["iup"])
        self.iright = self.str_to_bool(val["iright"])

    def select_output(self):
        x = self.x
        y = self.y
        self.open = y == 0
        self.doorstep = (x % self.k) == self.k-1
        for i in range(self.nb_rooms):
            self.zone[i] = x >= i * self.k and x < (i+1)*self.k

    def update_state(self):
        dx = (1 if self.iright else -1)
        dy = (1 if self.iup else -1)

        # introduce bug: refuse to move right at open /\ doorstep in the room 8
        if self.zone[8] and (self.x % self.k) == self.k-1 and self.y == 0:
            if dx > 0:
                dx = 0
        # collisions are forbidden except when y == 0
        if (self.x + dx < 0 or self.x + dx >= self.nb_rooms * self.k 
                or self.y + dy >= self.k or self.y+dy < 0):
            self.fault = True

        # We cannot cross closed doors:
        if dx == 1 and (self.x % self.k) == self.k-1 and self.y > 0:
            dx = 0
        # if we are crossing, then reset y
        if dx == 1 and (self.x % self.k) == self.k-1 and self.y == 0:
            self.y = self.k -1
        else:
            self.y = self.y + dy
        self.x = self.x + dx
        # We cannot cross walls:
        if (self.x < 0):
            self.x = 0            
        if (self.x >= self.nb_rooms * self.k):
            self.x = self.x - 1
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
            self.update_state()
            self.select_output()
            self.print_output()
            step += 1
            print(f"-- Step {step}")
            sys.stdout.flush()
            self.print_state()

    def parse_input(self, msg):
        pat = ".*putVal\((.*),(.*)\).*"
        r = re.compile(pat)
        m = r.match(msg)
        assert(m is not None)
        self.iup = m.group(1).strip() == "True"
        self.iright = m.group(2).strip() == "True"

    def encode_output(self):
      # OutputVal {open, doorstep, fault, zone :: Int }
      o = 1 if self.open else 0
      ds= 1 if self.doorstep else 0
      f = 1 if self.fault else 0
      z = min(map(lambda x: x[0], filter(lambda x: x[1], enumerate(self.zone))))
      return f"OutputVal({o},{ds},{f},{z})"

    def run_socket(self):
        step = 0
        while True:
            self.parse_input(sys.stdin.readline())
            self.update_state()
            self.select_output()
            print(self.encode_output())
            self.print_state()
            step += 1
            sys.stdout.flush()

maze = Corridor()
if len(sys.argv) >= 2 and sys.argv[1] == "-s":
    maze.run_socket()
else:
    maze.run()
