# coding: utf8

from azzert import azzert

data = {
    'id': '123',
    'name': 'tom',
    'contact': {
        'type': 'mobile',
        'value': '10010001000',
    },
    'hobbies': ['swimming', 'movie'],
}

schema = {
    'id': (int, r'^\d+$'),
    'name': str,
    'contact': {
        'type': {'mobile', 'email'},
        'value': (True, str, lambda v: 0 < len(v) < 100),
    },
    'hobbies': ([str], None),
}

result = azzert(data, schema)

print result
