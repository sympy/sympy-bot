import datetime
import os
import base64

from aiohttp import web, ClientSession

from gidgethub import routing, sansio
from gidgethub.aiohttp import GitHubAPI

from .changelog import (get_changelog, update_release_notes, VERSION_RE,
                        get_release_notes_filename)

router = routing.Router()

USER = 'sympy-bot'

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

@router.register("pull_request", action="edited")
async def pull_request_edited(event, gh, *args, **kwargs):
    url = event.data["pull_request"]["comments_url"]
    number = event.data["pull_request"]["number"]
    # TODO: Get the full list of users with commits, not just the user who
    # opened the PR.
    users = [event.data['pull_request']['head']['user']['login']]
    contents_url = event.data['pull_request']['base']['repo']['contents_url']

    version_url = contents_url.replace('{+path}', 'sympy/release.py')

    comments = gh.getiter(url)
    # Try to find an existing comment to update
    existing_comment = None
    async for comment in comments:
        if comment['user']['login'] == USER:
            existing_comment = comment
            break

    status, message, changelogs = get_changelog(event.data['pull_request']['body'])

    release_notes_file = "!!ERROR!! Could not get the release notes filename!"
    if status:
        release_file = await gh.get(version_url)
        m = VERSION_RE.search(base64.b64decode(release_file['content']).decode('utf-8'))
        if not m:
            status = False
            message = """\
There was an error getting the version from the sympy/release.py file. Please
open an issue at https://github.com/sympy/sympy-bot/issues."""
        else:
            version = m.group()
            release_notes_file = get_release_notes_filename(version)

    status_message = "OK" if status else "NO GOOD"

    if status:
        fake_release_notes = """
## Authors
"""
        wiki_url = event.data['pull_request']['base']['repo']['html_url'] + '/wiki/' + release_notes_file

        updated_fake_release_notes = update_release_notes(fake_release_notes,
            changelogs, number, users).replace('## Authors', '').strip()
        message += f'\nHere is what the release notes will look like:\n{updated_fake_release_notes}\n\nThis will be added to {wiki_url}.'

    PR_message = f"""\
I am the SymPy bot. You have edited the pull request description.

The status is **{status_message}**

{message}

If you edit the description, be sure to reload the page to see my latest
status check!
"""

    if existing_comment:
        await gh.patch(existing_comment['url'], data={"body": PR_message})
    else:
        await gh.post(url, data={"body": PR_message})

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main_post)
    app.router.add_get("/", main_get)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
