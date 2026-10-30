import textwrap
import datetime
import os
import base64
from subprocess import CalledProcessError
from collections import defaultdict

from aiohttp import web, ClientSession

from gidgethub import routing, sansio, BadRequest
from gidgethub.aiohttp import GitHubAPI

from .changelog import (get_changelog, update_release_notes, VERSION_RE,
                        get_release_notes_filename, BEGIN_RELEASE_NOTES,
                        END_RELEASE_NOTES)
from .pr_template import check_ai_disclosure
from .update_wiki import update_wiki

router = routing.Router()

USER = 'sympy-bot'
RELEASE_FILE = 'sympy/release.py'
# The label on pull requests that are waiting for an AI disclosure. The label
# must exist in the repository.
AI_DISCLOSURE_LABEL = 'missing-ai-disclosure'
AI_DISCLOSURE_GRACE_HOURS = 48
# Hidden marker used to find the bot's warning comment
AI_DISCLOSURE_MARKER = '<!-- sympy-bot: missing AI disclosure -->'
# The author_association of someone who has not had a pull request merged. The
# opened webhook gives NONE for these authors, even though the REST API gives
# FIRST_TIME_CONTRIBUTOR for the same pull requests.
FIRST_TIME_ASSOCIATIONS = {'NONE', 'FIRST_TIME_CONTRIBUTOR', 'FIRST_TIMER'}

async def main_post(request):
    # read the GitHub webhook payload
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    print(f"Received {event.event} event with delivery_id={event.delivery_id}")
    async with ClientSession() as session:
        gh = GitHubAPI(session, USER, oauth_token=oauth_token, cache={})

        # call the appropriate callback for the event
        result = await router.dispatch(event, gh)

        # The bot only runs when it gets a webhook, so this is when it checks
        # whether the grace period has run out on any pull requests.
        if event.event == "pull_request":
            await close_expired_ai_disclosure_prs(event, gh)

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
        if event.data['action'] == "edited":
            await reopen_pr_if_ai_disclosure_fixed(event, gh)
        return

    if event.data['pull_request']['user']['login'] == "dependabot[bot]":
        await pull_request_noop(event, gh, status_message="This is a Dependabot PR. SymPy Bot not run.")
    else:
        await update_ai_disclosure_warning(event, gh)
        await pull_request_comment_release_notes(event, gh)
    await pull_request_comment_added_deleted(event, gh)
    await rate_limit_comment(event, gh)

async def pull_request_noop(event, gh, status_message=None):
    statuses_url = event.data['pull_request']['statuses_url']
    await gh.post(statuses_url, data=dict(
        state='success',
        description=status_message,
        context='sympy-bot/release-notes',
    ))

def has_ai_disclosure_label(event):
    labels = event.data['pull_request'].get('labels', [])
    return any(label['name'] == AI_DISCLOSURE_LABEL for label in labels)

async def remove_ai_disclosure_label(issue_url, gh):
    await gh.delete(f'{issue_url}/labels/{AI_DISCLOSURE_LABEL}')

async def withdraw_ai_disclosure_warning(issue_url, comments_url, gh):
    await remove_ai_disclosure_label(issue_url, gh)
    async for comment in gh.getiter(comments_url):
        if comment['user']['login'] == USER and AI_DISCLOSURE_MARKER in comment['body']:
            await gh.delete(comment['url'])

async def update_ai_disclosure_warning(event, gh):
    """
    Warn a first-time contributor who opens a pull request without an AI
    disclosure, and withdraw the warning once the disclosure is added.
    """
    pull_request = event.data['pull_request']
    action = event.data['action']
    issue_url = pull_request['issue_url']
    comments_url = pull_request['comments_url']

    if action == "opened" and pull_request.get('author_association') in FIRST_TIME_ASSOCIATIONS:
        status, message = check_ai_disclosure(pull_request['body'])
        if status:
            return
        await gh.post(issue_url + '/labels', data={'labels': [AI_DISCLOSURE_LABEL]})
        await gh.post(comments_url, data={"body": f"""\
{AI_DISCLOSURE_MARKER}
Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot). This pull request's description is missing something required by the [SymPy pull request template](https://github.com/sympy/sympy/blob/master/.github/PULL_REQUEST_TEMPLATE.md):

{message}

Please edit the pull request description to fix this. If it is not fixed within {AI_DISCLOSURE_GRACE_HOURS} hours, I will close this pull request. If that happens, you can still fix the description, and I will reopen it.
"""})
    elif has_ai_disclosure_label(event):
        if action == "reopened":
            # A maintainer reopened the pull request, so don't close it again.
            await remove_ai_disclosure_label(issue_url, gh)
        elif action == "edited" and check_ai_disclosure(pull_request['body'])[0]:
            await withdraw_ai_disclosure_warning(issue_url, comments_url, gh)

async def close_expired_ai_disclosure_prs(event, gh):
    """
    Close the pull requests that are still missing an AI disclosure after the
    grace period.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    grace_period = datetime.timedelta(hours=AI_DISCLOSURE_GRACE_HOURS)
    repo_url = event.data['repository']['url']

    async for issue in gh.getiter(f'{repo_url}/issues?labels={AI_DISCLOSURE_LABEL}&state=open'):
        created_at = datetime.datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
        if 'pull_request' not in issue or now - created_at < grace_period:
            continue
        # The webhook for the edit that added the disclosure may have been
        # missed, for instance, if it timed out while the bot was starting up.
        if check_ai_disclosure(issue['body'])[0]:
            await withdraw_ai_disclosure_warning(issue['url'], issue['comments_url'], gh)
            continue
        print(f"Closing PR #{issue['number']}, which has no AI disclosure.")
        await gh.post(issue['comments_url'], data={"body": f"""\
I am closing this pull request because its description still does not have an AI disclosure after {AI_DISCLOSURE_GRACE_HOURS} hours.

You do not need to open a new pull request. If you edit the description of this one to add the disclosure, I will reopen it.
"""})
        await gh.patch(issue['url'], data={'state': 'closed'})

async def reopen_pr_if_ai_disclosure_fixed(event, gh):
    """
    Reopen a pull request that the bot closed for not having an AI disclosure
    once the disclosure is added.
    """
    pull_request = event.data['pull_request']
    if not has_ai_disclosure_label(event) or not check_ai_disclosure(pull_request['body'])[0]:
        return

    # Contributors can't normally reopen a pull request that someone else
    # closed, so don't let this undo a close by a maintainer.
    closed_by = None
    async for issue_event in gh.getiter(pull_request['issue_url'] + '/events'):
        if issue_event['event'] == 'closed':
            closed_by = issue_event['actor']['login']
    if closed_by != USER:
        return

    await remove_ai_disclosure_label(pull_request['issue_url'], gh)
    comments_url = pull_request['comments_url']
    try:
        await gh.patch(pull_request['url'], data={'state': 'open'})
    except BadRequest:
        # For example, the branch was deleted or force pushed.
        await gh.post(comments_url, data={"body": "The AI disclosure looks good now, but I was not able to reopen this pull request. Please open a new pull request with the same changes."})
        raise
    await gh.post(comments_url, data={"body": "Thanks for adding the AI disclosure. I have reopened this pull request."})

async def pull_request_comment_release_notes(event, gh):
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

    users.add(event.data['pull_request']['head']['user']['login'])

    users = sorted(users)

    contents_url = event.data['pull_request']['base']['repo']['contents_url']
    version_url = contents_url.replace('{+path}', RELEASE_FILE)
    base_ref = event.data['pull_request']['base']['ref']

    comments = gh.getiter(comments_url)
    # Try to find an existing comment to update
    existing_comment_release_notes = None
    async for comment in comments:
        if comment['user']['login'] == USER:
            if "release notes entry" in comment['body']:
                existing_comment_release_notes = comment

    status, message, changelogs = get_changelog(event.data['pull_request']['body'])

    if status and header_in_message:
        status = False
        message = f"* The `{BEGIN_RELEASE_NOTES}` / `{END_RELEASE_NOTES}` block should go in the pull request description only, not the commit messages. It was found in the message for the commit {header_in_message}. See https://github.com/sympy/sympy/wiki/Development-workflow#changing-of-commit-messages for information on how to edit commit messages."

    gh_status = 'success' if status else 'failure'

    release_notes_file = "!!ERROR!! Could not get the release notes filename!"
    if status:
        try:
            release_file = await gh.getitem(version_url + f'?ref={base_ref}')
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

    release_notes_message = f"""\
{emoji_status[status] if status else ''}

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot). I'm here to help you write a release notes entry. Please read the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes).

"""
    if not status:
        release_notes_message += f"{emoji_status[status]} There was an issue with the release notes. **Please do not close this pull request;** instead edit the description after reading the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes)."

    release_notes_message += f"""

{message}

<details><summary>Click here to see the pull request description that was parsed.</summary>

{textwrap.indent(event.data['pull_request']['body'], '    ')}

</details><p>
"""

    if existing_comment_release_notes:
        comment = await gh.patch(existing_comment_release_notes['url'], data={"body": release_notes_message})
    else:
        comment = await gh.post(comments_url, data={"body": release_notes_message})

    statuses_url = event.data['pull_request']['statuses_url']
    await gh.post(statuses_url, data=dict(
        state=gh_status,
        target_url=comment['html_url'],
        description=status_message,
        context='sympy-bot/release-notes',
    ))

    return status, release_notes_file, changelogs, comment, users

async def rate_limit_comment(event, gh):
    comments_url = event.data["pull_request"]["comments_url"]
    rate_limit = gh.rate_limit
    remaining = rate_limit.remaining
    total = rate_limit.limit
    reset_datetime = rate_limit.reset_datetime

    if remaining <= 10:
        message = f"""\

**:warning::warning::warning:WARNING:warning::warning::warning:**: I am nearing my API limit. I have only {remaining} of {total} API requests left. They will reset on {reset_datetime} (UTC), which is in {reset_datetime - datetime.datetime.now(datetime.timezone.utc)}.

"""

        await gh.post(comments_url, data={"body": message})

async def pull_request_comment_added_deleted(event, gh):
    comments_url = event.data["pull_request"]["comments_url"]
    # TODO: Get the full list of users with commits, not just the user who
    # opened the PR.
    commits_url = event.data["pull_request"]["commits_url"]
    commits = gh.getiter(commits_url)
    added = defaultdict(list)
    deleted = defaultdict(list)

    async for commit in commits:
        # Workaround https://github.com/sympy/sympy-bot/issues/84
        try:
            com = await gh.getitem(commit['url'])
        except BadRequest:
            print(f"Warning: could not get commit {commit['sha']}")
            continue
        if len(com['parents']) > 1:
            # Merge commit
            continue
        for file in com['files']:
            if file['status'] == 'added':
                added[com['sha']].append(file)
            elif file['status'] == 'removed':
                deleted[com['sha']].append(file)

    comments = gh.getiter(comments_url)
    # Try to find an existing comment to update
    existing_comment = None
    # mentioned = []
    async for comment in comments:
        if comment['user']['login'] == USER:
            if "add or delete" in comment['body']:
                existing_comment = comment
                break
        # if f'@{USER}' in comment['body']:
        #     mentioned.append(comment)

    if added or deleted:
        # \U0001f7e0 is an orange circle. Don't include it here literally
        # because it causes issues in some editors. We set it as a level 3
        # header so it appears the same size as the GitHub :emojis:. It isn't
        # available as a :emoji: unfortunately.
        added_deleted_message = """\
### \U0001f7e0

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot). I've noticed that some of your commits add or delete files. Since this is sometimes done unintentionally, I wanted to alert you about it.

This is an experimental feature of SymPy Bot. If you have any feedback on it, please comment at https://github.com/sympy/sympy-bot/issues/75.
"""
        if added:
            added_deleted_message += """
The following commits **add new files**:
"""
        for sha, files in added.items():
            added_deleted_message += f"* {sha}:\n"
            for file in files:
                added_deleted_message += f"  - `{file['filename']}`\n"

        if deleted:
            added_deleted_message += """
The following commits **delete files**:
"""
        for sha, files in deleted.items():
            added_deleted_message += f"* {sha}:\n"
            for file in files:
                added_deleted_message += f"  - `{file['filename']}`\n"

        added_deleted_message += """
If these files were added/deleted on purpose, you can ignore this message.
"""
        # TODO: Allow users to whitelist files by @mentioning the bot. Then we
        # could make this give a failing status.

        if existing_comment:
            comment = await gh.patch(existing_comment['url'], data={"body": added_deleted_message})
        else:
            comment = await gh.post(comments_url, data={"body": added_deleted_message})
    elif existing_comment:
        # Files were added or deleted before but now they aren't, so delete
        # the comment
        await gh.delete(existing_comment['url'])

@router.register("pull_request", action="closed")
async def pull_request_closed(event, gh, *args, **kwargs):
    pr_number = event.data['pull_request']['number']
    print(f"PR #{pr_number} was {event.data['action']}.")
    if not event.data['pull_request']['merged']:
        print(f"PR #{pr_number} was closed without merging, skipping")
        return

    if event.data['pull_request']['user']['login'] == "dependabot[bot]":
        print(f"PR #{pr_number} was merged but is a Dependabot PR. SymPy Bot not run.")
        return

    status, release_notes_file, changelogs, comment, users = await pull_request_comment_release_notes(event, gh, *args, **kwargs)

    wiki_url = event.data['pull_request']['base']['repo']['html_url'] + '.wiki'
    release_notes_url = event.data['pull_request']['base']['repo']['html_url'] + '/wiki/' + release_notes_file[:-3] # Strip the .md for the URL

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
                comment = await gh.patch(comment['url'], data={"body": update_message})
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

    await rate_limit_comment(event, gh)

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
