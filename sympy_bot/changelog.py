#!/usr/bin/env python
import os
import re

from collections import defaultdict

PREFIX = '* '
SUFFIX = ' ([#{pr_number}](../pull/{pr_number}) by {authors})\n'
AUTHOR = "[@{author}](https://github.com/{author})"
VERSION_RE = re.compile(r'\d+(?:(?:\.\d+)*(?:\.[1-9]\d*)|\.0)')

def get_valid_headers():
    valid_headers = []
    with open(os.path.join(os.path.dirname(__file__), 'submodules.txt')) as f:
        for line in f.readlines():
            if line and not line.startswith('#'):
                valid_headers.append(line.strip())

    return valid_headers

def get_changelog(pr_desc):
    """
    Parse changelogs from a string

    pr_desc should be a string or list or lines of the pull request
    description.

    Returns a tuple (status, message, changelogs), where:

    - status is a boolean indicating if the changelog entry is valid or not
    - message is a string with a message to be reported changelogs is a dict
    - mapping headers to changelog messages

    """
    status = True
    message_list = []
    changelogs = defaultdict(list)
    header = None
    if isinstance(pr_desc, (str, bytes)):
        pr_desc = pr_desc.splitlines()
    lines = iter(pr_desc)
    valid_headers = get_valid_headers()

    # First find the release notes header
    for line in lines:
        if line.strip() == "<!-- BEGIN RELEASE NOTES -->":
            break
    else:
        return (False, "The `<!-- BEGIN RELEASE NOTES -->` block was not found",
                changelogs)

    for line in lines:
        if line.strip() == "<!-- END RELEASE NOTES -->":
            break
        if line.strip() == 'NO ENTRY':
            message_list += ["No release notes entry will be added for this pull request."]
            changelogs.clear()
            status = True
            break
        elif line.startswith('* ') or line.startswith('- '):
            header = line.lstrip('*- ')
            header = header.strip()
            if header not in valid_headers:
                status = False
                if ' ' in header:
                    # Most likely just forgot the header
                    message_list += [
                        "Release notes must include a header.",
                        "Please use the submodule name as the header, like",
                        "```",
                        "* core",
                        "  * made Add faster",
                        "",
                        "* printing",
                        "  * improve LaTeX printing of fractions",
                        "```",
                    ]
                else:
                    message_list += [
                        "%s is not a valid release notes header." % header,
                        "Release notes headers should be SymPy submodule",
                        "names, like",
                        "```",
                        "* core",
                        "  * made Add faster",
                        "",
                        "* printing",
                        "  * improve LaTeX printing of fractions",
                        "```",
                        "or `other`.",
                        "",
                        "If you have added a new submodule, please add it to",
                        "the list of valid release notes headers at",
                        "https://github.com/sympy/sympy-bot/blob/master/sympy_bot/submodules.txt.",
                    ]

            else:
                changelogs[header] # initialize the defaultdict

        elif not line.strip():
            continue
        else:
            if not header:
                message_list += [
                    'No subheader found. Please add a header for',
                    'the module, for example,',
                    '',
                    '```',
                    '* solvers',
                    '  * improve solving of trig equations',
                    '```',
                ]
                status = False
                break
            changelogs[header].append(line.strip())
    else:
        if not changelogs:
            message_list += ['No release notes were detected. If there is no',
                             'release notes entry, please write `NO ENTRY` in the',
                             'PR description under `<!-- BEGIN RELEASE NOTES -->`.']
            status = False

    for header in changelogs:
        if not changelogs[header]:
            message_list += [
                'Invalid release notes entry for `%s`.' % header,
                'Make sure it has a release notes entry under it.',
            ]
            status = False
    if not message_list:
        message_list = ["Your release notes are in good order."]
    if not status:
        changelogs.clear()
    return status, '\n'.join(message_list), changelogs

def get_release_notes_filename(version):
    """
    Return filename of release notes for current development version
    """
    v = VERSION_RE.match(version).group()
    return 'Release-Notes-for-' + v + '.md'

def format_change(change, pr_number, authors):
    if len(authors) == 1:
        authors_info = AUTHOR.format(author=authors[0])
    elif len(authors) == 2:
        authors_info = AUTHOR.format(author=authors[0]) + " and " + AUTHOR.format(author=authors[1])
    else:
        authors_info = ", ".join([AUTHOR.format(author=author) for author
            in authors[:-1]]) + ', and ' + AUTHOR.format(author=authors[-1])

    return ' '*len(PREFIX) + change + SUFFIX.format(pr_number=pr_number, authors=authors_info)

def update_release_notes(*, rel_notes_txt, changelogs, pr_number, authors):
    """
    Update release notes

    changelogs is assumed to only contain valid headers
    """
    new_txt = []

    valid_headers = get_valid_headers()
    changelogs = changelogs.copy()
    authors = sorted(authors)

    for line in rel_notes_txt.splitlines():
        new_txt.append(line)
        line_header = line.lstrip(PREFIX)
        if line.startswith(PREFIX):
            if line_header not in valid_headers:
                continue
            for header in changelogs.copy():
                if (valid_headers.index(header) <
                    valid_headers.index(line_header)):
                    # We reached a header after one we haven't processed,
                    # meaning it isn't in the file, so add it.
                    del new_txt[-1]
                    new_txt.append(PREFIX + header)
                    for change in changelogs[header]:
                        new_txt.append(format_change(change, pr_number, authors))
                    del changelogs[header]
                    new_txt.append(line)
                    continue

            if line_header in changelogs:
                for change in changelogs[line_header]:
                    new_txt.append(format_change(change, pr_number, authors))
                del changelogs[line_header]
                continue

        if line == "## Authors":
            del new_txt[-1]
            # Keep the order from submodules.txt
            for header in valid_headers:
                if header in changelogs:
                    new_txt.append(PREFIX + header)
                    for change in changelogs[header]:
                        new_txt.append(format_change(change, pr_number, authors))
            new_txt.append(line)
            changelogs.clear()

    new_txt.append('')
    if changelogs:
        raise RuntimeError("Not all changelog entries were added. Make sure there is a header called `## Authors` at the end of the release notes.")

    return '\n'.join(new_txt)
