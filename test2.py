# coding: utf8

from __future__ import print_function

from azzert import azzert, ensure, mock, C, D, E


data = {
    'id': '123',
    'name': 'tom',
    'contact': {
        'type': 'mobile',
        'value': '10010001000',
    },
    'hobbies': ['Swimming', 'movie'],
}

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

result = azzert(data, schema)

print(result)

result = ensure(data, schema)

print(result)

result = mock(schema)

print(result)
