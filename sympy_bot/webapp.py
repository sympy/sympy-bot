import textwrap
import datetime
import os
import base64
from subprocess import CalledProcessError

from aiohttp import web, ClientSession

from gidgethub import routing, sansio, BadRequest
from gidgethub.aiohttp import GitHubAPI

from .changelog import (get_changelog, update_release_notes, VERSION_RE,
                        get_release_notes_filename, BEGIN_RELEASE_NOTES,
                        END_RELEASE_NOTES)
from .update_wiki import update_wiki

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

    return web.Response(status=200, text=f"SymPy Bot has {remaining} of {total} GitHub API requests remaining. They will reset on {reset_datetime} (UTC), which is in {reset_datetime - datetime.datetime.now(datetime.timezone.utc)}.")

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
    header_in_message = False
    async for commit in commits:
        if commit['author']:
            users.add(commit['author']['login'])
        message = commit['commit']['message']
        if BEGIN_RELEASE_NOTES in message or END_RELEASE_NOTES in message:
            header_in_message = commit['sha']

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

    if status and header_in_message:
        status = False
        message = f"* The `{BEGIN_RELEASE_NOTES}` / `{END_RELEASE_NOTES}` block should go in the pull request description only, not the commit messages. It was found in the message for the commit {header_in_message}. See https://github.com/sympy/sympy/wiki/Development-workflow#changing-of-commit-messages for information on how to edit commit messages."

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

    status_message = "The release notes look OK" if status else "The release notes check failed"

    emoji_status = {
        True: ':white_check_mark:',
        False: ':x:',
        }

    if status:
        fake_release_notes = """
## Changes

## Authors
"""
        release_notes_url = event.data['pull_request']['base']['repo']['html_url'] + '/wiki/' + release_notes_file[:-3] # Strip the .md for the URL

        try:
            updated_fake_release_notes = update_release_notes(rel_notes_txt=fake_release_notes,
                changelogs=changelogs, pr_number=number,
                authors=users).replace('## Authors', '').replace("## Changes", '').strip()
        except Exception as e:
            status = False
            status_message = "ERROR"
            message += f"""

There was an error processing the release notes, which most likely indicates a bug in the bot. Please open an issue at https://github.com/sympy/sympy-bot/issues. The error was: {e}

"""
        else:
            if changelogs:
                message += f'\n\nHere is what the release notes will look like:\n{updated_fake_release_notes}\n\nThis will be added to {release_notes_url}.'

    PR_message = f"""\
{emoji_status[status] if status else ''}

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot) ({BOT_VERSION}). I'm here to help you write a release notes entry. Please read the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes).

"""
    if not status:
        PR_message += f"{emoji_status[status]} There was an issue with the release notes. **Please do not close this pull request;** instead edit the description after reading the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes)."

    PR_message += f"""

{message}

Note: This comment will be updated with the latest check if you edit the pull request. You need to reload the page to see it. <details><summary>Click here to see the pull request description that was parsed.</summary>

{textwrap.indent(event.data['pull_request']['body'], '    ')}

</details><p>
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

    return status, release_notes_file, changelogs, comment

@router.register("pull_request", action="closed")
async def pull_request_closed(event, gh, *args, **kwargs):
    pr_number = event.data['pull_request']['number']
    print(f"PR #{pr_number} was {event.data['action']}.")
    if not event.data['pull_request']['merged']:
        print(f"PR #{pr_number} was closed without merging, skipping")
        return

    status, release_notes_file, changelogs, comment = await pull_request_comment(event, gh, *args, **kwargs)

    wiki_url = event.data['pull_request']['base']['repo']['html_url'] + '.wiki'
    release_notes_url = event.data['pull_request']['base']['repo']['html_url'] + '/wiki/' + release_notes_file[:-3] # Strip the .md for the URL

    users = [event.data['pull_request']['head']['user']['login']]
    number = event.data["pull_request"]["number"]

    if status:
        if changelogs:
            try:
                update_wiki(
                    wiki_url=wiki_url,
                    release_notes_file=release_notes_file,
                    changelogs=changelogs,
                    pr_number=number,
                    authors=users,
                )
                update_message = comment['body'] + f"""

**Update**

The release notes on the [wiki]({release_notes_url}) have been updated.
"""
                comment = await gh.post(comment['url'], data={"body": update_message})
            except RuntimeError as e:
                await error_comment(event, gh, e.args[0])
                raise
            except CalledProcessError as e:
                await error_comment(event, gh, str(e))
                raise
        else:
            print(f"PR #{pr_number} was merged with no change log entries.")
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
