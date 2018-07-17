import datetime
import os

from aiohttp import web, ClientSession

from gidgethub import routing, sansio
from gidgethub.aiohttp import GitHubAPI

from .changelog import get_changelog

router = routing.Router()

user = 'sympy-bot'

graphql_url = 'https://api.github.com/graphql'

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
    # We have to use the GraphQL API to update a pull request review
    user = event.data['pull_request']['user']['login']
    repo = event.data['pull_request']['head']['repo']['name']
    number = event.data['pull_request']['number']
    # Avoid f-string formatting, as that requires escaping every {
    get_review_id_query = """
    query FindReview {
      repository(owner: "%(user)s", name: "%(repo)s") {
        pullRequest(number: %(number)s) {
          reviews(first: 100) {
            edges {
              node {
                author {login}
                id
              }
            }
          }
        }
      }
    }
    """ % dict(user=user, repo=repo, number=number)

    r = await gh.post(graphql_url, data={'query': get_review_id_query})
    reviews = r['data']['repository']['pullRequest']['reviews']['edges']
    print(reviews)
    # Try to find an existing comment to update
    existing_review = None
    for review in reviews:
        if review['node']['author']['login'] == user:
            existing_review = review['node']['id']
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

    state = "APPROVE" if status else "REQUEST_CHANGES"

    if existing_review:
        update_review_query = """
        mutation UpdateReview {
          updatePullRequestReview(input: {pullRequestReviewId: "%(existing_review)s==", body: "%(body)s"}) {
            pullRequestReview {
              updatedAt
            }
          }
        }
        """ % dict(existing_review=existing_review, body=PR_message)

        r = await gh.post(graphql_url, data={'query': update_review_query})
    else:
        url = event.data["pull_request"]["url"] + '/reviews'
        await gh.post(url, data={"body": PR_message, 'event': state})

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main_post)
    app.router.add_get("/", main_get)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
