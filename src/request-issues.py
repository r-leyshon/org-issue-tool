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
repos_url = org_url + "repos"

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
        repos_url,
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

# https://api.github.com/repos/datasciencecampus/transport-network-performance/pulls
# https://api.github.com/repos/datasciencecampus/transport-network-performance/issues
