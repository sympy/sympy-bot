"""
Check that a pull request description follows the SymPy pull request template.

Only the AI generation disclosure is checked. It is found by its heading alone,
so this does not depend on the HTML comments in the template.
"""
import re

AI_DISCLOSURE_HEADING = "#### AI Generation Disclosure"
AI_POLICY_URL = "https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html"

_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)
_AI_DISCLOSURE_RE = re.compile(rf'^{re.escape(AI_DISCLOSURE_HEADING)}[ \t]*$', re.MULTILINE)
# Only a heading of the same level ends the section, so that a subheading
# written by the author doesn't make the section look empty.
_NEXT_SECTION_RE = re.compile(r'^####[ \t]', re.MULTILINE)

_AI_DISCLOSURE_HELP = f"""\
This section should say which AI tool was used and which lines it generated, \
or `NO AI USE` if no AI was used. See the [policy on AI generated \
code]({AI_POLICY_URL})."""


def check_ai_disclosure(pr_desc):
    """
    Check that ``pr_desc`` has a non-empty AI generation disclosure section.

    ``pr_desc`` is the pull request description as a string (``None`` is
    treated as an empty description).

    Returns a tuple ``(status, message)`` where ``status`` is ``True`` if the
    disclosure is present and ``message`` is a markdown string explaining what
    is wrong. ``message`` is empty when ``status`` is ``True``.
    """
    # Descriptions written in the GitHub web form use CRLF line endings.
    pr_desc = _COMMENT_RE.sub('', (pr_desc or '').replace('\r\n', '\n'))

    heading = _AI_DISCLOSURE_RE.search(pr_desc)
    if not heading:
        return False, f"* The `{AI_DISCLOSURE_HEADING}` section is missing. {_AI_DISCLOSURE_HELP}"

    section = pr_desc[heading.end():]
    next_section = _NEXT_SECTION_RE.search(section)
    if next_section:
        section = section[:next_section.start()]
    if not section.strip():
        return False, f"* The `{AI_DISCLOSURE_HEADING}` section is empty. {_AI_DISCLOSURE_HELP}"

    return True, ''
