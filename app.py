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
        choices=reps,
    ),
    ui.input_radio_buttons(
        id="type_filter",
        label="Select Type:",
        choices=["issue", "pr"],
        selected="issue",
        inline=True,
    ),
    ui.output_data_frame("table"),
)


def server(input, output, session):
    """Server logic goes here."""

    @output
    @render.data_frame
    def table():
        """Return the optionally filtered table object."""
        r = input.repo_filter()
        t = input.type_filter()
        q_string = f"name == '{r}' and type == '{t}'"
        return dat.query(q_string)


app = App(app_ui, server)
