# org-issue-tool
View all open repository issues and PRs for an organisation - a precursor
bounty board.

A [python shiny application](https://richleysh84.shinyapps.io/org-bounty-board/)
displays the time it was updated, organisation name and open repository
metadata. This is deployed on a Friday at 00:00 with GitHub Actions.

## Workflow Guide

```mermaid
flowchart LR
    A[update.yml] ==>|Friday 00:00| B(JOB: Install dependencies)
    B ==> C(JOB: Run pipeline)
    C --> D[data/vintage-date.pkl]
    C --> E[data/org-nm.pkl]
    C --> F[data/out.arrow]
    G([AGENT\nAPP_PAT\nORGNM]) -.-> C
    C ==> H(JOB: Configure rsconnect)
    I([RSCONNECT_USERNAME\nRSCONNECT_TOKEN\nRSCONNECT_SECRET]) -.-> H
    H ==> J(JOB: Deploy to rsconnect)
    K([APP_ID]) -.-> J
    J ==> L{{shinyapps.io: serve app.py}}
    D -.-> L
    E -.-> L
    F -.-> L

```

The [GitHub Actions workflow file](/./.github/workflows/update.yml) expects the
repository to have configured:

- environment variables
    - `RSCONNECT_USERNAME`
    - `ORGNM` (the organisation name to scrape issues/PRs)
- secrets
    - `AGENT` (an appropriate agent string)
    - `APP_PAT`
    - `RSCONNECT_TOKEN`
    - `RSCONNECT_SECRET`
    - `APP_ID`

Note the workflow deploys to an application called `org-bounty-board`.
