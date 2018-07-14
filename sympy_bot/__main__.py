import os

from aiohttp import web, ClientSession

from gidgethub import routing, sansio
from gidgethub.aiohttp import GitHubAPI

router = routing.Router()

user = 'asmeurer'

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
    return web.Response(status=200, text="SymPy Bot")

@router.register("pull_request", action="edited")
async def pull_request_edited(event, gh, *args, **kwargs):
    """ Whenever an issue is opened, greet the author and say thanks."""
    url = event.data["pull_request"]["comments_url"]

    message = "I am the SymPy bot. You have edited the pull request description."
    await gh.post(url, data={"body": message})

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main_post)
    app.router.add_get("/", main_get)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
