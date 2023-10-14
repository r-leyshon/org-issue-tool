"""Organisation bounty board app."""
from shiny import ui, App, render
import pandas as pd
from pyprojroot import here

dat = pd.read_feather(here("data/out.arrow"))
reps = dat["name"].unique().tolist()

app_ui = ui.page_fluid(
    ui.input_selectize(
        id="repo_filter",
        label="Select a Repo:",
        multiple=True,
        choices=reps,
    ),
    ui.input_radio_buttons(
        id="type_filter",
        label="Select Type:",
        choices=["all", "issues", "pull requests"],
        selected="all",
        inline=True,
    ),
    ui.output_data_frame("table"),
    # ui.output_text("table")
)


def server(input, output, session):
    """Server logic goes here."""

    @output
    @render.data_frame
    # @render.text
    def table():
        """Return the optionally filtered table object."""
        r = input.repo_filter()
        t = input.type_filter()
        if t == "issues":
            type_sel = "issue"
        elif t == "pull requests":
            type_sel = "pr"

        if len(r) == 0 and t == "all":
            # no repo selected and 'all' type is selected
            return dat
        elif len(r) == 0:
            # no repo selected, 'all' type is not selected
            q_string = f"type == '{type_sel}'"
        elif t == "all":
            # min 1 repo selected and 'all' type is not selected
            q_string = f"name in {r}"
        else:
            # min 1 repo selected & 'all' type is not selected
            q_string = f"name in {r} and type == '{type_sel}'"
        return dat.query(q_string)
        # return q_string


app = App(app_ui, server)
