from ..pr_template import (
    validate_pr_template,
    PR_TEMPLATE,
    REQUIRED_HEADINGS,
    CONTENT_REQUIRED_HEADINGS,
    REQUIRED_TEMPLATE_COMMENTS,
)


def make_compliant(release_notes="* solvers\n  * new trig solvers"):
    """
    Build a template-compliant description from the canonical template by
    filling in the two content-required sections and the release notes.
    """
    desc = PR_TEMPLATE
    desc = desc.replace(
        "#### Brief description of what is fixed or changed\n",
        "#### Brief description of what is fixed or changed\n\nFixed a bug in the solvers module.\n",
        1,
    )
    desc = desc.replace(
        "#### AI Generation Disclosure\n",
        "#### AI Generation Disclosure\n\nNO AI USE\n",
        1,
    )
    desc = desc.replace(
        "<!-- BEGIN RELEASE NOTES -->\n\n<!-- END RELEASE NOTES -->",
        "<!-- BEGIN RELEASE NOTES -->\n" + release_notes + "\n<!-- END RELEASE NOTES -->",
        1,
    )
    return desc


def test_required_template_comments_extracted():
    # The top comment, the References comment, the AI comment, the Release
    # Notes comment, and the BEGIN/END markers.
    assert len(REQUIRED_TEMPLATE_COMMENTS) == 6
    assert "<!-- BEGIN RELEASE NOTES -->" in REQUIRED_TEMPLATE_COMMENTS
    assert "<!-- END RELEASE NOTES -->" in REQUIRED_TEMPLATE_COMMENTS
    for comment in REQUIRED_TEMPLATE_COMMENTS:
        assert comment in PR_TEMPLATE


def test_compliant():
    status, message = validate_pr_template(make_compliant())
    assert status is True
    assert message == ""


def test_compliant_no_entry():
    status, message = validate_pr_template(make_compliant("NO ENTRY"))
    assert status is True
    assert message == ""


def test_compliant_empty_release_notes():
    # Release Notes content is validated elsewhere, so an empty release notes
    # block is still template-compliant as far as this validator is concerned.
    status, message = validate_pr_template(make_compliant(""))
    assert status is True
    assert message == ""


def test_none():
    status, message = validate_pr_template(None)
    assert status is False
    assert message


def test_empty():
    status, message = validate_pr_template("")
    assert status is False
    # Everything is wrong: headings, comments, and content.
    assert "section headings" in message
    assert "template's HTML comments" in message


def test_random_text():
    status, message = validate_pr_template("Here is my great PR, please merge it.")
    assert status is False
    assert message


def test_missing_one_heading():
    desc = make_compliant().replace("#### Other comments\n", "", 1)
    status, message = validate_pr_template(desc)
    assert status is False
    assert "Other comments" in message
    # The other headings are fine, so they should not be listed as missing.
    assert "References to other Issues or PRs" not in message


def test_missing_template_comment():
    # Delete the References comment. Its content is not required, so only the
    # comment check should fire.
    references_comment = [c for c in REQUIRED_TEMPLATE_COMMENTS
                          if "waste reviewer's time" in c][0]
    desc = make_compliant().replace(references_comment, "", 1)
    status, message = validate_pr_template(desc)
    assert status is False
    assert "template's HTML comments" in message


def test_modified_template_comment():
    # Rewording a comment (as AI often does) must fail: exact match is required.
    desc = make_compliant().replace(
        "DO NOT DELETE OR REPLACE THIS TEMPLATE",
        "Do not delete or replace this template",
        1,
    )
    status, message = validate_pr_template(desc)
    assert status is False
    assert "template's HTML comments" in message


def test_deleted_ai_comment():
    ai_comment = [c for c in REQUIRED_TEMPLATE_COMMENTS
                  if "AI-generated code or text" in c][0]
    desc = make_compliant().replace(ai_comment, "", 1)
    status, message = validate_pr_template(desc)
    assert status is False
    assert "template's HTML comments" in message


def test_empty_brief_description():
    # Compliant except the Brief description is left blank.
    desc = PR_TEMPLATE.replace(
        "#### AI Generation Disclosure\n",
        "#### AI Generation Disclosure\n\nNO AI USE\n",
        1,
    )
    status, message = validate_pr_template(desc)
    assert status is False
    assert "empty" in message
    assert "Brief description of what is fixed or changed" in message


def test_empty_ai_disclosure():
    # Compliant except the AI Generation Disclosure is left blank.
    desc = PR_TEMPLATE.replace(
        "#### Brief description of what is fixed or changed\n",
        "#### Brief description of what is fixed or changed\n\nFixed a bug.\n",
        1,
    )
    status, message = validate_pr_template(desc)
    assert status is False
    assert "empty" in message
    assert "AI Generation Disclosure" in message


def test_ai_disclosure_only_comment_is_empty():
    # The AI section contains only the template comment (no author text). After
    # stripping the comment it is empty, so it must fail the content check.
    desc = make_compliant().replace("\n\nNO AI USE\n", "\n", 1)
    status, message = validate_pr_template(desc)
    assert status is False
    assert "AI Generation Disclosure" in message


def test_heading_must_be_verbatim():
    # Changing a heading's level or wording counts as missing: the template
    # headings must be kept exactly as they are.
    desc = make_compliant().replace(
        "#### References to other Issues or PRs",
        "###### references to   other issues or prs",
        1,
    )
    status, message = validate_pr_template(desc)
    assert status is False
    assert "References to other Issues or PRs" in message


def test_content_required_is_subset_of_required():
    assert set(CONTENT_REQUIRED_HEADINGS) <= set(REQUIRED_HEADINGS)


def test_multiple_problems_reported_together():
    # An empty description should report both missing headings and missing
    # comments in one message.
    status, message = validate_pr_template("")
    assert status is False
    assert "section headings" in message
    assert "template's HTML comments" in message
