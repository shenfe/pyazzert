# coding: utf8

from __future__ import print_function

from azzert import azzert, ensure, mock, C, D, E


schema = {
    'id': (int, r'^\d+$', E(456)),
    'name': (str, E('jerry')),
    'age': (D(18), E(28)),
    'contact': {
        'type': {'mobile', 'email'},
        'value': ((True, str, lambda v: 0 < len(v) < 100), E('10020003000')),
    },
    'hobbies': ([(True, str, C(lambda s: s.lower()))], None, E(['Running', 'chess'])),
}

data = {
    'id': '123',
    'name': 'tom',
    'contact': {
        'type': 'mobile',
        'value': '10010001000',
    },
    'hobbies': ['Swimming', 'movie'],
}

result = azzert(data, schema)

assert result is True

result = ensure(data, schema)

assert result == {
    'id': '123',
    'name': 'tom',
    'age': 18,
    'contact': {
        'type': 'mobile',
        'value': '10010001000'
    },
    'hobbies': ['swimming', 'movie']
}

result = mock(schema)

assert result == {
    'id': 456,
    'name': 'jerry',
    'age': 18,
    'contact': {
        'type': 'mobile',
        'value': '10020003000'
    },
    'hobbies': ['running', 'chess']
}
