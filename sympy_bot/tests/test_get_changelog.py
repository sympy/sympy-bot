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

def test_bad_headers():
    desc = """
<!-- BEGIN RELEASE NOTES -->
  * new solver

"""
    status, message, changelogs = get_changelog(desc)
    assert not status
    assert "subheader" in message
    assert not changelogs

    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers

"""
    status, message, changelogs = get_changelog(desc)
    assert not status
    assert "invalid" in message.lower()
    assert not changelogs

    desc = """
<!-- BEGIN RELEASE NOTES -->
* new trig solvers

"""
    status, message, changelogs = get_changelog(desc)
    assert not status
    assert "header" in message.lower()
    assert not changelogs

    desc = """
<!-- BEGIN RELEASE NOTES -->
* invalid_header

"""
    status, message, changelogs = get_changelog(desc)
    assert not status
    assert "header" in message.lower()
    assert "invalid_header" in message
    assert not changelogs

def test_end_release_marker():

    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * new trig solvers
<!-- END RELEASE NOTES -->
* stuff after
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "good" in message
    assert changelogs == {'solvers': ['* new trig solvers']}

    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * new trig solvers
<!-- END RELEASE NOTES -->
* core
  * not a real change
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "good" in message
    assert changelogs == {'solvers': ['* new trig solvers']}

def test_multiline():
    desc = """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * new trig solvers

    ```
    code
    ```
* core
  * core change

<!-- END RELEASE NOTES -->
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "good" in message
    assert changelogs == {
        'solvers': ['* new trig solvers\n\n  ```\n  code\n  ```'],
        'core': ['* core change'],
    }
