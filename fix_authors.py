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

from sympy_bot.changelog import format_authors

from doctr.local import GitHub_login, GitHub_raise_for_status

def reauth_GitHub_raise_for_status(r, login_kwargs):
    if r.status_code == 401 and r.headers.get('X-GitHub-OTP'):
        auth = login_kwargs['auth']
        print("You must provide a new 2FA code")
        login_kwargs.update(GitHub_login(username=auth.username, password=auth.password))
    else:
        GitHub_raise_for_status(r)

def get(url, kwargs):
    while True:
        r = requests.get(url, **kwargs)
        reauth_GitHub_raise_for_status(r, kwargs)
        if r.status_code == 401 and r.headers.get('X-GitHub-OTP'):
            continue
        return r

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

    print(f"Found {len(PRs)} PRs, from #{min(PRs, key=int)} to #{max(PRs, key=int)}")

    pr_users = {}
    for i, pr in enumerate(sorted(PRs, key=int)):
        print(f"Getting PR #{pr}: {i+1}/{len(PRs)}")
        pull_request = get(f'https://api.github.com/repos/sympy/sympy/pulls/{pr}', login_kwargs)

        users = set()
        commits_url = pull_request.json()['commits_url']
        commits = get(commits_url, login_kwargs)
        for commit in commits.json():
            if commit['author']:
                users.add(commit['author']['login'])

        if not users:
            users = {pull_request.json()['head']['user']['login']}

        pr_users[pr] = users

    for pr in sorted(pr_users, key=int):
        users = pr_users[pr]
        if len(users) > 1:
            authors = format_authors(sorted(users, key=str.lower))
            print(f"Fixing authors for #{pr}: {authors}")
            release_re = rf'(?m)(\(\[#{pr}\]\(https://github.com/sympy/sympy/pull/{pr}\) by ).*\)$'
            repl = rf'\1{authors}'
            release_notes, n = re.subn(release_re, repl, release_notes)
            if n == 0:
                print(f"WARNING: Could not fix the authors for PR #{pr}.")

    print("Updating the release notes file.")
    with open(release_notes_file, 'w') as f:
        f.write(release_notes)

if __name__ == '__main__':
    sys.exit(main())
