import os

from ..changelog import get_release_notes_filename, format_change, update_release_notes

def test_get_release_notes_filename():
    assert get_release_notes_filename('1.1') == 'Release-Notes-for-1.1.md'
    assert get_release_notes_filename('1.1rc1') == 'Release-Notes-for-1.1.md'
    assert get_release_notes_filename('1.1.rc1') == 'Release-Notes-for-1.1.md'
    assert get_release_notes_filename('1.1dev') == 'Release-Notes-for-1.1.md'
    assert get_release_notes_filename('1.1.dev') == 'Release-Notes-for-1.1.md'

    assert get_release_notes_filename('1.1.1') == 'Release-Notes-for-1.1.1.md'
    assert get_release_notes_filename('1.1.1rc1') == 'Release-Notes-for-1.1.1.md'
    assert get_release_notes_filename('1.1.1rc1') == 'Release-Notes-for-1.1.1.md'
    assert get_release_notes_filename('1.1.1dev') == 'Release-Notes-for-1.1.1.md'
    assert get_release_notes_filename('1.1.1.dev') == 'Release-Notes-for-1.1.1.md'

def test_format_change():
    change = '* modified some stuff'
    pr_number = '123'
    authors = ['asmeurer']
    assert format_change(change, pr_number, authors) == \
        '  * modified some stuff ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer))\n'

    authors = ['asmeurer', 'certik']
    assert format_change(change, pr_number, authors) == \
        '  * modified some stuff ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))\n'

    authors = ['asmeurer', 'certik', 'sympy']
    assert format_change(change, pr_number,  authors) == \
        '  * modified some stuff ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer), [@certik](https://github.com/certik), and [@sympy](https://github.com/sympy))\n'

def test_update_release_notes():
    with open(os.path.join(os.path.dirname(__file__),
        get_release_notes_filename('1.2'))) as f:

        notes12 = f.read()

    changelogs = {'solvers': ['* solvers change 1', '* solvers change 2'], 'core': ['- core change 1']}
    authors = ['asmeurer', 'certik']
    pr_number = '123'

    new_notes12 = update_release_notes(notes12, changelogs, pr_number, authors)

    assert new_notes12.splitlines()[114:119] == ['', '* core', '  - core change 1 ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))', '', '  * Derivatives by a variable a symbolic number of times, like `diff(f(x), (x,']

    assert new_notes12.splitlines()[614:620] == ['* solvers', '  * solvers change 1 ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))', '', '  * solvers change 2 ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))', '', '  * Enable initial condition solving in `dsolve`']
