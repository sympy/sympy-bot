import subprocess
import os

# This is required for the tests to run properly
import pytest_mock
pytest_mock

from ..update_wiki import update_wiki, run

token = "TOKEN"

def test_run(mocker, capsys):
    mocker.patch.dict(os.environ, {"GH_AUTH": token})

    run(['echo', token])
    captured = capsys.readouterr()
    assert captured.out == 'echo ~~~~~\n~~~~~\n\n'
    assert captured.err == ''
