"""Query GitHub api."""
import requests
import pickle
import toml
from pyprojroot import here
from requests.adapters import HTTPAdapter, Retry

CONFIG = toml.load(here(".secrets.toml"))
ORG_NM = CONFIG["GITHUB"]["ORG_NM"]
PAT = CONFIG["GITHUB"]["PAT"]
USER_AGENT = CONFIG["USER"]["USER_AGENT"]

# GitHub API endpoint to list pull requests for the organization
org_url = f"https://api.github.com/orgs/{ORG_NM}/"
org_repos_url = org_url + "repos"

# configure scrape session
s = requests.Session()
retries = Retry(
    total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
)
s.mount("https://", HTTPAdapter(max_retries=retries))


responses = list()
page = 1
# paginate request
while True:
    print(f"Requesting page {page}")
    response = s.get(
        org_repos_url,
        headers={"Authorization": f"Bearer {PAT}", "User-Agent": USER_AGENT},
        params={"page": page},
    )
    if response.ok:
        responses.append(response.json())
        if "next" in response.links:
            print(f"Next link: {response.links['next']}")
            url = response.links["next"]["url"]
            page += 1
        else:
            print(
                f"Requests left: {response.headers['X-RateLimit-Remaining']}"
            )
            break
    else:
        print(f"Failed response for {url}, code: {response.status_code}")


# with open(here("data/github-api-repo-responses.pkl"), "wb") as f:
#     pickle.dump(responses, f)
with open(here("data/github-api-repo-responses.pkl"), "rb") as f:
    responses = pickle.load(f)

repo_nms = list()

for i in responses:
    for j in i:
        repo_nms.append(j["name"])


# some useful info through this endpoint
j.keys()
j["name"]
j["full_name"]
j["private"]
j["owner"]
j["html_url"]
j["issues_url"]  # need to programmatically insert numbers, incudes PRs
j["language"]  # python
j["has_issues"]
j["open_issues_count"]  # seems to include issues & PRs

# TODO: Read all PRs & metadata, read all issues & metadata

repos_url = f"https://api.github.com/repos/{ORG_NM}/"
repo_prs_url = repos_url + j["name"] + "/pulls"
repo_issues_url = repos_url + j["name"] + "/issues"

# get all PRs for a single repo
repo_prs_resp = s.get(
    repo_prs_url,
    headers={"Authorization": f"Bearer {PAT}", "User-Agent": USER_AGENT},
)
if repo_prs_resp.ok:
    repo_prs = repo_prs_resp.json()
else:
    print(f"Unable to get repo PRs, status code: {repo_prs_resp.status_code}")


for i in repo_prs:
    for j in repo_prs:
        print(j.keys())
        print(j["html_url"])
        print(j["created_at"])
        print(j["state"])
        print(j["title"])
        print(j["number"])
        print(j["assignee"])
        print(j["assignees"])
        print(j["requested_reviewers"])
        print(j["requested_teams"])
        print(j["labels"])
        print(j["draft"])
        print(j["user"]["login"])
        print(j["user"]["avatar_url"])
        print(j["user"]["type"])
        print(j["user"]["site_admin"])

# get all issues for a single repo
repo_issues_resp = s.get(
    repo_issues_url,
    headers={"Authorization": f"Bearer {PAT}", "User-Agent": USER_AGENT},
)

if repo_issues_resp.ok:
    repo_issues = repo_issues_resp.json()
else:
    print(f"Unable to get repo issues, code: {repo_issues_resp.status_code}")


for i in repo_issues:
    print(i.keys())
    # print(i["user"])
    print(
        i["pull_request"]
    )  # all PRs are issues, though not all issues are PR
    print(i["body"])
    print(i["state_reason"])
    print(i["number"])
    print(i["title"])
    print(i["labels"])
    print(i["state"])  # open, but api state sonly open issues will be listed
    print(i["assignee"])
    print(i["assignees"])
    print(i["created_at"])
    print(i["draft"])
