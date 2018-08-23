from ..changelog import get_release_notes_filename, format_change

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
        '  * modified some stuff ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))\n'

    authors = ['asmeurer', 'certik']
    assert format_change(change, pr_number, authors) == \
        '  * modified some stuff ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))\n'

    authors = ['asmeurer', 'certik', 'sympy']
    assert format_change(change, pr_number,  authors) == \
        '  * modified some stuff ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer), [@certik](https://github.com/certik), and [@sympy](https://github.com/sympy))\n'

def test_format_change_multiline():
    change = '* new trig solvers\n\n  ```\n  code\n  ```'
    authors = ['asmeurer']
    pr_number = '123'

    assert format_change(change, pr_number, authors) == """\
  * new trig solvers

    ```
    code
    ```

    ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))
"""

    change = '* new trig solvers\n  ```\n  code\n  ```'
    authors = ['asmeurer']
    pr_number = '123'

    assert format_change(change, pr_number, authors) == """\
  * new trig solvers
    ```
    code
    ```

    ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))
"""

    # Make sure changes that aren't really multiline don't get the PR and
    # author link on a separate line. From
    # https://github.com/sympy/sympy/pull/15133
    change = '* Used checksysodesol in test_ode.py to reduce amount of code. Also slightly modified the\n       representation of the test cases in the function, but with no changes in their values.'
    authors = ['sudz123']
    pr_number = '15133'

    assert format_change(change, pr_number, authors) == """\
  * Used checksysodesol in test_ode.py to reduce amount of code. Also slightly modified the\n         representation of the test cases in the function, but with no changes in their values. ([#15133](https://github.com/sympy/sympy/pull/15133) by [@sudz123](https://github.com/sudz123))
"""
