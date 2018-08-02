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

def test_multiple_multiline():
    # from sympy/sympy#14758, see #14
    desc = """
<!-- BEGIN RELEASE NOTES -->
* parsing
    * Added a submodule autolev which can be used to parse Autolev code to SymPy code.
* physics.mechanics
    * Added a center of mass function in functions.py which returns the position vector of the center of
      mass of a system of bodies.
    * Added a corner case check in kane.py (Passes dummy symbols to q_ind and kd_eqs if not passed in
       to prevent errors which shouldn't occur).
* physics.vector
    * Changed _w_diff_dcm in frame.py to get the correct results.
<!-- END RELEASE NOTES -->
"""
    status, message, changelogs = get_changelog(desc)
    assert status
    assert "good" in message
    assert changelogs == {
        'parsing': [
            '* Added a submodule autolev which can be used to parse Autolev code to SymPy code.',
        ],
        'physics.mechanics': [
            '* Added a center of mass function in functions.py which returns the position vector of the center of\n  mass of a system of bodies.',
            "* Added a corner case check in kane.py (Passes dummy symbols to q_ind and kd_eqs if not passed in\n   to prevent errors which shouldn't occur).",
        ],
        'physics.vector': [
            "* Changed _w_diff_dcm in frame.py to get the correct results.",
        ],
    }

def test_empty_lines():
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


def test_empty():
    desc = r"""
<!-- Your title above should be a short description of what
was changed. Do not include the issue number in the title. -->

#### References to other Issues or PRs
<!-- If this pull request fixes an issue, write "Fixes #NNNN" in that exact
format, e.g. "Fixes #1234". See
https://github.com/blog/1506-closing-issues-via-pull-requests .-->


#### Brief description of what is fixed or changed


#### Other comments


#### Release Notes

<!-- Write the release notes for this release below. See
https://github.com/sympy/sympy/wiki/Writing-Release-Notes for more information
on how to write release notes. If there is no release notes entry for this PR,
write "NO ENTRY". The bot will check your release notes automatically to see
if they are formatted correctly. -->

<!-- BEGIN RELEASE NOTES -->

<!-- END RELEASE NOTES -->
"""
    status, message, changelogs = get_changelog(desc)
    assert not status
    assert 'No release notes were found' in message
    assert not changelogs
