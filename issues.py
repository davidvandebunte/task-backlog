from datetime import date
import os

# Read as much as possible from a shared location when you're working on a
# team; put analysis in JIRA before your personal notes.
from jira import JIRA


def load_jira():
    import configparser
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.jira.conf'))
    jira_cred = config['credentials']
    # https://jira.readthedocs.io/en/master/examples.html#cookie-based-authentication
    return JIRA(
        'https://ngmp.in.here.com',
        auth=(jira_cred['username'], jira_cred['password']))


# The V and E in tasks are encouraged to include uncertainties.
from uncertainties import ufloat

# Tasks should be defined with:
# * E in time.
# * V in either dollars or time. If in dollars, use the "count" unit:
#   * https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
#   * https://pint.readthedocs.io/en/0.9/defining.html
#   * https://github.com/hgrecco/pint
import pint
ureg = pint.UnitRegistry()


class ValueDimensions():
    def __init__(self, learning_ratio, other=0.0 * ureg.hours):
        """Construct from raw data

        Parameters:
        learning_ratio (double): Ratio of time regained long-term to time
            invested now because of your increased knowledge/skills. Time can
            be regained before or after your current company; usually the time
            after will dominate this number.
        other (pint [time]): Other forms of value, converted to dimensions of time
        """
        # Learning ratio: The ratio of the time you'll gain long-term from
        # learning relative to the time it takes to do the task. For dedicated
        # learning tasks (e.g. following a tuturial) you would hope this to be
        # greater than one.
        self.learning_ratio = learning_ratio
        self.other = other

    @classmethod
    def from_components(cls,
                        learning_ratio,
                        compensation=0.0 * ureg.hours,
                        delay=0.0 * ureg.hours):
        """Construct from delineated value components

        V is stored in units of hours; the "smart" constructor takes
        measurements in time and converts to the standard of hours.

        Compensation is usually via salary or bonuses; cost of delay is also
        often dollars saved for a company and received in the same way.

        Parameters:
        learning_ratio (double): See above
        compensation (pint [time]): Dollar value of task, converted to
            dimensions of time.
        delay (pint [time]): Dollar value of cost of delay, converted to
            dimensions of time.
        """
        # TODO: Support converting dollars to hours once there are many V
        # measurements in dollars.
        return ValueDimensions(learning_ratio, compensation + delay)

    def total_value(self, task_size):
        """Value with all dimensions considered

        Parameters:
        task_size (pint [time]): Size of task

        Returns:
        double (pint [time]): Total value
        """
        return self.learning_ratio * task_size + self.other


class Issue():
    def __init__(self,
                 T,
                 value_dimensions,
                 created=None,
                 description=None,
                 notes=None,
                 url=None):
        # A short string summarizing the issue (title)
        self.T = T
        self.summary = T

        self.created = created
        self.description = description
        self.notes = notes

        self.value_dimensions = value_dimensions

        if url is not None:
            self.url = url
        else:
            self.url = ""


class PBI(Issue):
    # Only ask for a creation date; entering the hour of creation is too much
    # detail (actively prevent such detail).
    def __init__(self,
                 T,
                 V_units,
                 creation_date,
                 value_dimensions,
                 url=None,
                 tasks=None,
                 E_units=None):
        Issue.__init__(self, T=T, value_dimensions=value_dimensions, url=url)

        # TODO: Move to ValueDimensions
        # By providing V without units we make analysis of tasks
        # easier (no nested uncertainties classes in pint classes).
        self.V = V_units.to(ureg.hours).magnitude

        self.creation_date = creation_date

        if tasks is not None:
            self.tasks = tasks
            assert (E_units is None)
        elif E_units is not None:
            self.tasks = [
                Task(
                    summary=self.T,
                    value_dimensions=value_dimensions,
                    url=self.url,
                    estimate=E_units)
            ]
        else:
            raise Exception("Missing constructor parameter")

    def W(self):
        return self.V / self.E()

    def E(self):
        return sum(task.E for task in self.tasks)


class Task(Issue):
    def __init__(self,
                 summary,
                 estimate,
                 value_dimensions,
                 wip_ratio=1.0,
                 created=None,
                 description=None,
                 notes=None,
                 url=None):
        Issue.__init__(
            self,
            T=summary,
            value_dimensions=value_dimensions,
            created=created,
            description=description,
            notes=notes,
            url=url)
        """
        Parameters:
        wip_ratio (double): Ratio of time to complete this task now relative to
            a mental "cold start"; higher for:
              - Work you've already started yourself (in personal mental RAM).
              - Code you will have to read anyways others are writing (in team
                mental RAM). Now is the most efficient (for you, only) time to
                catch defects and improve code quality.
        """

        self.wip_ratio = wip_ratio

        # E is stored in units of hours; the "smart" constructor takes
        # measurements in time and converts to the standard of hours.
        #
        # By providing E without units we make analysis of tasks
        # easier (no nested uncertainties classes in pint classes).
        self.E = estimate.to(ureg.hours).magnitude

    jira = load_jira()

    @classmethod
    def from_jira_story(cls, jid, value_dimensions, estimate):
        """Construct a Task from a JIRA story

        Parameters:
        jid (string): JIRA ID
        """
        issue = cls.jira.issue(
            jid,
            fields='subtasks,timeestimate,status,summary,created,description')
        # If the story doesn't have subtasks, import it as a task of its own.
        if not issue.fields.subtasks:
            return cls.from_jira(
                jid, value_dimensions=value_dimensions, estimate=estimate)
        # Otherwise import all the subtasks, assuming they make the story
        # complete.
        tasks = []
        estimate = estimate / float(len(issue.fields.subtasks))
        for task in issue.fields.subtasks:
            tasks.extend(
                cls.from_jira(
                    task.key,
                    value_dimensions=value_dimensions,
                    estimate=estimate))
        return tasks

    @classmethod
    def from_jira(cls,
                  jid,
                  value_dimensions,
                  wip_ratio=0.7,
                  notes=None,
                  estimate=None):
        """Construct a Task from JIRA and optional overrides

        Parameters:
        jid (string): JIRA ID
        wip_ratio (double): See comments on the Task constructor. If the item
            is not WIP in JIRA, this parameter is reset to 1.0.
        """
        issue = cls.jira.issue(
            jid, fields='timeestimate,status,summary,created,description')
        if issue.fields.timeestimate:
            estimate = issue.fields.timeestimate * ureg.seconds
        assert estimate is not None

        ignorable_status = {'Complete', 'Cancelled', 'Released'}
        if issue.fields.status.name in ignorable_status:
            return []

        wip_status = {'Developing', 'Submitted'}
        if issue.fields.status.name not in wip_status:
            wip_ratio = 1.0

        return [
            Task(
                summary=issue.fields.summary,
                estimate=estimate,
                value_dimensions=value_dimensions,
                wip_ratio=wip_ratio,
                created=issue.fields.created,
                description=issue.fields.description,
                notes=notes,
                url=issue.permalink())
        ]

    def Timebox(self):
        # Default to two standard deviations (95% chance of completion)
        return self.E.nominal_value + 2 * self.E.std_dev
