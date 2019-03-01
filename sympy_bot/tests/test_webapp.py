"""
The tests here test the webapp by sending fake requests through a fake GH
object and checking that the right API calls were made.

Each fake request has just the API information currently needed by the webapp,
so if more API information is used, it will need to be added.

The GitHub API docs are useful:

- Pull request event (the main input to the webapp):
  https://developer.github.com/v3/activity/events/types/#pullrequestevent
- Pull request object (the 'pull_request' key to the pull request event):
  https://developer.github.com/v3/pulls/
- Commit objects (the output from the 'commits_url'):
  https://developer.github.com/v3/pulls/#list-commits-on-a-pull-request
- Comment objects (the output from the 'comments_url'):
  https://developer.github.com/v3/issues/comments/
- Contents objects (the output from the version_url):
  https://developer.github.com/v3/repos/contents/
- Statuses objects (the output from statuses_url):
  https://developer.github.com/v3/repos/statuses/

"""

import datetime
import base64
from subprocess import CalledProcessError
import os

from gidgethub import sansio

from ..webapp import router

# These are required for the tests to run properly
import pytest_aiohttp
pytest_aiohttp
import pytest_mock
pytest_mock

from pytest import mark, raises
parametrize = mark.parametrize

class FakeRateLimit:
    def __init__(self, *, remaining=5000, limit=5000, reset_datetime=None):
        self.remaining = remaining
        self.limit = limit
        now = datetime.datetime.now(datetime.timezone.utc)
        self.reset_datetime = reset_datetime or now + datetime.timedelta(hours=1)

class FakeGH:
    """
    Faked gh object

    Arguments:

    - getitem: dictionary mapping {url: result}, or None
    - getiter: dictionary mapping {url: result}, or None
    - rate_limit: FakeRateLimit object, or None
    - post: dictionary mapping {url: result}, or None
    - patch: dictionary mapping {url: result}, or None

    The results are stored in the properties

    - getiter_urls: list of urls called with getiter
    - getitem_urls: list of urls called with getitem
    - post_urls: list of urls called with post
    - post_data: list of the data input for each post
    - patch_urls: list of urls called with patch
    - patch_data: list of the data input for each patch

    """
    def __init__(self, *, getitem=None, getiter=None, rate_limit=None,
        post=None, patch=None):
        self._getitem_return = getitem
        self._getiter_return = getiter
        self._post_return = post
        self._patch_return = patch
        self.getiter_urls = []
        self.getitem_urls = []
        self.post_urls = []
        self.post_data = []
        self.patch_urls = []
        self.patch_data = []
        self.rate_limit = rate_limit or FakeRateLimit()

    async def getitem(self, url):
        self.getitem_urls.append(url)
        return self._getitem_return[url]

    async def getiter(self, url):
        self.getiter_urls.append(url)
        for item in self._getiter_return[url]:
            yield item

    async def post(self, url, *, data):
        self.post_urls.append(url)
        self.post_data.append(data)
        return self._post_return[url]

    async def patch(self, url, *, data):
        self.patch_urls.append(url)
        self.patch_data.append(data)
        return self._patch_return[url]

def _assert_gh_is_empty(gh):
    assert gh._getitem_return == None
    assert gh._getiter_return == None
    assert gh._post_return == None
    assert gh.getiter_urls == []
    assert gh.getitem_urls == []
    assert gh.post_urls == []
    assert gh.post_data == []
    assert gh.patch_urls == []
    assert gh.patch_data == []

def _event(data):
    return sansio.Event(data, event='pull_request', delivery_id='1')

version = '1.2.1'
release_notes_file = 'Release-Notes-for-1.2.1.md'
comments_url = 'https://api.github.com/repos/sympy/sympy/pulls/1/comments'
commits_url = 'https://api.github.com/repos/sympy/sympy/pulls/1/commits'
contents_url = 'https://api.github.com/repos/sympy/sympy/contents/{+path}'
version_url = 'https://api.github.com/repos/sympy/sympy/contents/sympy/release.py'
html_url = "https://github.com/sympy/sympy"
wiki_url = "https://github.com/sympy/sympy.wiki"
comment_html_url = 'https://github.com/sympy/sympy/pulls/1#issuecomment-1'
statuses_url = "https://api.github.com/repos/sympy/sympy/statuses/4a09f9f253c7372ec857774b1fe114b1266013fe"
existing_comment_url = "https://api.github.com/repos/sympy/sympy/issues/comments/1"
pr_number = 1

valid_PR_description = """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * new trig solvers
<!-- END RELEASE NOTES -->
"""

valid_PR_description_no_entry = """
<!-- BEGIN RELEASE NOTES -->
NO ENTRY
<!-- END RELEASE NOTES -->
"""

invalid_PR_description = """
<!-- BEGIN RELEASE NOTES -->

<!-- END RELEASE NOTES -->
"""

comment_body = """\
:white_check_mark:

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot) (version not found!). I'm here to help you write a release notes entry. Please read the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes).



Your release notes are in good order.

Here is what the release notes will look like:
* solvers
  * new trig solvers ([#1](https://github.com/sympy/sympy/pull/1) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))

This will be added to https://github.com/sympy/sympy/wiki/Release-Notes-for-1.2.1.

Note: This comment will be updated with the latest check if you edit the pull request. You need to reload the page to see it. <details><summary>Click here to see the pull request description that was parsed.</summary>


    <!-- BEGIN RELEASE NOTES -->
    * solvers
      * new trig solvers
    <!-- END RELEASE NOTES -->


</details><p>
"""


@parametrize('action', ['closed', 'synchronize', 'edited'])
async def test_closed_without_merging(action):
    gh = FakeGH()
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'closed',
            'merged': False,
            },
        }
    event_data['action'] = 'closed'

    event = _event(event_data)

    res = await router.dispatch(event, gh)
    assert res is None
    _assert_gh_is_empty(gh)

@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_good_new_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter)
    assert getitem_urls == list(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_good_existing_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter)
    assert getitem_urls == list(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment


@parametrize('action', ['closed'])
async def test_closed_with_merging(mocker, action):
    # Based on test_status_good_existing_comment

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter), getiter_urls
    assert getitem_urls == list(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url, existing_comment_url]
    assert len(patch_data) == 2
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert comment_body == comment
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment
    updated_comment = patch_data[1]['body']
    assert updated_comment.startswith(comment)
    assert "have been updated" in updated_comment

    assert update_wiki_called_kwargs == {
        'wiki_url': wiki_url,
        'release_notes_file': release_notes_file,
        'changelogs': {'solvers': ['* new trig solvers']},
        'pr_number': pr_number,
        'authors': ['asmeurer', 'certik'],
    }


@parametrize('action', ['closed'])
@parametrize('exception', [RuntimeError('error message'),
                           CalledProcessError(1, 'cmd')])
async def test_closed_with_merging_update_wiki_error(mocker, action, exception):
    # Based on test_closed_with_merging

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs
        raise exception

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)
    mocker.patch.dict(os.environ, {"GH_AUTH": "TESTING TOKEN"})

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        statuses_url: {},
        comments_url: {
            'html_url': comment_html_url,
        },
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    with raises(type(exception)):
        await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter), getiter_urls
    assert getitem_urls == list(getitem)
    assert post_urls == [statuses_url, comments_url, statuses_url]
    # Statuses data
    assert len(post_data) == 3
    assert post_data[0] == {
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }
    assert post_data[1].keys() == {'body'}
    error_message = post_data[1]['body']
    assert ':rotating_light:' in error_message
    assert 'ERROR' in error_message
    assert 'https://github.com/sympy/sympy-bot/issues' in error_message
    if isinstance(exception, RuntimeError):
        assert 'error message' in error_message
    else:
        assert "Command 'cmd' returned non-zero exit status 1." in error_message
    assert post_data[2] == {
        "state": "error",
        "target_url": comment_html_url,
        "description": "There was an error updating the release notes on the wiki.",
        "context": "sympy-bot/release-notes",
    }
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert comment_body == comment
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment

    assert update_wiki_called_kwargs == {
        'wiki_url': wiki_url,
        'release_notes_file': release_notes_file,
        'changelogs': {'solvers': ['* new trig solvers']},
        'pr_number': pr_number,
        'authors': ['asmeurer', 'certik'],
    }



@parametrize('action', ['closed'])
async def test_closed_with_merging_bad_status_error(mocker, action):
    # Based on test_closed_with_merging

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)
    mocker.patch.dict(os.environ, {"GH_AUTH": "TESTING TOKEN"})

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': invalid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {}
    post = {
        statuses_url: {},
        comments_url: {
            'html_url': comment_html_url,
        },
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter), getiter_urls
    assert getitem_urls == list(getitem)
    assert post_urls == [statuses_url, comments_url, statuses_url]
    # Statuses data
    assert len(post_data) == 3
    assert post_data[0] == {
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert post_data[1].keys() == {'body'}
    error_message = post_data[1]['body']
    assert ':rotating_light:' in error_message
    assert 'ERROR' in error_message
    assert 'https://github.com/sympy/sympy-bot/issues' in error_message
    assert "The pull request was merged even though the release notes bot had a failing status." in error_message

    assert post_data[2] == {
        "state": "error",
        "target_url": comment_html_url,
        "description": "There was an error updating the release notes on the wiki.",
        "context": "sympy-bot/release-notes",
    }
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "new trig solvers" not in comment
    assert "error" not in comment
    assert "There was an issue" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in invalid_PR_description:
        assert line in comment
    assert "good order" not in comment
    assert "No release notes were found" in comment, comment

    assert update_wiki_called_kwargs == {}


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_bad_new_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': invalid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {}
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter)
    assert getitem_urls == list(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "new trig solvers" not in comment
    assert "error" not in comment
    assert "There was an issue" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in invalid_PR_description:
        assert line in comment
    assert "good order" not in comment
    assert "No release notes were found" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_bad_existing_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': invalid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {}
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert getiter_urls == list(getiter)
    assert getitem_urls == list(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "new trig solvers" not in comment
    assert "error" not in comment
    assert "There was an issue" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in invalid_PR_description:
        assert line in comment
    assert "good order" not in comment
    assert "No release notes were found" in comment, comment


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_rate_limit_comment(action):
    # Based on test_status_good_new_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    now = datetime.datetime.now(datetime.timezone.utc)
    reset_datetime = now + datetime.timedelta(hours=1)
    rate_limit = FakeRateLimit(remaining=5, limit=1000, reset_datetime=reset_datetime)
    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, rate_limit=rate_limit)

    await router.dispatch(event, gh)

    # Everything else is already tested in test_status_good_new_comment()
    # above
    post_urls = gh.post_urls
    post_data = gh.post_data
    assert post_urls == [comments_url, statuses_url, comments_url]
    assert len(post_data) == 3
    assert post_data[2].keys() == {"body"}
    comment = post_data[2]["body"]
    assert ":warning:" in comment
    assert "5" in comment
    assert "1000" in comment
    assert str(reset_datetime) in comment


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_header_in_message(action):
    # Based on test_status_good_new_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * solver change
<!-- END RELEASE NOTES -->
"""
            },
            'sha': '174b8b37bc33e9eb29e710a233190d02a13bdb54',
        },
        {
            'author': {
                'login': 'certik',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
        # Test commits without a login
        {
            'author': {},
            'commit': {
                'message': "A good commit",
            },
            'sha': 'a109f824f4cb2b1dd97cf832f329d59da00d609a',
        },
    ]

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {}
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    # The rest is already tested in test_status_good_new_comment
    assert getiter_urls == list(getiter)
    assert getitem_urls == list(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    assert "good order" not in comment
    assert "174b8b37bc33e9eb29e710a233190d02a13bdb54" in comment
    assert "<!-- BEGIN RELEASE NOTES -->" in comment
    assert "<!-- END RELEASE NOTES -->" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []
