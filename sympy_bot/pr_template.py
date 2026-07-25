#!/usr/bin/env python
import re

# The section headings from the SymPy pull request template
# (https://github.com/sympy/sympy/blob/master/.github/PULL_REQUEST_TEMPLATE.md).
# The template requires that all of these are kept in the pull request
# description.
REQUIRED_SECTIONS = [
    '#### References to other Issues or PRs',
    '#### Brief description of what is fixed or changed',
    '#### Other comments',
    '#### AI Generation Disclosure',
    '#### Release Notes',
]

AI_DISCLOSURE_HEADING = '#### AI Generation Disclosure'

HTML_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

ISSUE_NUMBER_IN_TITLE_RE = re.compile(r'#\d+')

TEMPLATE_URL = 'https://github.com/sympy/sympy/blob/master/.github/PULL_REQUEST_TEMPLATE.md'
AI_POLICY_URL = 'https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html'

def _section_text(body, heading):
    """
    Return the lines of body under the given #### heading, up to the next
    #### heading or the end of the body. Returns an empty string if the
    heading is not present.
    """
    section_lines = []
    in_section = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith('#### '):
            if in_section:
                break
            in_section = stripped == heading
            continue
        if in_section:
            section_lines.append(line)
    return '\n'.join(section_lines)

def validate_pr_template(body, title):
    """
    Validate a pull request description and title against the pull request
    template.

    Returns a tuple (status, messages), where status is True if the pull
    request follows the template, and messages is a list of strings
    describing the problems found (empty if status is True).
    """
    messages = []
    body = body or ''

    missing = [s for s in REQUIRED_SECTIONS if s not in body]
    if missing:
        messages.append(
            '* Do not delete or replace the pull request template; all '
            'section headings must be kept. The following sections are '
            'missing: ' + ', '.join(f'`{s}`' for s in missing) + '.')

    if AI_DISCLOSURE_HEADING in body:
        section = HTML_COMMENT_RE.sub('', _section_text(body, AI_DISCLOSURE_HEADING))
        if not section.strip():
            messages.append(
                f'* The `{AI_DISCLOSURE_HEADING}` section must not be left '
                'blank. Disclose any AI-generated code or text, or write '
                f'"NO AI USE". See the [policy on AI generated code and '
                f'communication]({AI_POLICY_URL}).')

    if title and ISSUE_NUMBER_IN_TITLE_RE.search(title):
        messages.append(
            '* The pull request title should not include the issue number.')

    return (not messages, messages)
