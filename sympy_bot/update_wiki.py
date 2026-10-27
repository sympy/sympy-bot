import os
import shlex
import sys
from subprocess import run as subprocess_run, PIPE, CalledProcessError

from .changelog import update_release_notes

# Modified from doctr.travis.run_command_hiding_token
def run(args, shell=False, check=True):
    """
    Run a command, printing the command and its output with the GH_AUTH token
    hidden.

    If check=True and the command fails, the captured output is printed
    before CalledProcessError is raised, so that the reason for the failure
    (e.g., the stderr from git) is visible in the logs.
    """
    token = os.environ.get("GH_AUTH").encode('utf-8')

    if not shell:
        command = ' '.join(map(shlex.quote, args))
    else:
        command = args

    command = command.replace(token.decode('utf-8'), '~'*len(token))
    print(command)
    sys.stdout.flush()

    if token:
        stdout = stderr = PIPE
    else:
        stdout = stderr = None
    p = subprocess_run(args, stdout=stdout, stderr=stderr, shell=shell)
    out = err = None
    if token:
        # XXX: Do this in a way that is streaming
        out, err = p.stdout, p.stderr
        out = out.replace(token, b"~"*len(token)).decode('utf-8')
        err = err.replace(token, b"~"*len(token)).decode('utf-8')
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    if check and p.returncode:
        # Use the token-hidden command and output in the exception, since
        # str(e) ends up in the logs and in the error comment on the PR.
        raise CalledProcessError(p.returncode, command, output=out, stderr=err)
    return p.returncode

GIT_IDENTITY_OPTIONS = ['-c', 'user.name=SymPy Bot',
                        '-c', 'user.email=sympy+bot@sympy.org']

def update_wiki(*, wiki_url, release_notes_file, changelogs, pr_number,
                authors):
    """
    Update the release notes wiki with the given release notes

    Assumes the token to push to the wiki is in the GH_AUTH environment variable.

    The git commands and their output are printed to the terminal. The token
    is automatically hidden from the output.

    Raises:

    - RuntimeError: If there was an error.
    - CalledProcessError: If there was an error with a git command

    Otherwise, it returns None.

    """
    run(['git', 'clone', wiki_url, '--depth', '1'], check=True)
    _, wiki = wiki_url.rsplit('/', 1)
    os.chdir(wiki)

    with open(release_notes_file, 'r') as f:
        rel_notes_txt = f.read()

    try:
        new_rel_notes_txt = update_release_notes(rel_notes_txt=rel_notes_txt,
        changelogs=changelogs, pr_number=pr_number, authors=authors)
    except Exception as e:
        raise RuntimeError(str(e)) from e

    with open(release_notes_file, 'w') as f:
        f.write(new_rel_notes_txt)

    run(['git', 'diff'], check=True)
    run(['git', 'add', release_notes_file], check=True)

    message = f"Update {release_notes_file} from PR #{pr_number}"
    # Pass the bot's identity for this command only, rather than writing it
    # to the global git config, so that running this locally does not
    # overwrite the user's own identity. Also disable commit signing in case
    # the local git config has it enabled.
    run(['git', *GIT_IDENTITY_OPTIONS, '-c', 'commit.gpgsign=false',
         'commit', '-m', message], check=True)

    # Supply the token via a credential helper rather than embedding it in
    # the URL. Embedding it in the URL broke in October 2026: libcurl's fix
    # for CVE-2026-94266 strips credentials from the effective URL, which git
    # (before 2.43.0-1ubuntu7.4) misinterprets as a redirect and then drops
    # the credentials, failing with "could not read Username". It also keeps
    # the token out of the command line, so it cannot leak into tracebacks.
    # The helper reads GH_AUTH from the environment of the git subprocess.
    credential_helper = (
        '!f() { echo username=x-access-token; echo "password=$GH_AUTH"; }; f'
    )

    # TODO: Use a deploy key to do this
    run(['git', '-c', 'credential.helper=', '-c',
         f'credential.helper={credential_helper}', 'push', wiki_url,
         'master'], check=True)
