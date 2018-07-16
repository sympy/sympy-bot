from ..changelog import get_changelog

def test_get_changelog_no_marker():
    desc = """
* solvers
  * add a new solver
"""

    status, message, changelogs = get_changelog(desc)

    assert not status
    assert '<!-- BEGIN RELEASE NOTES -->' in message
    assert not changelogs
