import logging
import random
import argparse
import subprocess
import gc 
import cProfile
import queue
import time
import aiger
import re
import sys
from common import *
import mcts 

class BlackBoxProgram:
    """
    Interface for executing step by step a reactive program
    """
    def __init__(self, exec_file):
        self.exec_file = exec_file
        self.proc = None
        self.history = []

    def restart(self):
        """
        Restart the program
        """
        if (self.proc is not None):
            self.proc.stdin.close()
            self.proc.stdout.close()
            self.proc.terminate()

        self.history=[]
        self.proc = subprocess.Popen([self.exec_file],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

        _ = self.proc.stdout.readline()
        _ = self.proc.stdout.readline()

    def  __read_step(self):
        # Read state and output
        count = 0 # 0: output 1: step number 2: state
        preamble = None
        state = None
        output = None
        while(count <= 2):
            try:
                line = self.proc.stdout.readline()
                if (count == 0):
                    output = line
                elif (count == 1):
                    preamble = line
                elif (count == 2):
                    state = line
                count += 1
            except queue.Empty:
                time.sleep(0.1)
        return (output, preamble, state)

    
    def next(self, inp):
        """
        @return get next output given input. None if program stopped.
        """
        input_str = " ".join([f"{k}:{'true' if v else 'false'}" for (k,v) in inp.items()])+"\n"
        # feed input
        self.proc.stdin.write(input_str.encode("utf-8"))
        self.proc.stdin.flush()

        (output_str, stepno, state_str) = self.__read_step()

        self.history.append(input_str.strip())
        self.history.append(output_str.decode("utf-8").strip())
        self.history.append(stepno)
        self.history.append(state_str.decode("utf-8").strip())
        y = list(map(lambda x: x.split(":"), filter(lambda s: len(s)>0, output_str.decode("utf-8").strip().split(" "))))
        for (l,v) in y:
            if v not in ["false","true"]:
                raise Exception(f"Unrecognized Boolean value output by program: {v}")
        output = dict(map(lambda x: (x[0], x[1] == "true"), y))
        
        return output, state_str

    def terminate(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=0.2)
            logging.info(f'== subprocess exited with rc ={self.proc.returncode}')
        except subprocess.TimeoutExpired:
            logging.warning('subprocess did not terminate in time')
        #self.t.join()
        self.proc = None

    def get_history(self):
        return self.history
    def print_history(self):
        for (i,s) in enumerate(self.history):
            if (i%4) == 0:
                print(f"{(i//4)+1}. ")
            if (i%4) == 0:
                print("Input: ", end="")
            if (i%4) == 1:
                print("Output: ", end="")
            if (i%4) == 3:
                print("State: ", end="")
            if (i % 4) != 2:
                print(f"{s}")

class InconclusiveRun(Exception):
    pass

class RandomTester:
    def __init__(self, strat_file : str, impl : str, epsilon : int, verbose : bool):
        self.verbose = verbose
        self.epsilon = epsilon
        self.strat_file = strat_file
        self.strat = aiger.load(strat_file)
        self.man = BDD() 
        self.reqs_sim = self.strat.simulator()
        # Names of the inputs to program - Uncontrollable inputs for Abssynthe
        self.Xu = set()
        # Outputs of the program - Controllable inputs for Abssynthe
        self.Xc = set()
        # BDD cubes for inputs
        self.cinput_vars = []
        self.uinput_vars = []
        self.latch_vars = []
        self.cinput_cube = self.man.true
        self.uinput_cube = self.man.true
        # self.latches_cube = self.man.true
        self.input_history = []

        # Number of steps done in the current round
        self.step = None
        self.total_steps = 0

        for v in self.strat.inputs:
            self.man.declare(v)
            if v.startswith("controllable_"):
                self.cinput_vars.append(v)
                self.cinput_cube &= self.man.var(v)
            else:
                self.uinput_vars.append(v)
                self.uinput_cube &= self.man.var(v)
        for v in self.strat.latches:
            self.man.declare(v)
            self.latch_vars.append(v)

        for v in self.strat.inputs:
            if v.startswith("controllable_"):
                outp = v.replace("controllable_","")
                self.Xc.add(outp)
            else:
                self.Xu.add(v)
        self.Xu_noclk = self.Xu - set(["clk"])

        # BDDs of the next-state functions
        self.next_funcs = {}
        for l in self.strat.latches:
            self.next_funcs[l] = self.aig_to_bdd(self.strat.latch_map[l])
        

        self.attr = self.aig_to_bdd(self.strat.node_map["_attractor_"]) # (L, X_u)
        self.coreach = self.aig_to_bdd(self.strat.node_map["_coreach_"]) # (L, X_u)
        self.coop = self.aig_to_bdd(self.strat.node_map["_cooperation_"]) # (L, X_u)

        # self.man.dump("coop.pdf", [self.coop])
        # self.man.dump("attr.pdf", [self.attr])
        # self.man.dump("coreach.pdf", [self.coreach])

        input_vars = self.uinput_vars + self.cinput_vars
        greedy_states = self.man.quantify(self.attr | self.coop, input_vars)
        coreach_states = self.man.quantify(self.coreach, input_vars)
        assert((coreach_states & ~greedy_states) == self.man.false)

        self.aig_outputs_as_bdds = dict({(k,self.aig_to_bdd(v)) for (k,v) in self.strat.node_map.items()})

        # for (k,bdd) in self.aig_outputs_as_bdds.items():
        #     self.man.dump(k+".pdf", [bdd])
        # nb of test runs made by the tester
        self.iteration = 0

        # Interface to the program under test
        self.impl = BlackBoxProgram(impl)

        # Current state in the requirements automaton
        self.req_state_bdd = None

        self.initial_state = self.man.true
        for l in self.strat.latches:
            self.initial_state &= ~self.man.var(l)

        assert((self.coop | self.attr) & self.initial_state != self.man.false)
        # assert((self.attr) & self.initial_state != self.man.false)
        # assert((self.coop) & self.initial_state == self.man.false)

    def string_of_bdd_state(self):
        m = {k:v for (k,v) in self.man.pick_random(self.req_state_bdd).items() if k in self.strat.latches}
        return f"{m}"
    
    def getNbRuns(self):
        return self.iteration

    def aig_to_bdd(self, a : aiger.AIG):
        """
        Returns bdd representing the aig node a.
        @pre all latch and inputs were registered in man
        """
        man = self.man
        if (isinstance(a,aiger.aig.Input)):
            return man.var(a.name)
        elif (isinstance(a,aiger.aig.LatchIn)):
            return man.var(a.name)
        elif (isinstance(a,aiger.aig.ConstFalse)):
            return man.false
        elif (isinstance(a,aiger.aig.AndGate)):
            return self.aig_to_bdd( a.left) & self.aig_to_bdd(a.right)
        elif (isinstance(a,aiger.aig.Inverter)):
            return ~self.aig_to_bdd( a.input)
        else:
            raise Exception("What?")

    def aig_state_to_bdd(self, state):
        """
        Returns a bdd representing the cube given as a dict 
        @pre all var names were registered in man
        """
        man = self.man
        state_bdd = man.true
        for (k,v) in state.items():
            if v:
                state_bdd &= man.var(k)
            else:
                state_bdd &= ~man.var(k)
        return state_bdd

    def initialize_bdd_state(self):
        """
            Set the current state to the initial state of the requirements automaton
        """
        self.next_bdd_state(self.initial_state, self.cinput_cube & self.uinput_cube)
        # print(f"Initializing state: {self.string_of_bdd_state()}")

    def next_bdd_state(self, state, input_cube):
        """
            Update the current state to the successor for given input valuation
        """
        man = self.man
        nextstate = man.true
        for l in self.strat.latches:
            if ((self.next_funcs[l] & state) &input_cube) == self.man.false:
                nextstate &= ~man.var(l)
            else:
                nextstate &= man.var(l)
        self.req_state_bdd = nextstate

    def get_bdd_state(self):
        return self.req_state_bdd

    def restart(self):
        """
            Restart the black box implementation, and set the AIG and BDD states to initial
        """
        self.impl.restart()
        self.initialize_bdd_state()
        self.step = 1
        self.isTerminal()

    def getPossibleActions(self):
        coreach_state = self.coreach & self.req_state_bdd
        return coreach_state

    def getPossibleGreedyActions(self):
        greedy_state = self.attr & self.req_state_bdd
        if (greedy_state == self.man.false):
            greedy_state = self.coop & self.req_state_bdd
        return greedy_state


    def getRandomAction(self, actions=None):
        """
            Return an uncontrollable input valuation as a cube from actions.
            If actions is None, then we consider self.coreach
        """
        if actions is None:
            actions =self.coreach
        coreach_state = actions & self.req_state_bdd
        if (coreach_state == self.man.false):
            return None
        # restrict it to uncontrollable input
        mt ={k:v for (k,v) in self.man.pick_random(coreach_state).items() if k in self.strat.inputs and not "controllable_" in k and k != "clk"}
        return self.minterm2bdd(mt)

    def getGreedyAction(self, actions = None):
        """
            Return a random action using the greedy strategy; if no greedy choice is possible, a random coreachable action is returned
            This is an uncontrollable input valuation given as a cube from actions.
        """
        if actions is None:
            actions = self.coreach

        coreach_state = self.coreach & self.req_state_bdd
        attr_state = actions & self.attr & self.req_state_bdd
        coop_state = actions & self.coop & self.req_state_bdd

        if (coreach_state == self.man.false):
            return None
        choice = None
        if (attr_state != self.man.false):
            choice = attr_state
        elif coop_state != self.man.false:
            choice = coop_state
        else:
            choice = coreach_state
        # restrict it to uncontrollable input
        mt ={k:v for (k,v) in self.man.pick_random(choice).items() if k in self.strat.inputs and not "controllable_" in k and k != "clk"}
        return self.minterm2bdd(mt)

    def getStrictlyGreedyAction(self, actions = None):
        """
            Return a random action using the greedy strategy; if no greedy choice is possible, a random coreachable action is returned
            This is an uncontrollable input valuation given as a cube from actions.
        """
        if actions is None:
            actions = self.coreach

        attr_state = actions & self.attr & self.req_state_bdd
        coop_state = actions & self.coop & self.req_state_bdd

        choice = None
        if (attr_state != self.man.false):
            choice = attr_state
        elif coop_state != self.man.false:
            choice = coop_state
        else:
            #print(f"No greedy action for: {self.string_of_bdd_state()}")
            return None
        # restrict it to uncontrollable input
        mt ={k:v for (k,v) in self.man.pick_random(choice).items() if k in self.strat.inputs and not "controllable_" in k and k != "clk"}
        return self.minterm2bdd(mt)


    def getEpsilonGreedyAction(self):
        """
            With probability self.epsilon, return a random action; with prob. 1-epsilon, return a greedy action
        """
        if random.randint(0,100) < self.epsilon:
            return self.getRandomAction()
        else:
            return self.getGreedyAction()


    def takeAction(self, input_bdd):
        """
            Make one step in the blackbox implementation by sending it the given input.
            Read the output, and update the AIG and BDD states
        """
        self.step = self.step + 1
        self.total_steps += 1
        inp = {k:v for (k,v) in self.bdd2minterm(input_bdd).items() if k in self.strat.inputs and not "controllable_" in k}
        output, state = self.impl.next(inp)
        output = {f"controllable_{k}":v for (k,v) in output.items()}

        combined_aig_inputs = {**inp, **output}
        bdd_inputs = self.man.true
        for (i,b) in combined_aig_inputs.items():
            if b:
                bdd_inputs &= self.man.var(i)
            else:
                bdd_inputs &= ~self.man.var(i)
        self.next_bdd_state(self.req_state_bdd, bdd_inputs)
        if self.verbose >= 2:
            print(f"\tInput: {inp}")
            print(f"\tOutput: {output}")
            print(f"\tState: {state.decode()}", end="")
            self.printAIGOutputs()
            print("\n")

    def isError(self):
        """
            Is the AIG/BDD state at an error? (Is an error output set to 1)
        """
        for (output_label,output_bdd) in self.aig_outputs_as_bdds.items():
            satisfies = (output_bdd & self.req_state_bdd) != self.man.false
            if (satisfies and "error" in output_label):
                return True

    def getError(self):
        """
            Return the name of the error output that is satisfied.
        """
        for (output_label,output_bdd) in self.aig_outputs_as_bdds.items():
            satisfies = (output_bdd & self.req_state_bdd) != self.man.false
            if (satisfies and "error" in output_label):
                return output_label
        return None

    def isTerminal(self):
        """
            Is the AIG/BDD state terminal: this is the case if objective is satisfied or if we are in an inconclusive state
        """
        for (output_label,output_bdd) in self.aig_outputs_as_bdds.items():
            satisfies = (output_bdd & self.req_state_bdd) != self.man.false
            if (satisfies and "objective" in output_label):
                return True

        # coop_state = (self.coop & self.req_state_bdd) != self.man.false
        # attr_state = (self.attr & self.req_state_bdd) != self.man.false
        # print(f"Coop non-empty: {coop_state}, attr non empty: {attr_state}")
        coreach_state = self.coreach & self.req_state_bdd
        if (coreach_state == self.man.false):
            # print(f"{ANSI.PURPLE}{ANSI.BOLD}Inconclusive{ANSI.RESET}")
            return True

        return False

    def satisfiesObjective(self):
        """
            Whether current state satisfies objective
        """
        for (output_label,output_bdd) in self.aig_outputs_as_bdds.items():
            satisfies = (output_bdd & self.req_state_bdd) != self.man.false
            if (satisfies and "objective" in output_label):
                return True
        return False

    def getSatisfiedObjective(self):
        """
            Returns the label of an objective that is satisfied by the current state.
        """
        for (output_label,output_bdd) in self.aig_outputs_as_bdds.items():
            satisfies = (output_bdd & self.req_state_bdd) != self.man.false
            if (satisfies and "objective" in output_label):
                return output_label
        return None
        
    def isInconclusive(self):
        coreach_state = self.coreach & self.req_state_bdd
        if (coreach_state == self.man.false):
            # print(f"{ANSI.PURPLE}Inconclusive{ANSI.RESET}")
            return True
        return False

    def minterm2bdd(self, action):
        bdd = self.man.true
        for (x,b) in action.items():
            if(b):
                bdd &= self.man.var(x)
            else:
                bdd &= ~self.man.var(x)
        return bdd

    def bdd2minterm(self, bdd, care=None):
        return self.man.pick(bdd, care)

    def hashAction(self, action):
        return self.minterm2bdd(action)


    def printAIGOutputs(self):
        """
            Whether current state satisfies objective
        """
        print("\tAIG requirement outputs that are true:", end=" ")
        for (output_label,output_bdd) in self.aig_outputs_as_bdds.items():
            satisfies = (output_bdd & self.req_state_bdd) != self.man.false
            if (satisfies):
                print(output_label, end=", ")       
        return False

    def get_history(self):
        return self.input_history

    def print_bdd_history(self, history):
        for input_bdd in history:
            val = self.man.pick_random(input_bdd)
            print({k:v for (k,v) in val.items() if k in self.strat.inputs and not "controllable_" in k})

    def run(self, nb_runs : int, max_steps : int):
        start_time = time.time()
        total_steps = 0
        try:
            for r in range(1,nb_runs+1):
                self.iteration = r
                if self.verbose and ((r-1) % 10) == 0:
                    print(f"\r{ANSI.BROWN}{ANSI.NEGATIVE}{ANSI.BOLD}Random test run {r} / {nb_runs}{ANSI.RESET}",end='')

                self.restart()
                it = 0
                self.input_history = []
                try:
                    while(max_steps < 0 or it < max_steps):
                        if self.verbose >= 2:
                            print("")
                        total_steps = total_steps + 1

                        if self.isError():
                            raise RequirementViolation(self.getError(), self.input_history)
                        if self.satisfiesObjective():
                            raise ObjectiveReached(self.getSatisfiedObjective(), self.input_history)
                        if self.isInconclusive():
                            raise InconclusiveRun

                        input_bdd = self.getEpsilonGreedyAction()
                        self.input_history.append(input_bdd)
                        self.takeAction(input_bdd)
                        it += 1
                except InconclusiveRun:
                    continue
                except ObjectiveReached as e:
                    raise e
                except RequirementViolation as e:
                    raise e
            print("")
            print(f"\n{ANSI.YELLOW}Could not find covering trace{ANSI.RESET}")
            print(f"Made {self.total_steps} steps")
        except ObjectiveReached as e:
            logging.info("Displaying covering trace")
            # self.print_bdd_history(e.history)
            self.impl.print_history()
            print(f"\n{ANSI.GREEN}{ANSI.NEGATIVE}{ANSI.BOLD}Objective reached: {e.label}{ANSI.RESET}")
            print(f"Objective found after {self.total_steps} steps")
        except RequirementViolation as e:
            logging.info(f"Displaying error trace")
            self.impl.print_history()
            print(f"\n{ANSI.RED}{ANSI.NEGATIVE}{ANSI.BOLD}Requirement violation: State satisfies '{e.label}' {ANSI.RESET}")
            print(f"Error found after {self.total_steps} steps")
            # self.print_bdd_history(e.history)

        logging.info(f'{ANSI.BOLD}Test ended after {self.getNbRuns()} runs of {max_steps} steps{ANSI.RESET}')
        logging.info(f'Total time: {int(time.time() - start_time)}s')
        logging.info(f'Steps per second: {int(total_steps / ((time.time() - start_time)))}')

    def __del__(self):
        self.req_state_bdd = None
        self.coreach = None
        self.attr = None
        self.coop = None
        self.aig_outputs_as_bdds = None
        # Call gc to make sure bdd nodes are deallocated before exiting
        gc.collect()


class MCTSTester(RandomTester):
    def __init__(self, strat_file : str, impl : str, epsilon : int, rollout_policy : str, tree_policy_greedy_bound : int = 0, verbose : bool = False, graphviz : bool = False):
        super().__init__(strat_file, impl, epsilon, verbose)
        self.tree_policy_greedy_bound = tree_policy_greedy_bound
        self.rollout_policy = rollout_policy
        self.max_steps = None
        self.graphviz = graphviz
        # self.pre_bdds[i] is the BDD describing _pre{i}_
        self.pre_bdds = []
        pre_re = re.compile("_pre([0-9]+)_")
        for (k,v) in self.aig_outputs_as_bdds.items():
            m = pre_re.match(k)
            if m is not None:
                self.pre_bdds.append(None)
        for (k,v) in self.aig_outputs_as_bdds.items():
            m = pre_re.match(k)
            if m is not None:
                i = int(m.group(1))
                self.pre_bdds[i] = v
                assert(v != self.man.false)

    def getReward(self):
        """
            Return index i such that self.req_state_bdd belongs to pre_bdds[i].
            These bdds are supposed to be pairwise disjoint so this is well defined.
            Returns len(pre_bdds) if no such i (this is the case for states that are not coreachable).
        """
        for (i,prebdd) in enumerate(self.pre_bdds):
            if (self.req_state_bdd & prebdd) != self.man.false:
                return i
        return len(self.pre_bdds)


    def getMaxReward(self):
        return len(self.pre_bdds)

    def run(self, nb_runs : int, max_steps : int):
        self.max_steps = max_steps
        tester = mcts.mcts(bddman = self.man, max_steps = max_steps, timeLimit=None, iterationLimit=nb_runs, verbose=self.verbose, rollout_policy=self.rollout_policy, tree_policy_greedy_bound=self.tree_policy_greedy_bound)
        start_time = time.time()
        try:
            tester.search(self)
            print(f"\n\n{ANSI.YELLOW}Printing Optimal Policy{ANSI.RESET}")
            if self.verbose >= 1:
                tester.printOptimalPolicy(self)
                print("")
            print(f"\n{ANSI.YELLOW}Could not find covering trace after{ANSI.RESET}")
            print(f"Made {self.total_steps} steps")
        except mcts.RequirementViolation as e:
            logging.info(f"Displaying error trace")
            self.impl.print_history()
            print(f"\n{ANSI.RED}{ANSI.NEGATIVE}{ANSI.BOLD}Requirement violation: State satisfies '{e.label}' {ANSI.RESET}")
            print(f"Error found after {self.total_steps} steps")
        except mcts.ObjectiveReached as e:
            logging.info(f"Displaying covering trace")
            self.impl.print_history()
            print(f"\n{ANSI.GREEN}{ANSI.NEGATIVE}{ANSI.BOLD}Objective reached: {e.label}{ANSI.RESET}")
            print(f"Objective reached after {self.total_steps} steps")
        if self.graphviz:
            tester.displayDot(self.Xu - set(["clk"]))
        print("")
        logging.info(f'{ANSI.BOLD}Test ended after {tester.getNbRuns()} runs{ANSI.RESET}')
        logging.info(f'Steps per second: {int(tester.total_steps / ((time.time() - start_time)))}')
        logging.info(f'Minimum cost encountered: {tester.min_cost}')
    

def main():
    parser = argparse.ArgumentParser(description="Tester")
    parser.add_argument("-i", "--implementation", type=str, dest="impl",
                        help="Black-box executable to be tested",required=True)
    parser.add_argument("-s", "--strategy", type=str, dest="strat",
                        help="The strategy file obtained by test_generator.py applied on the requirements monitor",required=True)
    parser.add_argument("-e", "--engine", type=str, dest="engine",
                        help="Test algorithm", choices=["uniform", "mcts", "greedy"], required=True)
    parser.add_argument("--max-steps", type=int, dest="max_steps",
                        help="Bounds the number of steps made by each run of the tester. This is the max rollout length for the MCTS tester.",required=False,default=1000)
    parser.add_argument("--epsilon", type=int, dest="epsilon",
                        help="In the greedy approach, probability 0..100/100 of picking next input uniformly at random (from coreach); so that the greedy strategy is picked with prob. (100-epsilon)/100.",required=False,default=20)
    parser.add_argument("--random_seed", type=int, dest="random_seed",
                        help="random seed.",required=False,default=-1)
    parser.add_argument("-r", "--runs", type=int, dest="runs",
                        help="Number of test runs / MCTS rounds to perform.",required=False,default=25)
    parser.add_argument("-tpgb", "--tree-policy-greedy-bound", type=int, dest="greedy_tree_policy_bound",
                        help="At each node of the tree, apply eps-greedy as the tree policy n times, before switching to UCT", required=False,default=0)
    parser.add_argument("-rs", "--rollout-policy", type=str, dest="rollout_policy",
                        choices=["uniform","greedy"],
                        help="Rollout policy for MCTS: uniform | greedy", required=False, default="uniform")
    parser.add_argument("-v", "--verbose", type=int, dest="verbose",
                        help="Verbose mode.",required=False,default=True)
    parser.add_argument("-g", "--graphviz", type=bool, dest="graphviz",
                        help="Visualize the tree built by MCTS using graphviz.",required=False,default=False)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if (args.random_seed > 0 ):
        random.seed(args.random_seed)
    if args.engine == "uniform":
        args.epsilon = 100
    if ( args.engine == "greedy" or args.engine == "uniform"):
        tester = RandomTester(args.strat, args.impl, args.epsilon, args.verbose)
        tester.run(args.runs, args.max_steps)
    elif (args.engine == "mcts"):
        tester = MCTSTester(args.strat, args.impl, args.epsilon, args.rollout_policy, args.greedy_tree_policy_bound, args.verbose, args.graphviz)
        tester.run(args.runs, args.max_steps)
main()
