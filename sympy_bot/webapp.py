import textwrap
import datetime
import os
import base64
import urllib
import sys
import shlex
from subprocess import run as subprocess_run, CalledProcessError, PIPE

from aiohttp import web, ClientSession

from gidgethub import routing, sansio, BadRequest
from gidgethub.aiohttp import GitHubAPI

from .changelog import (get_changelog, update_release_notes, VERSION_RE,
                        get_release_notes_filename)

router = routing.Router()

USER = 'sympy-bot'
RELEASE_FILE = 'sympy/release.py'
BOT_VERSION = os.environ.get('HEROKU_RELEASE_VERSION', 'version not found!')

async def main_post(request):
    # read the GitHub webhook payload
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    async with ClientSession() as session:
        gh = GitHubAPI(session, USER, oauth_token=oauth_token)

        # call the appropriate callback for the event
        result = await router.dispatch(event, gh)

    return web.Response(status=200, text=str(result))

async def main_get(request):
    oauth_token = os.environ.get("GH_AUTH")

    async with ClientSession() as session:
        gh = GitHubAPI(session, USER, oauth_token=oauth_token)
        await gh.getitem("/rate_limit")
        rate_limit = gh.rate_limit
        remaining = rate_limit.remaining
        total = rate_limit.limit
        reset_datetime = rate_limit.reset_datetime

    return web.Response(status=200, text=f"You have {remaining} of {total} GitHub API requests remaining. They will reset on {reset_datetime} (UTC), which is in {reset_datetime - datetime.datetime.now(datetime.timezone.utc)}.")

@router.register("pull_request", action="opened")
@router.register("pull_request", action="reopened")
@router.register("pull_request", action="edited")
@router.register("pull_request", action="synchronize")
async def pull_request_edited(event, gh, *args, **kwargs):
    pr_number = event.data['pull_request']['number']
    print(f"PR #{pr_number} was {event.data['action']}.")
    if event.data['pull_request']['state'] == "closed":
        print(f"PR #{pr_number} is closed, skipping")
        return

    await pull_request_comment(event, gh)

async def pull_request_comment(event, gh):
    comments_url = event.data["pull_request"]["comments_url"]
    number = event.data["pull_request"]["number"]
    # TODO: Get the full list of users with commits, not just the user who
    # opened the PR.
    commits_url = event.data["pull_request"]["commits_url"]
    commits = gh.getiter(commits_url)
    users = set()
    async for commit in commits:
        if commit['author']:
            users.add(commit['author']['login'])

    if not users:
        users = {event.data['pull_request']['head']['user']['login']}

    users = sorted(users)
    contents_url = event.data['pull_request']['base']['repo']['contents_url']

    version_url = contents_url.replace('{+path}', RELEASE_FILE)

    comments = gh.getiter(comments_url)
    # Try to find an existing comment to update
    existing_comment = None
    async for comment in comments:
        if comment['user']['login'] == USER:
            existing_comment = comment
            break

    status, message, changelogs = get_changelog(event.data['pull_request']['body'])

    gh_status = 'success' if status else 'failure'

    release_notes_file = "!!ERROR!! Could not get the release notes filename!"
    if status:
        try:
            release_file = await gh.getitem(version_url)
            m = VERSION_RE.search(base64.b64decode(release_file['content']).decode('utf-8'))
        except BadRequest: # file not found
            m = False
        if not m:
            status = False
            gh_status = 'error'
            message = f"""\
There was an error getting the version from the `{RELEASE_FILE}` file. Please open an issue at https://github.com/sympy/sympy-bot/issues."""
        else:
            version = m.group()
            release_notes_file = get_release_notes_filename(version)

    status_message = "Release notes look OK" if status else "Release notes check failed"

    emoji_status = {
        True: ':white_check_mark:',
        False: ':x:',
        }

    if status:
        fake_release_notes = """
## Authors
"""
        wiki_url = event.data['pull_request']['base']['repo']['html_url'] + '/wiki/' + release_notes_file[:-3] # Strip the .md for the URL

        try:
            updated_fake_release_notes = update_release_notes(rel_notes_txt=fake_release_notes,
                changelogs=changelogs, pr_number=number,
                authors=users).replace('## Authors', '').strip()
        except Exception as e:
            status = False
            status_message = "ERROR"
            message += f"""

There was an error processing the release notes, which most likely indicates a bug in the bot. Please open an issue at https://github.com/sympy/sympy-bot/issues. The error was: {e}

"""
        else:
            if changelogs:
                message += f'\n\nHere is what the release notes will look like:\n{updated_fake_release_notes}\n\nThis will be added to {wiki_url}.'

    PR_message = f"""\
{emoji_status[status]}

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot) ({BOT_VERSION}). I'm here to make sure this pull request has a release notes entry. Please read the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes). <details><summary>Click here to see the pull request description that was parsed.</summary>

{textwrap.indent(event.data['pull_request']['body'], '    ')}

</details><p>

"""
    if not status:
        PR_message += "There was an issue with the release notes."

    PR_message += f"""

{message}

Note: This comment will be updated with the latest check if you edit the pull request. You need to reload the page to see it.

"""

    if existing_comment:
        comment = await gh.patch(existing_comment['url'], data={"body": PR_message})
    else:
        comment = await gh.post(comments_url, data={"body": PR_message})

    statuses_url = event.data['pull_request']['statuses_url']
    await gh.post(statuses_url, data=dict(
        state=gh_status,
        target_url=comment['html_url'],
        description=status_message,
        context='sympy-bot/release-notes',
    ))

    rate_limit = gh.rate_limit
    remaining = rate_limit.remaining
    total = rate_limit.limit
    reset_datetime = rate_limit.reset_datetime

    if remaining <= 10:
        message = f"""\

**:warning::warning::warning:WARNING:warning::warning::warning:**: I am nearing my API limit. I have only {remaining} of {total} API requests left. They will reset on {reset_datetime} (UTC), which is in {reset_datetime - datetime.datetime.now(datetime.timezone.utc)}.

"""

        comment = await gh.post(comments_url, data={"body": message})

    return status, release_notes_file, changelogs

@router.register("pull_request", action="closed")
async def pull_request_closed(event, gh, *args, **kwargs):
    pr_number = event.data['pull_request']['number']
    print(f"PR #{pr_number} was {event.data['action']}.")
    if not event.data['pull_request']['merged']:
        print("PR", pr_number, "was closed without merging, skipping")
        return

    status, release_notes_file, changelogs = await pull_request_comment(event, gh, *args, **kwargs)

    wiki_url = event.data['pull_request']['base']['repo']['html_url'] + '.wiki'
    users = [event.data['pull_request']['head']['user']['login']]
    number = event.data["pull_request"]["number"]

    if status:
        try:
            update_wiki(
                wiki_url=wiki_url,
                release_notes_file=release_notes_file,
                changelogs=changelogs,
                pr_number=number,
                authors=users,
            )
        except RuntimeError as e:
            await error_comment(event, gh, e.args[0])
            raise
        except CalledProcessError as e:
            await error_comment(event, gh, str(e))
            raise
    else:
        message = "The pull request was merged even though the release notes bot had a failing status."
        await error_comment(event, gh, message)

async def error_comment(event, gh, message):
    """
    Add a new comment with an error message. For use when updating the release
    notes fails.
    """
    token = os.environ.get("GH_AUTH")
    message = message.replace(token, '~~~TOKEN~~~')

    error_message = f"""\

**:rotating_light::rotating_light::rotating_light:ERROR:rotating_light::rotating_light::rotating_light:** There was an error automatically updating the release notes. Normally it should not have been possible to merge this pull request. You might want to open an issue about this at https://github.com/sympy/sympy-bot/issues.

In the meantime, you will need to update the release notes on the wiki manually.

The error message was: {message}
"""

    url = event.data["pull_request"]["comments_url"]
    comment = await gh.post(url, data={"body": error_message})

    statuses_url = event.data['pull_request']['statuses_url']
    await gh.post(statuses_url, data=dict(
        state='error',
        target_url=comment['html_url'],
        description='There was an error updating the release notes on the wiki.',
        context='sympy-bot/release-notes',
    ))

# Modified from doctr.travis.run_command_hiding_token
def run(args, shell=False, check=True):
    token = os.environ.get("GH_AUTH").encode('utf-8')

    if not shell:
        command = ' '.join(map(shlex.quote, args))
    else:
        command = args

    command = command.replace(token.decode('utf-8'), '~'*len(token))
    print(command)
    sys.stdout.flush()

    if token:
        stdout = stderr = PIPE
    else:
        stdout = stderr = None
    p = subprocess_run(args, stdout=stdout, stderr=stderr, shell=shell, check=check)
    if token:
        # XXX: Do this in a way that is streaming
        out, err = p.stdout, p.stderr
        out = out.replace(token, b"~"*len(token))
        err = err.replace(token, b"~"*len(token))
        if out:
            print(out.decode('utf-8'))
        if err:
            print(err.decode('utf-8'), file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    return p.returncode

def update_wiki(*, wiki_url, release_notes_file, changelogs, pr_number,
                authors):
    run(['git', 'config', '--global', 'user.email', "sympy+bot@sympy.org"])
    run(['git', 'config', '--global', 'user.name', "SymPy Bot"])

    run(['git', 'clone', wiki_url, '--depth', '1'], check=True)
    _, wiki = wiki_url.rsplit('/', 1)
    os.chdir(wiki)

    with open(release_notes_file, 'r') as f:
        rel_notes_txt = f.read()

    try:
        new_rel_notes_txt = update_release_notes(rel_notes_txt=rel_notes_txt,
        changelogs=changelogs, pr_number=pr_number, authors=authors)
    except Exception as e:
        raise RuntimeError(str(e)) from e

    with open(release_notes_file, 'w') as f:
        f.write(new_rel_notes_txt)

    run(['git', 'diff'], check=True)
    run(['git', 'add', release_notes_file], check=True)

    message = f"Update {release_notes_file} from PR #{pr_number}"
    run(['git', 'commit', '-m', message], check=True)

    parsed_url = list(urllib.parse.urlparse(wiki_url))
    parsed_url[1] = os.environ.get("GH_AUTH") + '@' + parsed_url[1]
    auth_url = urllib.parse.urlunparse(parsed_url)

    # TODO: Use a deploy key to do this
    run(['git', 'push', auth_url, 'master'], check=True)
