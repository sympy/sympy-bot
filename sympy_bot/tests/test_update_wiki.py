import os
from subprocess import CalledProcessError, run as subprocess_run

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

def test_run_failure(mocker, capsys):
    mocker.patch.dict(os.environ, {"GH_AUTH": token})

    # The output should be printed (with the token hidden) before the
    # exception is raised, so that the cause of the failure is visible in
    # the logs.
    with pytest.raises(CalledProcessError) as excinfo:
        run(['sh', '-c', f'echo out {token}; echo err {token} >&2; exit 3'])
    captured = capsys.readouterr()
    assert captured.out == 'sh -c \'echo out ~~~~~; echo err ~~~~~ >&2; exit 3\'\nout ~~~~~\n\n'
    assert captured.err == 'err ~~~~~\n\n'
    e = excinfo.value
    assert e.returncode == 3
    assert e.stderr == 'err ~~~~~\n'
    assert e.output == 'out ~~~~~\n'
    assert token not in str(e)
    assert token not in e.cmd

    # check=False should not raise
    assert run(['sh', '-c', 'exit 3'], check=False) == 3

def test_update_wiki_push_uses_credential_helper(mocker, tmp_path, monkeypatch):
    mocker.patch.dict(os.environ, {"GH_AUTH": token})
    monkeypatch.chdir(tmp_path)

    wiki_url = 'https://github.com/sympy/sympy-bot.wiki'
    calls = []
    def fake_run(args, shell=False, check=True):
        calls.append(args)
        if args[:2] == ['git', 'clone']:
            os.mkdir(tmp_path / 'sympy-bot.wiki')
            with open(tmp_path / 'sympy-bot.wiki' / 'Release-Notes-Tests.md', 'w') as f:
                f.write("## Changes\n\n## Authors\n")
        return 0
    mocker.patch('sympy_bot.update_wiki.run', fake_run)

    update_wiki(
        wiki_url=wiki_url,
        release_notes_file='Release-Notes-Tests.md',
        changelogs={'other': ['* Release notes update']},
        pr_number='14942',
        authors=['asmeurer'],
    )

    # The bot's identity must be passed per command, never written to the
    # global git config (which would clobber the identity of whoever runs
    # this locally).
    assert not any('--global' in call for call in calls)
    commit = [call for call in calls if 'commit' in call][0]
    assert '-c' in commit
    assert 'user.name=SymPy Bot' in commit
    assert 'user.email=sympy+bot@sympy.org' in commit
    assert 'commit.gpgsign=false' in commit

    push = calls[-1]
    assert push[0] == 'git'
    assert push[-3:] == ['push', wiki_url, 'master']
    # The token must not appear on the command line at all. It is supplied
    # via a credential helper that reads GH_AUTH from the environment.
    assert not any(token in arg for arg in push)
    helpers = [arg for arg in push if arg.startswith('credential.helper=!')]
    assert len(helpers) == 1
    assert '$GH_AUTH' in helpers[0]

@pytest.mark.skipif(True, reason="The update wiki test needs to be updated. See https://github.com/sympy/sympy-bot/issues/98")
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

def test_update_wiki_local_repo(mocker, tmp_path, monkeypatch):
    """
    Run update_wiki for real against a local bare repository standing in for
    the wiki, and check that it commits as the bot without touching the
    global git config.
    """
    mocker.patch.dict(os.environ, {"GH_AUTH": token})
    # Isolate the global git config so the test neither reads the user's
    # config (e.g. commit signing) nor can modify it.
    global_config = tmp_path / 'gitconfig'
    global_config.write_text('')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(global_config))

    def git(*args, cwd):
        return subprocess_run(['git', *args], cwd=cwd, check=True,
                              capture_output=True, text=True).stdout

    # Create a "remote" bare repo named like a GitHub wiki, with one commit
    # on master containing the release notes file.
    remote = tmp_path / 'remote' / 'sympy-bot.wiki'
    remote.parent.mkdir()
    git('init', '--bare', '-b', 'master', str(remote), cwd=tmp_path)
    seed = tmp_path / 'seed'
    git('clone', '-q', str(remote), str(seed), cwd=tmp_path)
    (seed / 'Release-Notes-Tests.md').write_text("## Changes\n\n## Authors\n")
    git('add', 'Release-Notes-Tests.md', cwd=seed)
    git('-c', 'user.name=Seed', '-c', 'user.email=seed@example.com',
        '-c', 'commit.gpgsign=false', 'commit', '-q', '-m', 'seed', cwd=seed)
    git('push', '-q', 'origin', 'master', cwd=seed)

    workdir = tmp_path / 'work'
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    update_wiki(
        wiki_url=str(remote),
        release_notes_file='Release-Notes-Tests.md',
        changelogs={'other': ['* Release notes update']},
        pr_number='14942',
        authors=['asmeurer'],
    )

    log = git('log', '--format=%an <%ae> %s', 'master', cwd=remote)
    assert log.splitlines()[0] == 'SymPy Bot <sympy+bot@sympy.org> Update Release-Notes-Tests.md from PR #14942'
    contents = git('show', 'master:Release-Notes-Tests.md', cwd=remote)
    assert '[#14942]' in contents
    assert global_config.read_text() == ''
