from ..changelog import format_change, format_authors

def test_format_authors():
    assert format_authors(['asmeurer']) == '[@asmeurer](https://github.com/asmeurer)'
    assert format_authors(['certik', 'asmeurer']) == '[@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik)'
    assert format_authors(['Upabjojr', 'certik', 'asmeurer']) == '[@asmeurer](https://github.com/asmeurer), [@certik](https://github.com/certik), and [@Upabjojr](https://github.com/Upabjojr)'

def test_format_change():
    assert format_change("* improved solvers", 123, ['certik', 'asmeurer']) == '  * improved solvers ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))\n'
    assert format_change("* example\n```\n>>> print(1)\n1\n```", 123, ['asmeurer']) == '  * example\n  ```\n  >>> print(1)\n  1\n  ```\n\n    ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))\n'
    assert format_change('* improved solvers\n\n  * dsolve\n  * solve', 123, ['asmeurer']) == '  * improved solvers\n\n    * dsolve\n    * solve\n\n    ([#123](https://github.com/sympy/sympy/pull/123) by [@asmeurer](https://github.com/asmeurer))\n'


def test_threebackticks_not_multiline():
    assert format_change('* added ```rot13``` and ```atbash``` ciphers',
    16516, ['znxftw']) == '  * added ```rot13``` and ```atbash``` ciphers ([#16516](https://github.com/sympy/sympy/pull/16516) by [@znxftw](https://github.com/znxftw))\n'
