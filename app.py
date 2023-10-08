"""Organisation bounty board app."""
from shiny import ui, App, render
import pandas as pd
from pyprojroot import here

dat = pd.read_feather(here("data/out.arrow"))

app_ui = ui.page_fluid(
    ui.input_text(
        id="name_entry",
        label="Please enter your name",
        placeholder="Your name here",
    ),
    ui.output_data_frame("table"),
)


def server(input, output, session):
    """Server logic goes here."""

    @output
    @render.data_frame
    def table():
        """Return the table object."""
        return dat


app = App(app_ui, server)
