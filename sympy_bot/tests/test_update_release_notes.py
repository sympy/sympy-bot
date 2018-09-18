import os

from ..changelog import get_release_notes_filename, update_release_notes

def test_existing_header():
    with open(os.path.join(os.path.dirname(__file__),
        get_release_notes_filename('1.2'))) as f:

        notes12 = f.read()

    changelogs = {'solvers': ['* solvers change 1', '* solvers change 2'], 'core': ['- core change 1']}
    authors = ['asmeurer', 'certik']
    pr_number = '123'

    new_notes12 = update_release_notes(rel_notes_txt=notes12, changelogs=changelogs, pr_number=pr_number, authors=authors)

    assert new_notes12.splitlines()[114:119] == ['', '* core', '  - core change 1 ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))', '', '  * Derivatives by a variable a symbolic number of times, like `diff(f(x), (x,']

    assert new_notes12.splitlines()[614:620] == ['* solvers', '  * solvers change 1 ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))', '', '  * solvers change 2 ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))', '', '  * Enable initial condition solving in `dsolve`']

def test_new_header():
    notes = """\
## Changes

## Authors
"""

    # Also makes sure they are inserted in the right order. 'other' should
    # stay last in submodules.txt
    changelogs = {'solvers': ['- solvers change'], 'other': ['- other changes']}
    authors = ['asmeurer']
    pr_number = '123'

    new_notes = update_release_notes(rel_notes_txt=notes, changelogs=changelogs, pr_number=pr_number, authors=authors)

    assert new_notes == """\
## Changes

* solvers
  - solvers change ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))

* other
  - other changes ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))

## Authors
"""


def test_insert_new_header():
    notes = """\
## Changes

* core
  * core change

* solvers
  * solvers change

## Authors
"""

    # 'other' should stay last in submodules.txt
    changelogs = {'sets': ['- sets change'], 'calculus': ['- calculus change'], 'other': ['- other changes']}
    authors = ['asmeurer']
    pr_number = '123'

    new_notes = update_release_notes(rel_notes_txt=notes, changelogs=changelogs, pr_number=pr_number, authors=authors)

    assert new_notes == """\
## Changes

* calculus
  - calculus change ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))

* core
  * core change

* sets
  - sets change ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))

* solvers
  * solvers change

* other
  - other changes ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))

## Authors
""", new_notes

def test_no_changes_header():
    notes = """\

## Authors
"""

    # Also makes sure they are inserted in the right order. 'other' should
    # stay last in submodules.txt
    changelogs = {'solvers': ['- solvers change'], 'other': ['- other changes']}
    authors = ['asmeurer']
    pr_number = '123'

    try:
        update_release_notes(rel_notes_txt=notes, changelogs=changelogs, pr_number=pr_number, authors=authors)
    except RuntimeError as e:
        assert "## Changes" in e.args[0]
    else:
        raise AssertionError("Did not raise")

    notes = ""

    try:
        update_release_notes(rel_notes_txt=notes, changelogs=changelogs, pr_number=pr_number, authors=authors)
    except RuntimeError as e:
        assert "## Changes" in e.args[0]
    else:
        raise AssertionError("Did not raise")

def test_no_authors_header():
    notes = "## Changes"

    changelogs = {'solvers': ['* solvers change 1', '* solvers change 2'], 'core': ['- core change 1']}
    authors = ['asmeurer', 'certik']
    pr_number = '123'

    try:
        update_release_notes(rel_notes_txt=notes, changelogs=changelogs, pr_number=pr_number, authors=authors)
    except RuntimeError as e:
        assert "## Authors" in e.args[0]
    else:
        raise AssertionError("Did not raise")

def test_before_changes_header():
    # This is based on what happened to the 1.4 release notes (#35), except
    # with "## Major Changes" replaced with "## Changes"
    notes = """

## Backwards compatibility breaks and deprecations

**Please manually add any backwards compatibility breaks or
[deprecations](https://github.com/sympy/sympy/wiki/Deprecating-policy) here,
in addition to the automatic listing below.**

* printing
  * Old behavior of `theanocode.theano_function` when passed a single-element list as the `outputs` parameter has been deprecated. Use `squeeze=False` to enable the new behavior (the created function will return a single-element list also). To get a function that returns a single value not wrapped in a list, pass a single expression not wrapped in a list to `outputs` (e.g. `theano_function([x, y], x + y)` instead of `theano_function([x, y], [x + y])`). See [#14986](https://github.com/sympy/sympy/issues/14986).

## Changes

* printing
  * Added `squeeze=False` option to `theanocode.theano_function` to give more consistent sequence-in-sequence-out behavior, keep old behavior as default for now but deprecate it. ([#14949](https://github.com/sympy/sympy/pull/14949) by [@jlumpe](https://github.com/jlumpe))

  * Added `scalar=True` option to `theanocode.theano_function` to create a function which returns scalars instead of 0-dimensional arrays. ([#14949](https://github.com/sympy/sympy/pull/14949) by [@jlumpe](https://github.com/jlumpe))

* series
  * implemented expression-based recursive sequence class ([#15184](https://github.com/sympy/sympy/pull/15184) by [@rwbogl](https://github.com/rwbogl))

## Authors
"""

    pr_number = "15207"
    authors = ["sylee957"]
    changelogs = {'matrices': ["- Added `iszerofunc` parameter for `_eval_det_bareiss()`"]}

    new_notes = update_release_notes(rel_notes_txt=notes, changelogs=changelogs, pr_number=pr_number, authors=authors)

    assert new_notes == """

## Backwards compatibility breaks and deprecations

**Please manually add any backwards compatibility breaks or
[deprecations](https://github.com/sympy/sympy/wiki/Deprecating-policy) here,
in addition to the automatic listing below.**

* printing
  * Old behavior of `theanocode.theano_function` when passed a single-element list as the `outputs` parameter has been deprecated. Use `squeeze=False` to enable the new behavior (the created function will return a single-element list also). To get a function that returns a single value not wrapped in a list, pass a single expression not wrapped in a list to `outputs` (e.g. `theano_function([x, y], x + y)` instead of `theano_function([x, y], [x + y])`). See [#14986](https://github.com/sympy/sympy/issues/14986).

## Changes

* matrices
  - Added `iszerofunc` parameter for `_eval_det_bareiss()` ([#15207](https://github.com/sympy/sympy/pull/15207) by [@sylee957](https://github.com/sylee957))

* printing
  * Added `squeeze=False` option to `theanocode.theano_function` to give more consistent sequence-in-sequence-out behavior, keep old behavior as default for now but deprecate it. ([#14949](https://github.com/sympy/sympy/pull/14949) by [@jlumpe](https://github.com/jlumpe))

  * Added `scalar=True` option to `theanocode.theano_function` to create a function which returns scalars instead of 0-dimensional arrays. ([#14949](https://github.com/sympy/sympy/pull/14949) by [@jlumpe](https://github.com/jlumpe))

* series
  * implemented expression-based recursive sequence class ([#15184](https://github.com/sympy/sympy/pull/15184) by [@rwbogl](https://github.com/rwbogl))

## Authors
"""


def test_multiline_indent():
    # See test_multiple_multiline() in test_get_changelogs.py and issue #14.
    # This is from sympy/sympy#14758.
    pr_number = '14758'
    authors = ['NikhilPappu']
    notes = """\
## Changes

## Authors
"""

    changelogs = {
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

    assert update_release_notes(rel_notes_txt=notes, changelogs=changelogs,
    pr_number=pr_number, authors=authors) == """\
## Changes

* parsing
  * Added a submodule autolev which can be used to parse Autolev code to SymPy code. ([#14758](https://github.com/sympy/sympy/pull/14758) by [@NikhilPappu](https://github.com/NikhilPappu))

* physics.mechanics
  * Added a center of mass function in functions.py which returns the position vector of the center of
    mass of a system of bodies. ([#14758](https://github.com/sympy/sympy/pull/14758) by [@NikhilPappu](https://github.com/NikhilPappu))

  * Added a corner case check in kane.py (Passes dummy symbols to q_ind and kd_eqs if not passed in
     to prevent errors which shouldn't occur). ([#14758](https://github.com/sympy/sympy/pull/14758) by [@NikhilPappu](https://github.com/NikhilPappu))

* physics.vector
  * Changed _w_diff_dcm in frame.py to get the correct results. ([#14758](https://github.com/sympy/sympy/pull/14758) by [@NikhilPappu](https://github.com/NikhilPappu))

## Authors
"""
