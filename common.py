#import dd.autoref
from dd import cudd
import random

class ANSI:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = "\033[0m"

#class BDD(dd.autoref.BDD):
class BDD(cudd.BDD):
    """
    Extension of the autoref BDD class with a random satisfying minterm method
    """
    def __pick_random_rec(self, u, cube):
        """ Pick a random cube."""
        assert(u is not None)
        assert(u != self.false)
        if u == self.true:
            cube = {
                self.var_at_level(i): v
                for i, v in cube.items()}
            return cube

        v = u.high
        w = u.low
        i = u.level
        if (u.negated):
            v = ~v
            w = ~w

        if (v == self.false):
            d = dict(cube)
            d[i] = False
            return self.__pick_random_rec(w, d)
        elif (w == self.false):
            d = dict(cube)
            d[i] = True
            return self.__pick_random_rec(v, d)
        else:
            d = dict(cube)
            countw = self.count(w) 
            countu = self.count(u)
            if random.randint(0,countw+countu-1) < countw:
            #if random.randint(0,1) == 0:
                d[i] = False
                return self.__pick_random_rec(w, d)
            else:
                d[i] = True
                return self.__pick_random_rec(v, d)

    def pick_random(self, u):
        """
        Return a random satisfying minterm.
        """
        cube = self.__pick_random_rec(u, dict([]))
        for var in self.vars:
            if not var in cube.keys():
                if random.randint(0,1) == 0:
                    cube[var] = False
                else:
                    cube[var] = True
        return cube



class RequirementViolation(Exception):
    def __init__(self, label, history):
        self.history = history
        self.label = label
    pass

class ObjectiveReached(Exception):
    def __init__(self, label, history):
        self.history = history
        self.label = label
    pass

