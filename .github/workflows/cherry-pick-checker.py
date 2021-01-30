#!/usr/bin/env python3

import os
import re
import git
import json
import logging
import argparse

GITHUB_WORKSPACE = os.environ.get('GITHUB_WORKSPACE')
GITHUB_SHA       = os.environ.get('GITHUB_SHA')
GITHUB_BASE_REF  = os.environ.get('GITHUB_BASE_REF')

if GITHUB_WORKSPACE is None or GITHUB_SHA is None or GITHUB_BASE_REF is None:
    print("Error: this script is designed to run as a Github Action")
    exit(1)

#----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Git cherry pick checker')
parser.add_argument('--notacherrypick',
                    action="store_true",
                    default=False,
                    help="If this flag is used, then cherry pick messages are not required (regardless of the cherry_pick_required config setting)")
args = parser.parse_args()

#----------------------------------------------------------------------------

# Defaults, unless overridden by .github/workflows/cherry-pick-checker.json
config = {
    'cherry_pick_required' : False,
}

filename = os.path.join(GITHUB_WORKSPACE, '.github', 'workflows', 'cherry-pick-checker.json')
if os.path.exists(filename):
    with open(filename) as fp:
        new_config = json.load(fp)
    for key in new_config:
        config[key] = new_config[key]

# If --notacherrypick was specified, then disable the requirement for cherry
# pick messages
if args.notacherrypick:
    config['cherry_pick_required'] = False

#----------------------------------------------------------------------------

# This is the regexp we'll be looking for
prog = re.compile(r'\(cherry picked from commit ([a-z0-9]+)\)')

#----------------------------------------------------------------------------

# Get a list of commits that we'll be examining.  Use the progromatic form of
# "git log BASE_REF..HEAD" (i.e., "git log ^BASE_REF HEAD") to do the heavy
# lifting to find that set of commits.
git_cli = git.cmd.Git(GITHUB_WORKSPACE)
commits = git_cli.log(f"--pretty=format:%h", f"origin/{GITHUB_BASE_REF}..{GITHUB_SHA}").splitlines()

#----------------------------------------------------------------------------

# Get a handle we can use to search for hashes in the git DAG
repo = git.Repo(GITHUB_WORKSPACE)

found_happy     = list()
found_not_happy = list()
not_found       = list()
skipped         = list()
for hash in commits:
    logging.debug(f"Getting hash: {hash}")
    commit = repo.commit(hash)

    # Skip the GITHUB_SHA, because that's the Github artificial merge hash
    # for this PR
    if hash == GITHUB_SHA[:len(hash)] and len(commit.parents) == 2:
        continue

    # If the message starts with "Revert" or if the commit is a merge, don't
    # require a cherry-pick message
    if commit.message.startswith("Revert ") or len(commit.parents) == 2:
        skipped.append(hash)
        continue

    # Otherwise, find all cherry pick messages and check to make sure that the
    # commit message they refer to exists
    found_cherry_pick_line = False
    non_existent = dict()
    for match in prog.findall(commit.message):
        found_cherry_pick_line = True
        try:
            c = repo.commit(match)
        except ValueError as e:
            # These errors mean that the git library recognized the hash as
            # a valid commit, but the GitHub Action didn't fetch the entire
            # repo, so we don't have all the meta data about this commit.
            # Bottom line: it's a good hash.  So -- no error here.
            pass
        except git.BadName as e:
            # Use a dictionary to track the non-existent hashes, just on the
            # off chance that the same non-existent hash exists more than
            # once in a single commit message (i.e., the dictionary will
            # effectively give us de-duplication for free).
            non_existent[match] = True

    # Process the results for this commit
    if found_cherry_pick_line:
        if len(non_existent) == 0:
            found_happy.append(hash)
        else:
            str = f"{hash} refers to non-existent commit"
            if len(non_existent) > 1:
                str += "s"
            str += ": "
            str += ", ".join(non_existent)
            found_not_happy.append(str)
    else:
        not_found.append(hash)

#----------------------------------------------------------------------------

def print_list(msg, items, prefix=""):
    print(msg)
    for item in items:
        print(f"{prefix}* {item}")

passed = True
if len(found_happy):
    print_list("""
The following commits contained messages with good cherry pick comments:""",
               found_happy)

# If we found commits with cherry pick messages that refer to non-existent
# commits, this *always* causes the test to fail.
if len(found_not_happy):
    passed = False
    print_list("""
::error ::The following commits contained messages with erroneous cherry pick comments:
::error ::(*** these commits caused the test to fail ***)""",
                found_not_happy, prefix="::error ::")

# If we found commits without cherry pick messages, it depends on the config
# as to whether that causes the test to fail or not
if len(not_found):
    prefix = ""
    suffix = ""
    middle = "did NOT cause"
    error  = ""

    if config['cherry_pick_required']:
        passed = False
        prefix = "*** "
        middle = "caused"
        suffix = " ***"
        error  = "::error ::"

    msg = f"""
{error}The following commits did not contain cherry pick notices in their commit messages:
{error}({prefix}these commits {middle} the test to fail{suffix}):"""
    print_list(msg, not_found, prefix=error)

if len(skipped):
    print_list("\nThe following commits were skipped (reverts, merges, skips):", skipped)

if passed:
    print("\nTest passed: everything was good!")
    exit(0)
else:
    print("\nTest failed: sad panda")
    exit(1)
