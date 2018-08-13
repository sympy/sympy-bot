import urllib
import os
import shlex
import sys
from subprocess import run as subprocess_run, PIPE

from .changelog import update_release_notes

# Modified from doctr.travis.run_command_hiding_token
def run(args, shell=False, check=True):
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
    p = subprocess_run(args, stdout=stdout, stderr=stderr, shell=shell, check=check)
    if token:
        # XXX: Do this in a way that is streaming
        out, err = p.stdout, p.stderr
        out = out.replace(token, b"~"*len(token))
        err = err.replace(token, b"~"*len(token))
        if out:
            print(out.decode('utf-8'))
        if err:
            print(err.decode('utf-8'), file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    return p.returncode

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
    run(['git', 'config', '--global', 'user.email', "sympy+bot@sympy.org"])
    run(['git', 'config', '--global', 'user.name', "SymPy Bot"])

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
    run(['git', 'commit', '-m', message], check=True)

    parsed_url = list(urllib.parse.urlparse(wiki_url))
    parsed_url[1] = os.environ.get("GH_AUTH") + '@' + parsed_url[1]
    auth_url = urllib.parse.urlunparse(parsed_url)

    # TODO: Use a deploy key to do this
    run(['git', 'push', auth_url, 'master'], check=True)
