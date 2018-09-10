from azzert import azzert

data = {
    'id': 123,
    'name': 'tom',
    'contact': {
        'type': 'mobile',
        'value': '10010001000',
    },
    'hobbies': ['swimming', 'movie'],
}

schema = {
    'id': (int, str),
    'name': str,
    'contact': {
        'type': {'mobile', 'email'},
        'value': (True, str, lambda v: 0 < len(v) < 100),
    },
    'hobbies': ([str], None),
}

try:
    result = azzert(data, schema)
except Exception as e:
    raise e
