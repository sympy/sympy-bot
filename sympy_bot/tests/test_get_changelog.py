from ..changelog import get_changelog

def test_no_marker():
    desc = """
* solvers
  * add a new solver
"""

    status, message, changelogs = get_changelog(desc)

    assert not status
    assert '<!-- BEGIN RELEASE NOTES -->' in message
    assert not changelogs

    desc = """
NO ENTRY
"""

    status, message, changelogs = get_changelog(desc)

    assert not status
    assert '<!-- BEGIN RELEASE NOTES -->' in message
    assert not changelogs

def test_no_entry():
    desc = """
<!-- BEGIN RELEASE NOTES -->
NO ENTRY
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "No release notes entry" in message
    assert not changelogs

    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers
 * new solver

NO ENTRY
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "No release notes entry" in message
    assert not changelogs

    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers

NO ENTRY
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "No release notes entry" in message
    assert not changelogs

def test_headers():
    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * new solver

* core
  * faster core
  * better stuff

"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "good" in message
    assert changelogs == {
        'solvers': ['* new solver'],
        'core': ['* faster core', '* better stuff']
    }
