"""Organisation bounty board app."""
from shiny import ui, App, reactive, render, Inputs, Outputs, Session
import pandas as pd
from pyprojroot import here
import os
import pickle

from org_bounty_board.utilities import check_df_for_true_column_value

dat_pth = "data/out.arrow"
if os.path.exists(dat_pth):
    dat = pd.read_feather(here("data/out.arrow"))
    check_df_for_true_column_value(dat, "is_private")
else:
    raise FileNotFoundError("Issue data not found.")

vintage_pth = "data/vintage-date.pkl"
if os.path.exists(vintage_pth):
    with open(vintage_pth, "rb") as f:
        vintage_dt = pickle.load(f)
        f.close()
else:
    raise FileNotFoundError("Vintage date not found.")

orgnm_pth = "data/org-nm.pkl"
if os.path.exists(orgnm_pth):
    with open(orgnm_pth, "rb") as f:
        orgnm = pickle.load(f)
        f.close()
else:
    raise FileNotFoundError("Organisation name not found.")

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
    ui.output_text("organisation"),
    ui.output_text("vintage"),
    ui.output_data_frame("table"),
    ui.download_button("download", "Download CSV"),
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

    @output
    @render.text
    def vintage():
        """Present the datetime that the data was ingested at."""
        return f"Date of Ingest: {vintage_dt}"

    @output
    @render.text
    def organisation():
        """Present the organisation name."""
        return f"Organisation name: {orgnm}"

    @session.download(filename="data.csv")
    def download():
        """Download the selected row range to file."""
        yield selected_rows().to_csv()


app = App(app_ui, server)
