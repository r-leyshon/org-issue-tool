"""Query GitHub api."""
import requests
import pickle
import toml
from pyprojroot import here
from requests.adapters import HTTPAdapter, Retry
import pandas as pd

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
all_repo_deets = pd.DataFrame()

for i in responses:
    for j in i:
        repo_nms.append(j["name"])
        repo_deets = pd.DataFrame(
            {
                "html_url": [j["html_url"]],
                "is_private": [j["private"]],
                "is_archived": [j["archived"]],
                "name": [j["name"]],
                "description": [j["description"]],
                "programming_language": [j["language"]],
            }
        )
        all_repo_deets = pd.concat([all_repo_deets, repo_deets])


# get PRs and issues through the repos endpoint

repos_url = f"https://api.github.com/repos/{ORG_NM}/"
nm = "transport-network-performance"
repo_prs_url = repos_url + nm + "/pulls"
# experiment with hard coded repo nms
# repo_prs_url = repos_url + j["name"] + "/pulls"
# repo_issues_url = repos_url + j["name"] + "/issues"

# # get all PRs for a single repo
# repo_prs_resp = s.get(
#     repo_prs_url,
#     headers={"Authorization": f"Bearer {PAT}", "User-Agent": USER_AGENT},
# )
# if repo_prs_resp.ok:
#     repo_prs = repo_prs_resp.json()
# else:
#     print(f"Cant get repo PRs, status code: {repo_prs_resp.status_code}")


# for i in repo_prs:
#     for j in repo_prs:
#         # print(j.keys())
#         print(j["html_url"])
#         print(j["created_at"])
#         print(j["state"])
#         print(j["title"])
#         print(j["number"])
#         print(j["assignee"])
#         print(j["assignees"])
#         print(j["requested_reviewers"])
#         print(j["requested_teams"])
#         print(j["labels"])
#         print(j["draft"])
#         print(j["user"]["login"])
#         print(j["user"]["avatar_url"])
#         print(j["user"]["type"])
#         print(j["user"]["site_admin"])


def get_repo_issues(
    repo_url: str,
    sess: requests.Session = s,
    pat: str = PAT,
    agent: str = USER_AGENT,
) -> list:
    """Get all issues for a single repo, handles pagination.

    Parameters
    ----------
    repo_url : str
        The url string of the repo. Pattern is
        'https://api.github.com/repos/<ORGANISATION_NAME>/<REPO_NM>/issues'
    sess : requests.Session, optional
        Session configured with retry strategy, by default s
    pat : str, optional
        The GitHub PAT, by default PAT
    agent : str, optional
        User's browser agent, by default USER_AGENT

    Returns
    -------
    list
        A nested list containing the response JSON for each open issue in the
        repo.

    Raises
    ------
    PermissionError
        The PAT is not recognised by GitHub.

    """
    page = 1
    responses = list()
    while True:
        resp = sess.get(
            repo_url,
            headers={"Authorization": f"Bearer {pat}", "User-Agent": agent},
            params={"page": page},
        )

        if resp.ok:
            responses.append(resp.json())
            if "next" in resp.links:
                repo_url = resp.links["next"]["url"]
                page += 1
            else:
                # no more next links so stop while loop
                print(
                    "Requests left: " + resp.headers["X-RateLimit-Remaining"]
                )
                break
        elif resp.status_code == 401:
            raise PermissionError("PAT is invalid. Try generating a new PAT.")

        else:
            print(f"Unable to get repo issues, code: {resp.status_code}")
    return responses


# get all repo issues for selected organisation
all_repo_issues = list()
for nm in repo_nms[0:2]:
    print(nm)
    repo_issues = get_repo_issues(f"{repos_url}{nm}/issues")
    all_repo_issues.extend(repo_issues)


# handle response (maybe get_issue_metadata)
# get repo issue details for each page
repo_issues_concat = pd.DataFrame()
for issue in all_repo_issues:
    for i in issue:
        # pull assignees rather than assignee, as both fields are populated
        assignees = i["assignees"]
        if len(assignees) == 0:
            assignees_users = None
            assignees_avatar_urls = None
        else:
            assignees_users = [usr["login"] for usr in assignees]
            assignees_avatar_urls = [usr["avatar_url"] for usr in assignees]

        # collect issue details
        issue_row = pd.DataFrame.from_dict(
            {
                "repo_url": [i["repository_url"]],
                "issue_id": [i["id"]],
                "title": [i["title"]],
                "body": [i["body"]],
                "number": [i["number"]],
                "labels": [", ".join([lab["name"] for lab in i["labels"]])],
                "assignee_login": [assignees_users],
                "assignees_avatar_urls": [assignees_avatar_urls],
                "created_at": [i["created_at"]],
                "user_name": [i["user"]["login"]],
                "user_avatar": [i["user"]["avatar_url"]],
            }
        )
        repo_issues_concat = pd.concat([repo_issues_concat, issue_row])

repo_issues_concat.sort_values(by="created_at", inplace=True)


repo_issues_concat.to_csv("data/testing.csv")
