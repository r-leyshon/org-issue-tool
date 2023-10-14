"""api usage."""
import toml
from pyprojroot import here

from org_bounty_board import request_org_issues as reqiss

CONFIG = toml.load(here(".secrets.toml"))
ORG_NM = CONFIG["GITHUB"]["ORG_NM"]
PAT = CONFIG["GITHUB"]["PAT"]
USER_AGENT = CONFIG["USER"]["USER_AGENT"]

# get all org issues
all_repo_deets = reqiss.get_org_repos(org_nm=ORG_NM, pat=PAT, agent=USER_AGENT)
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