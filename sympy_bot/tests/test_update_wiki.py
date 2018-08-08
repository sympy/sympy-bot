import os

import pytest
# This is required for the tests to run properly
import pytest_mock
pytest_mock

from ..update_wiki import update_wiki, run

token = "TOKEN"

TESTING_TOKEN = os.environ.get('TESTING_TOKEN', None)

def test_run(mocker, capsys):
    mocker.patch.dict(os.environ, {"GH_AUTH": token})

    run(['echo', token])
    captured = capsys.readouterr()
    assert captured.out == 'echo ~~~~~\n~~~~~\n\n'
    assert captured.err == ''

@pytest.mark.skipif(not TESTING_TOKEN, reason="No API token present")
def test_update_wiki(mocker):
    mocker.patch.dict(os.environ, {"GH_AUTH": TESTING_TOKEN})

    travis_build = os.environ.get("TRAVIS_JOB_ID")
    travis_url = f"https://travis-ci.org/sympy/sympy-bot/builds/{travis_build}" if travis_build else "unknown"
    update_wiki(
        wiki_url='https://github.com/sympy/sympy-bot.wiki',
        release_notes_file='Release-Notes-Tests.md',
        changelogs={'other': [f'* Release notes update from {travis_url}']},
        pr_number='14942',
        authors=['asmeurer'],
    )
