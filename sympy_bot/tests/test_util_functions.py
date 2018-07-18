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
        '  * modified some stuff ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer))\n'

    authors = ['asmeurer', 'certik']
    assert format_change(change, pr_number, authors) == \
        '  * modified some stuff ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))\n'

    authors = ['asmeurer', 'certik', 'sympy']
    assert format_change(change, pr_number,  authors) == \
        '  * modified some stuff ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer), [@certik](https://github.com/certik), and [@sympy](https://github.com/sympy))\n'

def test_format_change_multiline():
    change = '* new trig solvers\n\n  ```\n  code\n  ```'
    authors = ['asmeurer']
    pr_number = '123'

    assert format_change(change, pr_number, authors) == """\
  * new trig solvers

    ```
    code
    ```

    ([#123](../pull/123) by [@asmeurer](https://github.com/asmeurer))
"""
