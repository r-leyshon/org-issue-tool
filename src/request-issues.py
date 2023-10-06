"""Query GitHub api."""
import requests

# import pickle
import toml
from pyprojroot import here
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
retries = requests.adapters.Retry(
    total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
)
s.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))


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
# with open(here("data/github-api-repo-responses.pkl"), "rb") as f:
#     responses = pickle.load(f)

all_repo_deets = pd.DataFrame()

for i in responses:
    for j in i:
        repo_deets = pd.DataFrame(
            {
                "html_url": [j["html_url"]],
                "repo_url": [j["url"]],
                "is_private": [j["private"]],
                "is_archived": [j["archived"]],
                "name": [j["name"]],
                "description": [j["description"]],
                "programming_language": [j["language"]],
            }
        )
        all_repo_deets = pd.concat([all_repo_deets, repo_deets])


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


def get_all_org_issues(
    org_nm: str = ORG_NM,
    repo_nms: list = all_repo_deets["name"],
    issue_type="issues",
    sess: requests.Session = s,
    pat: str = PAT,
    agent: str = USER_AGENT,
) -> pd.DataFrame:
    """Get every repo issue for entire org.

    Will work for issues or pulls. Returns a table of all issues metadata.

    Parameters
    ----------
    org_nm : str, optional
        The name of the organisation, by default ORG_NM (from .secrets.toml)
    repo_nms : list, optional
        List of the repo name strings, by default all_repo_deets["name"]
    issue_type : str, optional
        Accepts either 'issues' or 'pulls'
    sess : requests.Session, optional
        Request session configured with retry strategy, by default s
    pat : str, optional
        User's PAT code, by default PAT (from .secrets.toml)
    agent : str, optional
        User agent string, by default USER_AGENT (from .secrets.toml)

    Returns
    -------
    list
        List of JSON content with metadata for each issue (or PR)

    Raises
    ------
    ValueError
        `issue_type` is not either 'issues' or 'pulls'

    """
    issue_type = issue_type.lower().strip()
    if "issue" in issue_type:
        endpoint = "issues"
    elif "pull" in issue_type:
        endpoint = "pulls"
    else:
        raise ValueError("`issue_type` must be either 'issues' or 'pulls'.")

    base_url = f"https://api.github.com/repos/{org_nm}/"
    all_issues = list()
    n_repos = len(repo_nms)
    for i, nm in enumerate(repo_nms):
        print(f"Get issues for {nm}, {i+1}/{n_repos} done.")
        repo_issues = get_repo_issues(f"{base_url}{nm}/{endpoint}")
        all_issues.extend(repo_issues)

    repo_issues_concat = pd.DataFrame()
    for issue in all_issues:
        print(issue)
        # catch empty responses where repos have no PRs
        if len(issue) == 0:
            continue
        else:
            for i in issue:
                # pull assignees over assignee, as both fields are populated
                assignees = i["assignees"]
                if len(assignees) == 0:
                    assignees_users = None
                    assignees_avatar = None
                else:
                    assignees_users = [usr["login"] for usr in assignees]
                    assignees_avatar = [usr["avatar_url"] for usr in assignees]

                # collect issue details
                if endpoint == "issues":
                    repo_url = i["repository_url"]
                else:
                    repo_url = i["url"]

                issue_row = pd.DataFrame.from_dict(
                    {
                        "repo_url": [repo_url],
                        "issue_id": [i["id"]],
                        "title": [i["title"]],
                        "body": [i["body"]],
                        "number": [i["number"]],
                        "labels": [
                            ", ".join([lb["name"] for lb in i["labels"]])
                        ],
                        "assignee_login": [assignees_users],
                        "assignees_avatar_urls": [assignees_avatar],
                        "created_at": [i["created_at"]],
                        "user_name": [i["user"]["login"]],
                        "user_avatar": [i["user"]["avatar_url"]],
                    }
                )

                repo_issues_concat = pd.concat([repo_issues_concat, issue_row])

    repo_issues_concat.sort_values(by="created_at", inplace=True)

    return repo_issues_concat


# get every organisation issue
repos_issues = get_all_org_issues(repo_nms=all_repo_deets["name"])

repos_with_issues = all_repo_deets.merge(
    repos_issues, how="left", on="repo_url", suffixes=["_repo", "_issue"]
)

# repos_with_issues.to_csv("data/testing.csv")

# get every organisation pull request
all_org_pulls = get_all_org_issues(
    repo_nms=all_repo_deets["name"],
    issue_type="pulls",
)

# all_org_pulls.to_csv("data/test-pulls.csv")
