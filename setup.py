# Your backlog is a list of tasks.
backlog = []

# The V and E in tasks are encouraged to include uncertainties.
import uncertainties
from uncertainties import ufloat

from datetime import datetime

# Tasks should be defined with:
# * E in time.
# * V in either dollars or time. If in dollars, use the "count" unit:
#   * https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
#   * https://pint.readthedocs.io/en/0.9/defining.html
#   * https://github.com/hgrecco/pint
import pint
ureg = pint.UnitRegistry()
ureg.setup_matplotlib(True)

class PBI():
    # TODO: Should you include a personal V and a company V? The personal V includes
    # whether you learn from the story. You are looking for the alignment of your interests
    # with the company interests. You could have a table that lists priorities if you
    # only include company interests, or if you only include your personal interests.
    #
    # I like this approach because it makes it clear what some "research" developers do
    # (they only care about the personal V).
    def __init__(self, T, V_units, creation_time, tasks):
        # A short string summarizing the value of the PBI, such as:
        # - A user story.
        # - A functional requirement.
        self.T = T
        
        # V is stored in units of hours; the "smart" constructor takes
        # measurements in time and converts to the standard of hours.
        #
        # TODO: Support converting dollars to hours once there are many V
        # measurements in dollars.
        #
        # By providing V without units we make analysis of tasks
        # easier (no nested uncertainties classes in pint classes).
        self.V = V_units.to(ureg.hours).magnitude

        self.creation_time = creation_time
        
        self.tasks = tasks
        
    def W(self):
        return self.V / self.E()

    def E(self):
        return sum(task.E for task in self.tasks)

    def S(self):
        return self.E() < 8


class Task():
    def __init__(self, T, E_units):
        # A short string summarizing the task.
        self.T = T

        # E is stored in units of hours; the "smart" constructor takes
        # measurements in time and converts to the standard of hours.
        #
        # By providing E without units we make analysis of tasks
        # easier (no nested uncertainties classes in pint classes).
        self.E = E_units.to(ureg.hours).magnitude

    # Is the task small enough to start on? Should this include the uncertainty?
    def S(self):
        return self.E.nominal_value < 8
