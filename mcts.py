"""
This module was initially built upon the following code: https://github.com/pbsinclair42/MCTS under the MIT Licence:

Copyright 2018 Paul Sinclair

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import division
import time
import math
import random
import graphviz
import sys
from common import ANSI, RequirementViolation, ObjectiveReached


class treeNode():
    """
        A node of the MCTS. We do not store states which are assumed not to be observable.
    """
    def __init__(self, parent, incoming_action):
        self.isFullyExpanded = False
        self.isSuccess = False
        self.isDeadEnd = False
        self.parent = parent
        self.incoming_action = incoming_action
        self.numVisits = 0
        self.totalReward = 0
        self.children = {}
        self.unexploredActions = None
    def __str__(self):
        return f"Q: {self.totalReward/self.numVisits:.2f} x {self.numVisits}"

class mcts():
    """
        Standard MCTS algorithm. We use a mixed of discounted cost and undiscounted costs on rollouts:
        the cost of the rollout history (starting from the leaf of the tree) is discounted, while the cost of the 
        last state of the rollout is not discounted.
        A BDD is used at each node to store the set of available actions that have not been explored yet.
        The goal of MCTS is to optimize the policy to reach objective. Errors are not given particular costs
        since we just stop and report whenever an error is reached. One can guide the search towards error states
        by choosing objective as error.
    """
    def __init__(self, bddman, max_steps, discount=0.8, verbose=0, timeLimit=None, iterationLimit=None, explorationConstant=1/math.sqrt(2),
                 rollout_policy="uniform", tree_policy_greedy_bound: int = 0):
        self.man = bddman
        self.verbose = verbose
        self.discount = discount
        self.max_steps = max_steps
        self.rollout_policy = rollout_policy
        self.tree_policy_greedy_bound = tree_policy_greedy_bound
        if timeLimit is not None:
            if iterationLimit is not None:
                raise ValueError("Cannot have both a time limit and an iteration limit")
            # time taken for each MCTS search in milliseconds
            self.timeLimit = timeLimit
            self.limitType = 'time'
        else:
            if iterationLimit is None:
                raise ValueError("Must have either a time limit or an iteration limit")
            # number of iterations of the search
            if iterationLimit < 1:
                raise ValueError("Iteration limit must be greater than one")
            self.searchLimit = iterationLimit
            self.limitType = 'iterations'
        self.explorationConstant = explorationConstant
        self.root = None
        self.do_not_stop_on_error = False
        self.do_not_stop_on_objective = False
        # number of runs / rounds made by MCTS
        self.iteration = 0
        # number of interaction steps including by the tree polciy and rollout
        self.total_steps = 0
        self.min_cost = float("inf")
        self.tree_rewards = [] # rewards encountered during the traversal of the tree

    def rollout(self, system, discount, history=None):
        """
            Runs a rollout with given policy.
            Returns a pair of costs (discounted_cost, final_reward):
            discounted_cost is the discounted cost of the rollout history (where each step has unit cost),
            and final_reward is the cost of the last state; the latter is not discounted.
        """
        discounted_cost = 0
        steps = len(system.get_history())
        min_cost = system.getMaxReward()
        gamma_n = 1.
        if self.rollout_policy == "greedy":
            action_selector = system.getEpsilonGreedyAction
        else:
            action_selector = system.getRandomAction
        while not system.isTerminal() and steps < self.max_steps:
            action = action_selector()
            if history is not None:
                history.append(action)
            system.takeAction(action)

            r = system.getReward()
            # discounted_cost = discount * discounted_cost + r
            discounted_cost += gamma_n * r
            if min_cost is None or r < min_cost:
                min_cost = r
            steps = steps + 1
            gamma_n = gamma_n * discount
        final_cost =  system.getReward()
        if final_cost < self.min_cost:
            self.min_cost = final_cost
        for i in range(steps, self.max_steps+1):
            discounted_cost += gamma_n * final_cost
            gamma_n = gamma_n * discount
        # print(f"discount: {discount}")
        # print(f"max_steps, steps: {(self.max_steps, steps)}")
        # print(f"{discount ** (self.max_steps - steps)}")        
        # print(f"Adding final_cost * { (1 -(discount ** (self.max_steps - steps))) /(1-discount)} to rollout cost")
        assert(steps <= self.max_steps)
        # print(f"Rollout cost: {discounted_cost} + {final_cost * (1 - (discount ** (self.max_steps - steps))) /(1-discount)}")
        # discounted_cost += final_cost * (1 - (discount ** (self.max_steps - steps))) /(1-discount)
        self.total_steps = self.total_steps + steps
        if self.verbose >= 2:
            print(f"Rollout gamma-cost: {float(discounted_cost):0.2f}.\nMin cost: {min_cost}\nFinal cost: {final_cost}")
        return (discounted_cost, min_cost, final_cost)

    def search(self, system):
        self.root = treeNode(None, None)
        system.restart()
        self.min_cost = float("inf")
        self.total_steps = 0
        self.root.unexploredActions = system.getPossibleActions()

        if self.limitType == 'time':
            timeLimit = time.time() + self.timeLimit / 1000
            while time.time() < timeLimit:
                self.executeRound(system)
        else:
            for i in range(self.searchLimit):
                self.iteration = i
                if self.verbose >= 1 and (i % 10) == 0:
                    print(f"\r{ANSI.BROWN}{ANSI.NEGATIVE}{ANSI.BOLD}MCTS Tester run: {i} / {self.searchLimit}{ANSI.RESET}",end='')
                self.executeRound(system)

    def executeRound(self, system):
        """
            execute a selection-expansion-simulation-backpropagation round
        """
        if self.verbose >= 2:
            print(f"\n{ANSI.BLUE}New Round{ANSI.RESET}\n")
        system.restart()
        self.tree_rewards = []
        self.tree_rewards.append(system.getReward())
        node = self.selectNode(self.root, system)
        if (system.isTerminal()):
            node.isSuccess = system.satisfiesObjective()
            node.isDeadEnd = system.isInconclusive()
        if self.verbose >= 2:
            print("--- Leaf selected. Starting rollout ---")
        history = []

        discounted_cost, min_cost, final_cost = self.rollout(system, self.discount, history)
        if self.verbose >= 2:
            print(f"--- Got reward rollout cost: {discounted_cost}; final cost: {final_cost} ---")
        self.backpropogate(node, discounted_cost, min_cost, final_cost)
        if(not self.do_not_stop_on_error and system.isError()):
            while(node.incoming_action is not None):
                history.insert(0, node.incoming_action)
                node = node.parent
            raise RequirementViolation(system.getError(), history)
        if(not self.do_not_stop_on_objective and system.satisfiesObjective()):
            while(node.incoming_action is not None):
                history.insert(0, node.incoming_action)
                node = node.parent
            raise ObjectiveReached(system.getSatisfiedObjective(), history)

    def selectNode(self, node, system):
        """
            Apply tree policy to return a leaf node
        """
        while not system.isTerminal():
            self.total_steps = self.total_steps + 1
            if node.numVisits < self.tree_policy_greedy_bound:
                next_node = self.expandGreedyChild(node, system)
                if next_node is not None:
                    return next_node
                else:
                    node = self.getBestChild(node, system, self.explorationConstant)
            else:
                if node.unexploredActions == self.man.false: # node.isFullyExplored
                    node = self.getBestChild(node, system, self.explorationConstant)
                else:
                    return self.expand(node, system)
        return node


    def expand(self, node, system):
        """
            Expand inner tree node with one action not yet seen.
            Simulate the impl with the chosen input.
        """
        action_bdd = system.getRandomAction(node.unexploredActions)
        node.unexploredActions &= ~action_bdd
        newNode = treeNode(node, action_bdd)
        node.children[action_bdd] = newNode
        if node.unexploredActions == self.man.false:
            node.isFullyExpanded = True
        system.takeAction(action_bdd)
        self.tree_rewards.append(system.getReward())

        newNode.unexploredActions = system.getPossibleActions()
        return newNode


    def expandGreedyChild(self, node, system):
        """
            Expand the node by a new greedy action, and simulate the impl with the chosen input.
            If all strictly greedy actions have been explored before, return None.
        """
        action_bdd = system.getStrictlyGreedyAction(node.unexploredActions)
        if action_bdd is None:
            return None
        node.unexploredActions &= ~action_bdd
        newNode = treeNode(node, action_bdd)
        node.children[action_bdd] = newNode
        if node.unexploredActions == self.man.false:
            node.isFullyExpanded = True
        system.takeAction(action_bdd)
        self.tree_rewards.append(system.getReward())
        newNode.unexploredActions = system.getPossibleActions()
        return newNode


    def getEpsilonGreedyChild(self, node, system):
        """
            Return a successor for the given tree node using the eps-greedy policy.
            Return (node,b) where node is the successor node, and b is True iff node is a newly created leaf.
        """
        action_bdd = system.getEpsilonGreedyAction()
        system.takeAction(action_bdd)
        self.tree_rewards.append(system.getReward())        
        if (action_bdd in node.children):
            return node.children[action_bdd], False
        else:
            newNode = treeNode(node, action_bdd)
            node.unexploredActions &= ~action_bdd
            node.children[action_bdd] = newNode
            if node.unexploredActions == self.man.false:
                node.isFullyExpanded = True
            newNode.unexploredActions = system.getPossibleActions()
            return newNode, True


    def backpropogate(self, node, discounted_cost, min_cost, final_reward):
        current_r = discounted_cost
        while node is not None:
            node.numVisits += 1 
            current_r = (self.tree_rewards.pop() + self.discount * discounted_cost)
            node.totalReward += current_r * min_cost
            node = node.parent

    def getBestChild(self, node, system, explorationValue):
        """
            Return a tree node using UCT. Also simulate the impl with the chosen input.
        """
        bestValue = float("inf")
        bestNodes = []
        for child in node.children.values():
            nodeValue =  child.totalReward / child.numVisits - explorationValue * math.sqrt(
                2 * math.log(node.numVisits) / child.numVisits)
            if nodeValue < bestValue:
                bestValue = nodeValue
                bestNodes = [child]
            elif nodeValue == bestValue:
                bestNodes.append(child)
        node = random.choice(bestNodes)
        system.takeAction(node.incoming_action)
        self.tree_rewards.append(system.getReward())
        return node

    def getNbRuns(self):
        return self.iteration

    def printOptimalPolicy(self, system):
        inputs = system.Xu_noclk
        node = self.root
        system.restart()
        while (len(node.children)>0 and not system.isTerminal()):
            print(node)
            print(f"Success: {node.isSuccess}")
            print(f"Deadend: {node.isDeadEnd}")
            print(f"Actions: {(list(map(lambda x: self.man.pick(x, inputs), node.children.keys())))}")
            print(f"Remaining actions: {self.man.false != node.unexploredActions}")
            node = self.getBestChild(node, system, 0)

    def displayDot(self, inputs):
        g = graphviz.Graph('MCTS', filename='mcts.gv', engine='dot')
        node_names = dict()
        node_index = 0
        todo = [self.root]
        while len(todo)>0:
            node = todo.pop()
            node_names[node] = node_index
            if (node.isSuccess):
                g.attr('node', shape='rectangle', color="green", style="filled")
            elif (node.isDeadEnd):
                g.attr('node', shape='rectangle', color="gray", style="filled")
            else:
                g.attr('node', shape='rectangle', color="black", style="solid")
            g.node(f"{node_index}", label=node.__str__())
            node_index = node_index + 1
            for ch in node.children.values():
                todo.append(ch)

        todo = [self.root]
        while len(todo)>0:
            node = todo.pop()
            for (inp, ch)in node.children.items():
                g.edge(f"{node_names[node]}", f"{node_names[ch]}", label=f"{self.man.pick(inp, inputs)}")
                todo.append(ch)

        g.view()
