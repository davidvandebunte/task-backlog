from datetime import datetime, timedelta, timezone
from threading import Timer
from IPython.display import display, Math, Latex, Markdown
import pandas as pd
import os, time

from taskbacklog.analysis import perform_analysis

class System():
    def __init__(self, name, tips):
        self.name = name
        self.tips = tips

systems = {'c': System(name="Calendar", tips="""
Can you shrink the “filled” blocks in your schedule? For example, can you:
* Shorten meetings? Achieve the meeting goal so it can be cancelled.
* Get exercise at the same time?
* "Work" less than 40 hours?
* Ignore a deadline to do weightier work instead? See [Decision: Should you respect a particular deadline?](https://docs.google.com/document/d/1JKY2lkoiNFfMR-UEcAL3EEOeIVhftIgdke-60MdYk64/edit).

Review:
* [Google Calendar - today](https://calendar.google.com/calendar/r/day)
* [Calendar - Outlook - today](https://outlook.office.com/calendar/view/day)
"""),
           'g': System(name="Gmail", tips="""
- [Gmail](https://mail.google.com/mail/u/0/#inbox) tips:
  - Use j/k
  - Find email count in the top right (to the left of the gear).
"""),
           'o': System(name="Outlook", tips="""
- [Outlook](https://outlook.office.com/mail/inbox) tips:
  - Use j/k!
  - Snooze on your phone
  - Find email count by selecting all conversations then deselecting one.
"""),
           'k': System(name="Keep", tips="""
- [Keep](https://keep.google.com/#home) tips:
  - Use j/k
"""),
           'u': System(name="Unfinished", tips="""
If you already started some task, have a bias towards finishing it before you move on (lower E[**E**] for tasks in working memory).

If you must move on and you also believe the task will come up again, move unorganized working memory into a git commit message (long-term shared storage). For example:
* Chrome tabs
* tmux tabs
* Other applications

Consider restarting your machine after a cleanup.
"""),
           's': System(name="Schedule", tips="""
Schedule the item to your day. See:
  * [Decision: Should you schedule your day down to the hour?](https://docs.google.com/document/d/1QuEe13p89Ffcq7Ao_zVcYyrHaq9rMvv8oOCKzmN9BnU/edit)
  * See [Process: Schedule day (home)](https://docs.google.com/document/d/1iPrL-jZtRQC2e3C70vFTNahcJa_H9IBMWOByTciPkHk/edit) (i.e. use a timer).
""")}

option_table = pd.DataFrame(
    {systems[system].name: pd.Series(dict({'Key': system})) for system in systems})

def prompt_for_integer(prompt_string):
    expect_integer = None
    while(expect_integer is None):
        try:
            expect_integer = int(input(prompt_string))
        except ValueError:
            print("Please enter an integer.")
    return expect_integer

# https://stackoverflow.com/a/1301528/622049
#
# TODO: Set timezone in Docker so you can use python3 conversions:
# https://stackoverflow.com/a/13287083/622049
os.environ['TZ'] = 'America/Chicago'
time.tzset()

def start_timer(timebox, timeout_string):
    cutoff = (datetime.now() + timebox).strftime('%Y-%m-%d %H:%M')
    display(Markdown(f"""
- Timebox: {timebox}
- Cutoff: {cutoff}"""
))
    t = Timer(timebox.seconds, lambda: display(Markdown("""
```diff
- {}
```
""".format(timeout_string))))
    t.start()
    return t

def schedule_day(fetch_ideas):
    # Skim online task systems (starting with the most interruptive)
    while True:
        display(option_table)
        sk = input("Enter system selection (empty to stop): ")
        if sk not in systems:
            break

        system = systems[sk]
        display(Markdown(system.tips))

        if sk == 'c':
            input("Hit enter to continue.")
            continue

        if sk == 's':
            full = perform_analysis(fetch_ideas)
            task = prompt_for_integer("Enter task index: ")
            if task < 0 or task >= full.size:
                break
            t = start_timer(timedelta(hours=full.at[task, "Timebox"]),
                            "Ask someone for help.")
            row = full.loc[task]
            
            if row.estimate > 1 and not row.url:
                display(Markdown(
    """
    Before starting work on a task larger than an hour, report your plan:
    - On a shared backlog
    - At a daily stand-up
    """
            ))

            if row.estimate > 4:
                display(Markdown(
    """
    Break down tasks larger than 4 hours. See:
    - [Process: Backlog grooming](https://docs.google.com/document/d/1bmRN4n0kbMN2EOhMKk62VMjpkAYcolWbKj0vPLyJKa8/edit#)
    - [Decision: Should you split story subtasks further?][1]
    - [Process: PBI subtask planning](https://docs.google.com/document/d/1g39MM493y1KSkZLYHWtxmnf-68CZjfw_rPADFaErvgk/edit).

    [1]: https://docs.google.com/document/d/1hQ99w3ZnrLpwygfZJHFTKfbrYqwo-cXB5tZIBmKtw4o/edit#
    """
            ))

            if row.age < 3:
                display(Markdown(
    """
    Avoid recently created stories. See:
    - [Process: Handling interruptions](https://docs.google.com/document/d/1Y0LbIWeP4wnwm09FsC2YejIMFvrG3wfNtiVQVQaG4ew/edit)
    - [What if the build breaks?](https://docs.google.com/document/d/1wp7nLk6tkN8FlLELK7-IcbWgNlpmw51MC1DWSW9_yLc/edit)
    """
            ))
            if row.age < timedelta(weeks=2).days:
                display(Markdown(
    """
    This story was created in the last two weeks. Is it valuable because it is focal?
    """
            ))
            input("Hit enter to complete.")
            t.cancel()
            continue
            
        tasks = prompt_for_integer("Enter unsorted tasks in {}: ".format(system.name))
        if tasks == 0:
            continue

        t = start_timer(timedelta(minutes=2*tasks), "Timeout! Routine: Come back to this system.")
        print("")
        
        # It's inefficient to snooze to your task backlog items that are
        # less than 60m even though there is risk they have focal value
        # you could remove. Your only option is to apply a safety factor
        # that adds the typical "focal value" of a small task. What boost
        # (as a ratio of true value) does a typical small task get from
        # being focal? Small tasks have little time to get focal?
        focal_boost = 0.1
        
        # It’s addicting to get “something” done even if it's not weighty
        # ("gamification" of email).
        gamification_boost = 0.05
        
        # Don't become a manager; you do the vast majority of long-term
        # valuable learning in focused work (you learn almost nothing on
        # small tasks).
        #
        # Knuth doesn't spend any time on tasks that don't involve focus.
        #
        # The W you enter for these mini tasks is often
        # anchored off typical values on your task backlog; how bad is
        # the anchoring?
        learn_boost = 0.4

        # The weight of the top item on your backlog is probably only
        # ever going to get higher. It's questionable to do any task of
        # lower weight than from the top of your backlog (opportunity
        # costs).
        weight_top_of_backlog = 5
        weight_small = weight_top_of_backlog * (1 + focal_boost) * (1 + gamification_boost) * (1 + learn_boost)

        display(Markdown("""
    Perform up to one minute on TVE, then bin it:

    | Size range (bin) of E[E]    | Algorithm            |
    | ---                         | ---                  |
    | $E[\\textbf{E}] < 1m$       | Small personal task  |
    | $1m < E[\\textbf{E}] < 4m$  | Medium personal task |
    | $4m < E[\\textbf{E}] < 60m$ | Large personal task  |
    | $60m < E[\\textbf{E}]$      | Shareable task       |

    ### Small personal tasks
    Unsubscribe from small tasks with $E[\\textbf{W}]$ lower
    than $W_{small}$ (currently """ + f"{weight_small}). Resolve as you encounter."
    ))
        
        # All the same for medium
        focal_boost = 0.2
        gamification_boost = 0.1
        learn_boost = 0.6
        weight_medium = weight_top_of_backlog * (1 + focal_boost) * (1 + gamification_boost) * (1 + learn_boost)
        
        display(Markdown(
    """
    ### Large personal task
    Steps:
    1. If the item has no cost of delay and is weighty, attempt
       to group it with other items on your task backlog.
    1. Annotate with your one-minute TVE analysis (to define an
       E for a detailed TVE analysis later).

    Immediately resolve annotated personal tasks only after skimming all systems. Spend up
    to 10\% of $E[\\textbf{E}]$ on TVE, then flip a coin to decide whether to do it.

    ### Shareable task
    Move larger tasks ($E[\\textbf{E}] > 60m$) to a shared backlog, or analyze
    them on your task backlog and report you are going to do them at daily scrum.

    ### Medium personal task
    Spend up to 10\% of $E[\\textbf{E}]$ on TVE, or $6s < E[\\textbf{E}] < 24s$
    (i.e. do a mental analysis only). Resolve as you encounter; enter "y" then the weight below.
    """
    ))

        while True:
            medium = input("Do you need to add 4m for a medium personal task (empty to stop)?")
            t.cancel()
            if not medium:
                break

            display(Markdown("""
    Estimate the weight of the medium task: 
    $$W = E[\\textbf{V}/\\textbf{E}]$$"""
    ))
            weight = prompt_for_integer("Estimated weight: ")
            if weight < weight_medium:
                display(Markdown(
    "Say no to this task because $E[\\textbf{V}/\\textbf{E}] < W_{medium}$ " + f" ({weight} < {weight_medium}). "
    ))

            t = start_timer(timedelta(minutes=8), "Timeout! Come back to this task.")
            input("Hit enter to complete.")
            print("")
