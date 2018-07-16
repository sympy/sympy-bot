from ..changelog import get_release_notes_filename

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
