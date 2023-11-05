"""Query GitHub api."""
import requests
import pandas as pd


def _configure_requests(
    n=5, backoff_f=0.1, force_on=[500, 502, 503, 504]
) -> requests.Session:
    """Set up a request session with retry.

    Parameters
    ----------
    n : int, optional
        Number of retries, by default 5
    backoff_f : float, optional
        backoff_factor, by default 0.1
    force_on : list, optional
        HTTP status errors to retry, by default [500,502,503,504]

    Returns
    -------
    requests.Session
        The requests session configured with the specified retry strategy.

    """
    # configure scrape session
    s = requests.Session()
    retries = requests.adapters.Retry(
        total=n, backoff_factor=backoff_f, status_forcelist=force_on
    )
    s.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))
    return s


def _paginated_get(
    url: str,
    pat: str,
    agent: str,
    params: dict = {},
    sess: requests.Session = _configure_requests(),
) -> list:
    """Get paginated responses.

    Parameters
    ----------
    url : str
        The url string to query.
    pat : str,
        The User's GitHub PAT.
    agent : str,
        User's browser agent.
    params: dict
        Dictionary of parameters to pass the developer API.
    sess : requests.Session, optional
        Session configured with retry strategy, by default
        _configure_requests() with default values of n=5, backoff_f=0.1,
        force_on=[500, 502, 503, 504]

    Returns
    -------
    list
        A nested list containing the response JSON content.

    Raises
    ------
    PermissionError
        The PAT is not recognised by GitHub.

    """
    page = 1
    responses = list()
    while True:
        print(f"Requesting page {page}")
        params["page"] = page
        resp = sess.get(
            url,
            headers={"Authorization": f"Bearer {pat}", "User-Agent": agent},
            params=params,
        )
        if resp.ok:
            responses.append(resp.json())
            if "next" in resp.links:
                url = resp.links["next"]["url"]
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


def get_org_repos(
    org_nm: str,
    pat: str,
    agent: str,
    sess: requests.Session = _configure_requests(),
    public_only: bool = False,
) -> pd.DataFrame:
    """Get repo metadata for all repos in a GitHub organisation.

    Parameters
    ----------
    org_nm : str,
        The organisation name, by default ORG_NM (read from .secrets.toml)
    pat : str,
        GitHub user PAT, by default PAT
    agent : str,
        User agent, by default USER_AGENT
    sess : requests.Session, optional
        Session configured with retry strategy, by default
        _configure_requests() with default values of n=5, backoff_f=0.1,
        force_on=[500, 502, 503, 504]
    public_only : bool
        If the GitHub PAT has private scopes for the organisation you are
        requesting, then private repo metadata will also be returned. To filter
        to public repo matadata only, set this parameter to True. Defaults to
        False.

    Returns
    -------
    pd.DataFrame
        Table of repo metadat.

    """
    # GitHub API endpoint to list pull requests for the organization
    org_repos_url = f"https://api.github.com/orgs/{org_nm}/repos"
    params = {}
    if public_only:
        params["type"] = "public"

    responses = _paginated_get(
        org_repos_url, sess=sess, pat=pat, params=params, agent=agent
    )
    DTYPES = {
        "html_url": str,
        "repo_url": str,
        "is_private": bool,
        "is_archived": bool,
        "name": str,
        "description": str,
        "programming_language": str,
    }
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
            # set dtypes
            for col, dtype in DTYPES.items():
                repo_deets[col].astype(dtype)

            all_repo_deets = pd.concat([all_repo_deets, repo_deets])

    return all_repo_deets


def get_all_org_issues(
    repo_nms: list,
    org_nm: str,
    pat: str,
    agent: str,
    issue_type="issues",
    sess: requests.Session = _configure_requests(),
) -> pd.DataFrame:
    """Get every repo issue for entire org.

    Will work for issues or pulls. Returns a table of all issues metadata.

    Parameters
    ----------
    repo_nms : list,
        List of the repo name strings
    org_nm : str,
        The name of the organisation, by default ORG_NM (from .secrets.toml)
    pat : str,
        User's PAT code, by default PAT (from .secrets.toml)
    agent : str,
        User agent string, by default USER_AGENT (from .secrets.toml)
    issue_type : str, optional
        Accepts either 'issues' or 'pulls', by default "issues"
    sess : requests.Session, optional
        Session configured with retry strategy, by default
        _configure_requests() with default values of n=5, backoff_f=0.1,
        force_on=[500, 502, 503, 504]

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
        repo_issues = _paginated_get(
            f"{base_url}{nm}/{endpoint}", pat=pat, agent=agent
        )
        all_issues.extend(repo_issues)

    # ensure consistent dtypes
    DTYPES = {
        "repo_url": str,
        "issue_id": int,
        "node_id": str,
        "title": str,
        "body": str,
        "number": int,
        "labels": str,
        "assignees_logins": str,
        "assignees_avatar_urls": str,
        "created_at": str,
        "user_name": str,
        "user_avatar": str,
    }

    repo_issues_concat = pd.DataFrame()
    for issue in all_issues:
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
                        "node_id": [i["node_id"]],
                        "title": [i["title"]],
                        "body": [i["body"]],
                        "number": [i["number"]],
                        "labels": [
                            ", ".join([lb["name"] for lb in i["labels"]])
                        ],
                        "assignees_logins": [assignees_users],
                        "assignees_avatar_urls": [assignees_avatar],
                        "created_at": [i["created_at"]],
                        "user_name": [i["user"]["login"]],
                        "user_avatar": [i["user"]["avatar_url"]],
                    }
                )
                # Set dtypes for each column
                for col, dtype in DTYPES.items():
                    issue_row[col] = issue_row[col].astype(dtype)

                repo_issues_concat = pd.concat([repo_issues_concat, issue_row])

    repo_issues_concat.sort_values(by="created_at", inplace=True)

    return repo_issues_concat


def combine_repo_tables(
    repo_table: pd.DataFrame,
    issues_table: pd.DataFrame,
    pulls_table: pd.DataFrame,
) -> pd.DataFrame:
    """Combine the three tables to provide a single coherent output.

    Parameters
    ----------
    repo_table : pd.DataFrame
        Output of get_org_repos().
    issues_table : pd.DataFrame
        Output of get_all_org_issues(repo_nms=all_repo_deets["name"],
        issue_type="issues")
    pulls_table : pd.DataFrame
        Output of get_all_org_issues(repo_nms=all_repo_deets["name"],
        issue_type="pulls")

    Returns
    -------
    pd.DataFrame
        Issues and PRs are concatenated with a 'type' marker. Single table
        joined with repo_table to give full context of each issue or PR.

    """
    reps = repo_table.copy(deep=True).reset_index(drop=True)
    iss = issues_table.copy(deep=True).reset_index(drop=True)
    pulls = pulls_table.copy(deep=True).reset_index(drop=True)
    # the pull table repo_url is not consistent with the issue table repo_url.
    # pattern is repo_url/pulls/pull_no
    pulls["repo_url"] = [i.split("pulls")[0][:-1] for i in pulls["repo_url"]]
    pulls["type"] = "pr"
    # filter down the issues table, which contains pulls too, and no obvious
    # identifier
    issues_pulls = iss.merge(pulls, how="left", on="node_id", indicator=True)[
        "_merge"
    ]
    iss = issues_table.loc[issues_pulls == "left_only"]
    iss["type"] = "issue"
    # combine issues & pulls
    output_table = pd.concat([iss, pulls], ignore_index=True)
    output_table = output_table.merge(reps, how="left", on="repo_url")

    return output_table
