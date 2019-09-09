import pandas as pd
from IPython.core.display import display, Markdown
from datetime import date


def perform_analysis(fetch_ideas):
    # Convert raw data to a pandas data frame.
    full = pd.DataFrame([{
        'summary':
        task.summary,
        'estimate':
        task.E,
        'weight':
        (pbi.V * task.E / pbi.E() + task.V_learn + task.V_lr * task.E) /
        task.E,
        'url':
        task.url,
        'age': (date.today() - pbi.creation_date).days,
        'Timebox':
        task.Timebox()
    } for pbi in fetch_ideas() for task in pbi.tasks])

    # Plot (V, E) with a label on every point with the summary of the Task. You should be able to quickly see how many
    # tasks or stories are small enough to start on (less than 4-8 hours). Hopefully you always have at least 3-4 stories
    # that are small enough you can pick from. Over time you should be able to see what kind of V/E ratio you typically have
    # on tasks you actually do.
    nominal = pd.DataFrame({
        'weight':
        full['weight'].map(lambda w: w.nominal_value),
        'estimate':
        full['estimate'].map(lambda e: e.nominal_value)
    })

    import matplotlib.pyplot as plt
    plt.rcParams['figure.figsize'] = [12, 6]

    # https://stackoverflow.com/a/26000515/622049
    # https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.errorbar.html
    # https://matplotlib.org/gallery/lines_bars_and_markers/errorbar_limits_simple.html
    # https://stackoverflow.com/a/43990689/622049
    fig, ax = plt.subplots()
    ax.errorbar(
        nominal.estimate,
        nominal.weight,
        xerr=full['estimate'].map(lambda e: e.std_dev),
        yerr=full['weight'].map(lambda w: w.std_dev),
        fmt='o')
    ax.set_xlim(left=0.1)
    ax.set_xscale("log")
    ax.set_ylim(bottom=0.)
    ax.axvline(x=4, linestyle=':', color='red')
    ax.axvline(x=1, linestyle='--', color='orange')
    ax.axhline(y=1, linestyle='-', color='red')

    for k, v in nominal.iterrows():
        ax.annotate(
            s=k,
            xy=(v.estimate, v.weight),
            xytext=(5, 5),
            textcoords='offset points',
            family='sans-serif',
            fontsize=16,
            color='darkslategrey')

    ax.grid()
    plt.show()

    # https://stackoverflow.com/a/48481247/622049
    def make_clickable(val):
        # target _blank to open new window
        return '<a target="_blank" href="{}">{}</a>'.format(val, val)

    # Show a table with what you believe the weightiest item is (even if it's too large to do).
    full.sort_values(by='weight', ascending=False, inplace=True)
    full['calendar_distance_hours'] = full.estimate.cumsum()
    full['calendar_distance_hours'] = full.calendar_distance_hours.apply(
        lambda x: x.nominal_value)
    styler = full.style
    styler.format({'url': make_clickable})

    # Schedule your day down to the hour; don't even consider tasks larger than 4 hours.
    styler.bar(subset="Timebox", color='#d65f5f', vmin=1.0, vmax=4.0)

    # Prefer older tasks (avoid focal work)
    styler.bar(subset="age", color='green', vmin=0.0, vmax=42.0)

    # Avoid tasks far in the future
    styler.bar(
        subset="calendar_distance_hours", color='yellow', vmin=0.0, vmax=40.0)

    def highlight_empty(x):
        return ['background-color: #d65f5f' if v == "" else '' for v in x]

    styler.apply(func=highlight_empty, subset="url")

    display(styler)

    return full
