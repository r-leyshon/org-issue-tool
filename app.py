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
    ui.output_data_frame("table"),
)


def server(input, output, session):
    """Server logic goes here."""

    @output
    @render.data_frame
    def table():
        """Return the table object."""
        repo_select = input.repo_filter()

        if repo_select == "":
            return dat
        else:
            return dat.loc[dat["name"] == repo_select]


app = App(app_ui, server)
