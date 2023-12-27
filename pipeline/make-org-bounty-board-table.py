"""api usage."""
# import toml
import os

# from pyprojroot import here
from datetime import datetime as dt
import pickle

from org_bounty_board import request_org_issues as reqiss
from org_bounty_board.utilities import check_df_for_true_column_value

PUBLIC_ONLY = True

# CONFIG = toml.load(here(".secrets.toml"))
# ORG_NM = CONFIG["GITHUB"]["ORG_NM"]
# PAT = CONFIG["GITHUB"]["PAT"]
# USER_AGENT = CONFIG["USER"]["USER_AGENT"]
USER_AGENT = os.getenv("AGENT")
ORG_NM = os.getenv("ORG_NM")
PAT = os.getenv("PAT")
# get all org issues
all_repo_deets = reqiss.get_org_repos(
    org_nm=ORG_NM,
    pat=PAT,
    agent=USER_AGENT,
    public_only=PUBLIC_ONLY,
)
# failsafe if api parameters change
if PUBLIC_ONLY:
    check_df_for_true_column_value(all_repo_deets, "is_private")

# get every organisation issue
all_org_issues = reqiss.get_all_org_issues(
    repo_nms=all_repo_deets["name"],
    org_nm=ORG_NM,
    pat=PAT,
    agent=USER_AGENT,
    issue_type="issues",
)
# get every organisation pull request
all_org_pulls = reqiss.get_all_org_issues(
    repo_nms=all_repo_deets["name"],
    org_nm=ORG_NM,
    pat=PAT,
    agent=USER_AGENT,
    issue_type="pulls",
)

out = reqiss.combine_repo_tables(all_repo_deets, all_org_issues, all_org_pulls)
out.to_feather("data/out.arrow")

# save date of ingest for presentation in UI
vintage_dt = dt.now().replace(microsecond=0)
with open("data/vintage-date.pkl", "wb") as f:
    pickle.dump(vintage_dt, f)
    f.close()
# save organisation name for presentation in UI
with open("data/org-nm.pkl", "wb") as f:
    pickle.dump(ORG_NM, f)
    f.close()
