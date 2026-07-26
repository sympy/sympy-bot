#!/usr/bin/env python
import re

from .changelog import BEGIN_RELEASE_NOTES

# The AI Generation Disclosure section of the SymPy pull request template
# (https://github.com/sympy/sympy/blob/master/.github/PULL_REQUEST_TEMPLATE.md).
#
# This is the only part of the template that the bot checks for. The other
# sections are conventions, but this one corresponds to a policy requirement
# (see AI_POLICY_URL), so it is worth complaining about. Checking the other
# headings produces false positives, e.g. when a contributor deletes an
# "#### Other comments" section they had nothing to put in.
AI_DISCLOSURE_HEADING = '#### AI Generation Disclosure'

TEMPLATE_URL = 'https://github.com/sympy/sympy/blob/master/.github/PULL_REQUEST_TEMPLATE.md'
AI_POLICY_URL = 'https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html'

# The text under AI_DISCLOSURE_HEADING, up to the next #### heading or the end
# of the description. Markdown allows a heading to be indented by up to three
# spaces, and the template's headings may pick up trailing whitespace.
#
# BEGIN_RELEASE_NOTES also ends the section. Otherwise a blank disclosure whose
# "#### Release Notes" heading has been deleted would swallow the release notes
# below it and look like it had been filled in.
AI_SECTION_RE = re.compile(
    rf'^[ \t]*{re.escape(AI_DISCLOSURE_HEADING)}[ \t]*$'
    rf'(.*?)'
    rf'(?=^[ \t]*(?:#### |{re.escape(BEGIN_RELEASE_NOTES)})|\Z)',
    re.DOTALL | re.MULTILINE)

HTML_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

def validate_pr_template(body):
    """
    Validate a pull request description against the pull request template.

    Returns a tuple (status, messages), where status is True if the pull
    request follows the template, and messages is a list of strings describing
    the problems found (empty if status is True). This mirrors the return value
    of changelog.get_changelog, so that the messages can be included in the
    same comment.
    """
    messages = []
    section = AI_SECTION_RE.search(body or '')

    if not section:
        messages.append(
            f'* The `{AI_DISCLOSURE_HEADING}` section is missing from the pull '
            f'request description. Please restore it from the [pull request '
            f'template]({TEMPLATE_URL}) and disclose any AI-generated code or '
            f'text, or write "NO AI USE". See the [policy on AI generated code '
            f'and communication]({AI_POLICY_URL}).')
    elif not HTML_COMMENT_RE.sub('', section.group(1)).strip():
        # The section is present but contains nothing except the explanatory
        # comment from the template.
        messages.append(
            f'* The `{AI_DISCLOSURE_HEADING}` section must not be left blank. '
            f'Please disclose any AI-generated code or text, or write "NO AI '
            f'USE". See the [policy on AI generated code and communication]'
            f'({AI_POLICY_URL}).')

    return (not messages, messages)
