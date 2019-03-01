#!/usr/bin/env python
"""
Script to check which pull requests listed in the release notes have multiple
authors. Prior to https://github.com/sympy/sympy-bot/pull/51, the bot was not
posting multiple authors to the wiki correctly, so this script helps to
retroactively fix that.

This requires doctr for the GitHub login functionality.
"""

import sys
import re

import requests

from doctr.local import GitHub_login, GitHub_raise_for_status

def main():
    if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help']:
        print("Provide the path to the release notes page you want to fix.")
        print("You will need to clone the SymPy wiki repo (git clone git@github.com:sympy/sympy.wiki.git).")
        sys.exit(1)

    release_notes_file = sys.argv[1]

    with open(release_notes_file) as f:
        release_notes = f.read()

    PRs = set()
    for m in re.finditer(r'https://github.com/sympy/sympy/pull/(\d+)', release_notes):
        PRs.add(m.group(1))

    login_kwargs = GitHub_login()

    pr_users = {}
    for pr in sorted(PRs):
        print(f"Getting PR #{pr}")
        pull_request = requests.get(f'https://api.github.com/repos/sympy/sympy/pulls/{pr}', **login_kwargs)
        GitHub_raise_for_status(pull_request)

        users = set()
        commits_url = pull_request.json()['commits_url']
        commits = requests.get(commits_url, **login_kwargs)
        GitHub_raise_for_status(commits)
        for commit in commits.json():
            if commit['author']:
                users.add(commit['author']['login'])

        if not users:
            users = {pull_request.json()['head']['user']['login']}

        pr_users[pr] = users

    for pr, users in sorted(pr_users.items()):
        if len(users) > 1:
            print(f"Authors for #{pr}: {format_authors(users)}")

AUTHOR = "[@{author}](https://github.com/{author})"

def format_authors(authors):
    if len(authors) == 1:
        authors_info = AUTHOR.format(author=authors[0])
    elif len(authors) == 2:
        authors_info = AUTHOR.format(author=authors[0]) + " and " + AUTHOR.format(author=authors[1])
    else:
        authors_info = ", ".join([AUTHOR.format(author=author) for author
            in authors[:-1]]) + ', and ' + AUTHOR.format(author=authors[-1])
    return authors_info

if __name__ == '__main__':
    sys.exit(main())
