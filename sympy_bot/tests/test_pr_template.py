from pytest import mark
parametrize = mark.parametrize

from ..pr_template import check_ai_disclosure

# The instructions in the template, as HTML comments
COMMENTED_TEMPLATE = """\
<!-- DO NOT DELETE OR REPLACE THIS TEMPLATE or the PR will be closed. -->

#### References to other Issues or PRs

<!-- If there is an issue related to this PR, include a link to the issue here. -->


#### Brief description of what is fixed or changed

{brief}

#### Other comments


#### AI Generation Disclosure

<!-- If this pull request includes AI-generated code or text, please disclose
the tool used and specify which lines were generated. Otherwise, write "NO AI USE". -->

{disclosure}

#### Release Notes

<!-- Write the release notes for this release below. -->

<!-- BEGIN RELEASE NOTES -->
NO ENTRY
<!-- END RELEASE NOTES -->
"""

# The same template with the instructions removed, leaving only what the
# release notes check needs
UNCOMMENTED_TEMPLATE = """\
#### References to other Issues or PRs


#### Brief description of what is fixed or changed

{brief}

#### Other comments


#### AI Generation Disclosure

{disclosure}

#### Release Notes

<!-- BEGIN RELEASE NOTES -->
NO ENTRY
<!-- END RELEASE NOTES -->
"""

templates = parametrize('template', [COMMENTED_TEMPLATE, UNCOMMENTED_TEMPLATE])
line_endings = parametrize('line_ending', ['\n', '\r\n'])


def _description(template, line_ending, disclosure, brief="Fixed a bug."):
    desc = template.format(brief=brief, disclosure=disclosure)
    return desc.replace('\n', line_ending)


@templates
@line_endings
@parametrize('disclosure', [
    "NO AI USE",
    "Claude wrote the tests.",
    "### Tools\n\nClaude wrote the tests.",
    "## Tools",
])
def test_disclosure_present(template, line_ending, disclosure):
    desc = _description(template, line_ending, disclosure)
    assert check_ai_disclosure(desc) == (True, '')


@templates
@line_endings
@parametrize('disclosure', ["", "   \n\n  ", "<!-- NO AI USE -->"])
def test_disclosure_empty(template, line_ending, disclosure):
    status, message = check_ai_disclosure(_description(template, line_ending, disclosure))
    assert status is False
    assert "`#### AI Generation Disclosure` section is empty" in message
    assert "NO AI USE" in message


@line_endings
def test_disclosure_empty_at_end_of_description(line_ending):
    desc = f"#### Brief description of what is fixed or changed{line_ending}Fixed a bug.{line_ending}#### AI Generation Disclosure{line_ending}"
    status, message = check_ai_disclosure(desc)
    assert status is False
    assert "section is empty" in message


@parametrize('desc', [
    None,
    "",
    "Please merge my great PR.",
    "AI Generation Disclosure: NO AI USE",
    "### AI Generation Disclosure\n\nNO AI USE",
    "##### AI Generation Disclosure\n\nNO AI USE",
    "#### ai generation disclosure\n\nNO AI USE",
    "#### AI Generation Disclosure: NO AI USE",
    "<!-- #### AI Generation Disclosure\n\nNO AI USE -->",
])
def test_disclosure_missing(desc):
    status, message = check_ai_disclosure(desc)
    assert status is False
    assert "`#### AI Generation Disclosure` section is missing" in message
    assert "NO AI USE" in message


def test_only_the_ai_disclosure_is_checked():
    desc = "#### AI Generation Disclosure\n\nNO AI USE\n"
    assert check_ai_disclosure(desc) == (True, '')
