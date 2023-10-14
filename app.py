"""Organisation bounty board app."""
from shiny import ui, App, reactive, render, Inputs, Outputs, Session
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
    ui.download_button("download", "Download CSV"),
    ui.output_data_frame("table"),
)


def server(input: Inputs, output: Outputs, session: Session):
    """Server logic goes here."""

    @reactive.Calc
    def selected_rows():
        """Handle the table querying. Pass to output.table() or download()."""
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

    @output
    @render.data_frame
    def table():
        """Return the optionally filtered table object."""
        return selected_rows()

    @session.download(filename="data.csv")
    def download():
        """Download the selected row range to file."""
        yield selected_rows().to_csv()


app = App(app_ui, server)
