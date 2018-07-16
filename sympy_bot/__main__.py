import datetime
import os

from aiohttp import web, ClientSession

from gidgethub import routing, sansio
from gidgethub.aiohttp import GitHubAPI

from .changelog import get_changelog

router = routing.Router()

user = 'sympy-bot'

async def main_post(request):
    # read the GitHub webhook payload
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    async with ClientSession() as session:
        gh = GitHubAPI(session, user, oauth_token=oauth_token)

        # call the appropriate callback for the event
        result = await router.dispatch(event, gh)

    return web.Response(status=200, text=str(result))

async def main_get(request):
    oauth_token = os.environ.get("GH_AUTH")

    async with ClientSession() as session:
        gh = GitHubAPI(session, user, oauth_token=oauth_token)
        await gh.getitem("/rate_limit")
        rate_limit = gh.rate_limit
        remaining = rate_limit.remaining
        total = rate_limit.limit
        reset_datetime = rate_limit.reset_datetime

    return web.Response(status=200, text=f"You have {remaining} of {total} GitHub API requests remaining. They will reset on {reset_datetime} (UTC), which is in {reset_datetime - datetime.datetime.now(datetime.timezone.utc)}.")

@router.register("pull_request", action="edited")
async def pull_request_edited(event, gh, *args, **kwargs):
    url = event.data["pull_request"]["url"] + '/reviews'

    comments = gh.getiter(url)
    # Try to find an existing comment to update
    existing_comment = None
    async for comment in comments:
        if comment['user']['login'] == user:
            existing_comment = comment
            break

    status, message, changelogs = get_changelog(event.data['pull_request']['body'])

    status_message = "OK" if status else "NO GOOD"

    PR_message = f"""\
I am the SymPy bot. You have edited the pull request description.

The status is **{status_message}**

{message}

Here are the changelog entries: {changelogs}

If you edit the description, be sure to reload the page to see my latest
status check!
"""

    event = "APPROVE" if status else "REQUEST_CHANGES"

    if existing_comment:
        await gh.patch(existing_comment['url'], data={"body": PR_message,
            'event': event})
    else:
        await gh.post(url, data={"body": PR_message, 'event': event})

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main_post)
    app.router.add_get("/", main_get)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
