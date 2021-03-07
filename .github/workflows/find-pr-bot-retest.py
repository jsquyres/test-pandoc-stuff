#!/usr/bin/env python3

"""

JMS new description

"""

import os
import git
import json
import argparse

# Python API for GitHub API
from github import Github

GITHUB_WORKSPACE  = os.environ.get('GITHUB_WORKSPACE')
GITHUB_TOKEN      = os.environ.get('GITHUB_TOKEN')
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY')

# Sanity check
if (GITHUB_WORKSPACE is None or
    GITHUB_TOKEN is None or
    GITHUB_REPOSITORY is None):
    print("Error: this script is designed to run as a Github Action")
    exit(1)

#----------------------------------------------------------------------------

"""
If "bot:notacherrypick" is in the PR description, then disable the
cherry-pick message requirement.
"""
def get_pr_metadata(pr_num):
    g    = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPOSITORY)
    pr   = repo.get_pull(pr_num)

    retest = False
    for token in ['bot:retest', 'bot:github:retest', 'bot:ompi:retest']:
        if token in pr.body:
            retest = True

            pr.create_reaction("rocket")

            break

    return pr, retest

#----------------------------------------------------------------------------

def setup_cli():
    parser = argparse.ArgumentParser(description='Github CI Action')
    parser.add_argument('--pr', type=int,
                        required=True,
                        help='PR number')

    args = parser.parse_args()

    return args

#----------------------------------------------------------------------------

def main():
    args = setup_cli()

    pr, retest = get_pr_metadata(args.pr)

    print(f"""
::set-output name=GITHUB_BASE_REF::{pr.base.ref}
::set-output name=GITHUB_REF::{pr.head.ref}
::set-output name=BOT_RETEST::{int(retest)}
""")

#----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
