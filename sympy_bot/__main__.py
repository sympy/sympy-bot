import os

from aiohttp import web, ClientSession

from gidgethub import routing, sansio
from gidgethub.aiohttp import GitHubAPI

router = routing.Router()

async def main(request):
    # read the GitHub webhook payload
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    async with ClientSession() as session:
        gh = GitHubAPI(session, "asmeurer",
                                  oauth_token=oauth_token)

        # call the appropriate callback for the event
        result = await router.dispatch(event, gh)

    return web.Response(status=200, text=str(result))

@router.register("pull_request", action="edited")
async def pull_request_edited(event, gh, *args, **kwargs):
    """ Whenever an issue is opened, greet the author and say thanks."""
    return event.data

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
