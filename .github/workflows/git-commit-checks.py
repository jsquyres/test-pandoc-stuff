#!/usr/bin/env python3

import os
import re
import git
import json
import argparse

GITHUB_WORKSPACE = os.environ.get('GITHUB_WORKSPACE')
GITHUB_SHA       = os.environ.get('GITHUB_SHA')
GITHUB_BASE_REF  = os.environ.get('GITHUB_BASE_REF')

# Sanity check
if GITHUB_WORKSPACE is None or GITHUB_SHA is None or GITHUB_BASE_REF is None:
    print("Error: this script is designed to run as a Github Action")
    exit(1)

#----------------------------------------------------------------------------

def print_result(good_list, bad_list, skipped_list):
    def _print_list(msg, items, prefix=""):
        print(msg)
        for item in items:
            print(f"{prefix}- {item}")

    passed = True
    if len(good_list):
        msg = "\nThe following commits passed all tests:"
        _print_list(msg, good_list)

    if len(bad_list):
        passed = False
        # The "::error ::" token will cause Github to highlight these
        # lines as errors
        msg = f"\n::error ::The following commits caused this test to fail"
        _print_list(msg, bad_list, prefix="::error ::")

    if len(skipped_list):
        msg = "\nThe following commits were skipped (reverts, merges):"
        _print_list(msg, skipped_list)

    return passed

#----------------------------------------------------------------------------

# Global regexp, because we use it every time we call check_signed_off()
# (i.e., for each commit in this PR)
prog_sob = re.compile(r'Signed-off-by: (.+) <(.+)>')

def check_signed_off(config, repo, commit, bad_list):
    matches = prog_sob.search(commit.message)
    if not matches:
        bad_list.append(f"{commit.hexsha}: does not contain a valid Signed-off-by line")
        return False

    return True

#----------------------------------------------------------------------------

def check_email(config, repo, commit, bad_list):
    email = commit.committer.email.lower()

    for pattern in config['bad emails']:
        match = re.search(pattern, email)
        if match:
            bad_list.append(f"{commit.hexsha}: committer email address contains '{pattern}'")
            return False

    return True

#----------------------------------------------------------------------------

# Global regexp, because we use it every time we call check_cherry_pick()
# (i.e., for each commit in this PR)
prog_cp = re.compile(r'\(cherry picked from commit ([a-z0-9]+)\)')

def check_cherry_pick(config, repo, commit, bad_list):
    non_existent = dict()
    found_cherry_pick_line = False
    for match in prog_cp.findall(commit.message):
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
            return True
        else:
            str = f"{commit.hexsha}: contains a cherry pick message that refers to non-existent commit"
            if len(non_existent) > 1:
                str += "s"
            str += ": "
            str += ", ".join(non_existent)
            bad_list.append(str)
            return False

    else:
        if config['cherry pick required']:
            bad_list.append(f"{commit.hexsha}: does not include a cherry pick message")
            return False
        else:
            return True

#----------------------------------------------------------------------------

def check_all_commits(config):
    # Get a list of commits that we'll be examining.  Use the progromatic form of
    # "git log BASE_REF..HEAD" (i.e., "git log ^BASE_REF HEAD") to do the heavy
    # lifting to find that set of commits.
    git_cli = git.cmd.Git(GITHUB_WORKSPACE)
    commits = git_cli.log(f"--pretty=format:%h", f"origin/{GITHUB_BASE_REF}..{GITHUB_SHA}").splitlines()

    #----------------------------------------------------------------------------

    # Get a handle we can use to search for hashes in the git DAG
    repo = git.Repo(GITHUB_WORKSPACE)

    good_list    = list()
    bad_list     = list()
    skipped_list = list()
    for hash in commits:
        commit = repo.commit(hash)

        # Skip the GITHUB_SHA, because that's the Github artificial merge hash
        # for this PR
        if hash == GITHUB_SHA[:len(hash)] and len(commit.parents) == 2:
            continue

        # If the message starts with "Revert" or if the commit is a merge, don't
        # require a signed-off-by
        if commit.message.startswith("Revert "):
            skipped_list.append(f"{commit.hexsha} (revert)")
            continue
        elif len(commit.parents) == 2:
            skipped_list.append(f"{commit.hexsha} (merge)")
            continue

        # Do the checks
        # The checks will add the commit to the bad_list if they fail
        good  = check_signed_off(config, repo, commit, bad_list)
        good &= check_email(config, repo, commit, bad_list)
        good &= check_cherry_pick(config, repo, commit, bad_list)

        # If all tests pass, add the commit to the good_list
        if good:
            lines = commit.message.split('\n')
            first = lines[0][:50]
            if len(lines[0]) > 50:
                first += "..."
            good_list.append(f'{commit} ("{first}")')

    return good_list, bad_list, skipped_list

#----------------------------------------------------------------------------

def load_config(args):
    # Defaults
    config = {
        'cherry pick required' : False,
        'permit empty' : False,
        'bad emails' : [
            '^root@',
            'localhost',
            'localdomain',
        ],
    }

    filename = os.path.join(GITHUB_WORKSPACE, '.github', 'workflows', 'git-commit-checks.json')
    if os.path.exists(filename):
        with open(filename) as fp:
            new_config = json.load(fp)
        for key in new_config:
            config[key] = new_config[key]

    # If --notacherrypick was specified, then disable the requirement for cherry
    # pick messages
    if args.notacherrypick:
        config['cherry pick required'] = False

    return config

#----------------------------------------------------------------------------

def setup_cli():
    parser = argparse.ArgumentParser(description='Git cherry pick checker')
    parser.add_argument('--notacherrypick',
                        action="store_true",
                        default=False,
                        help="If this flag is used, then cherry pick messages are not required (regardless of the 'cherry pick required' config setting)")
    args = parser.parse_args()

    return args

#----------------------------------------------------------------------------

def main():
    args   = setup_cli()
    config = load_config(args)
    good_list, bad_list, skipped_list = check_all_commits(config)
    passed = print_result(good_list, bad_list, skipped_list)

    if passed:
        print("\nTest passed: everything was good!")
        exit(0)
    else:
        print("\nTest failed: sad panda")
        exit(1)

#----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
