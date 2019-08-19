# Your backlog is a list of tasks.
backlog = []

# The V and E in tasks are encouraged to include uncertainties.
import uncertainties
from uncertainties import ufloat

from datetime import date

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
    # Only ask for a creation date; entering the hour of creation is too much
    # detail (actively prevent such detail).
    def __init__(self, V_units, creation_date, T=None, url=None, tasks=None, E_units=None):
        if url is not None:
            self.url = url
            self.T = "See link"
        else:
            self.url = ""

        if T is not None:
            # A short string summarizing the value of the PBI, such as:
            # - A user story.
            # - A functional requirement.
            self.T = T

        assert(self.T is not None)
        
        # V is stored in units of hours; the "smart" constructor takes
        # measurements in time and converts to the standard of hours.
        #
        # TODO: Support converting dollars to hours once there are many V
        # measurements in dollars.
        #
        # By providing V without units we make analysis of tasks
        # easier (no nested uncertainties classes in pint classes).
        self.V = V_units.to(ureg.hours).magnitude

        self.creation_date = creation_date
        
        if tasks is not None:
            self.tasks = tasks
            assert(E_units is None)
        elif E_units is not None:
            self.tasks = [Task(T=self.T, E_units=E_units)]
        else:
            raise Exception("Missing constructor parameter")
        
    def W(self):
        return self.V / self.E()

    def E(self):
        return sum(task.E for task in self.tasks)


class Task():
    def __init__(self, E_units, V_learn=ufloat(0, 0)*ureg.hour, T=None, url=None):
        if url is not None:
            self.url = url
            self.T = "See link"
        else:
            self.url = ""

        if T is not None:
            # A short string summarizing the task.
            self.T = T

        assert(self.T is not None)

        # E is stored in units of hours; the "smart" constructor takes
        # measurements in time and converts to the standard of hours.
        #
        # By providing E without units we make analysis of tasks
        # easier (no nested uncertainties classes in pint classes).
        self.V_learn = V_learn.to(ureg.hours).magnitude
        self.E = E_units.to(ureg.hours).magnitude

    def Timebox(self):
        # Default to two standard deviations (95% chance of completion)
        return self.E.nominal_value + 2*self.E.std_dev
