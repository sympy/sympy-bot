import datetime

from gidgethub import sansio

from ..webapp import router

# This is required for the tests to run properly
import pytest_aiohttp
pytest_aiohttp

class FakeRateLimit:
    def __init__(self, *, remaining=5000, limit=5000, reset_datetime=None):
        self.remaining = remaining
        self.limit = limit
        now = datetime.datetime.now(datetime.timezone.utc)
        self.reset_datetime = reset_datetime or now + datetime.timedelta(hours=1)

class FakeGH:
    def __init__(self, *, getitem=None, getiter=None, rate_limit=None, post=None):
        self._getitem = getitem
        self._getiter = getiter
        self._post = post
        self.getiter_url = None
        self.getitem_url = None
        self.post_urls = []
        self.post_data = []
        self.rate_limit = rate_limit or FakeRateLimit()

    async def getitem(self, url):
        self.getitem_url = url
        return self._getitem_return[self.getitem_url]

    async def getiter(self, url):
        self.getiter_url = url
        for item in self._getiter_return:
            yield item

    async def post(self, url, *, data):
        self.post_urls.append(url)
        self.post_data.append(data)
        return self._post

def _assert_gh_is_empty(gh):
    assert gh._getitem == None
    assert gh._getiter == None
    assert gh._post == None
    assert gh.getiter_url == None
    assert gh.getitem_url == None
    assert gh.post_urls == []
    assert gh.post_data == []

def _event(data):
    return sansio.Event(data, event='pull_request', delivery_id='1')

async def test_closed_without_merging():
    gh = FakeGH()
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'closed',
            'merged': False,
            },
        }
    closed_event_data = event_data.copy()
    closed_event_data['action'] = 'closed'

    synchronize_event_data = event_data.copy()
    synchronize_event_data['action'] = 'synchronize'

    edited_event_data = event_data.copy()
    edited_event_data['action'] = 'edited'

    closed_event = _event(closed_event_data)
    synchronize_event = _event(synchronize_event_data)
    edited_event = _event(edited_event_data)

    for event in [closed_event, synchronize_event, edited_event]:
        res = await router.dispatch(event, gh)
        assert res is None
        _assert_gh_is_empty(gh)
