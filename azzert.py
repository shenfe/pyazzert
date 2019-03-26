# coding: utf8

"""
################################ assertion schema ################################

schema = int

schema = lambda v: v in [0, 1]

schema = (int, float, str)                          # OR

schema = (int, float, str, type(None))              # can be `null` (i.e. `None` in python)

schema = (int, float, str, type(None), None)        # can be missing

schema = (True, (int, float), lambda v: v >= 0)     # AND

schema = {0, 1, 2}                                  # should be in the set

schema = {'id': idSchema, 'name': nameSchema}       # a dict

schema = [elementScheme]                            # a list

schema = ([elementScheme], len)                     # a nonempty list

##################################################################################
"""

from __future__ import print_function

import sys
import json
import re as regex

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring  # pylint: disable=undefined-variable


__all__ = ['azzert', 'ensure', 'mock', 'C', 'D', 'E']


def type_of(v):
    return type(v)


class ErrorInfo:
    invalidSchema       = 'schema is invalid'
    wrongType           = 'value type is wrong'
    emptyValue          = 'value cannot be null'
    missingProperty     = 'property is missing'
    redundantProperty   = 'property is redundant'
    emptyList           = 'list cannot be empty'
    notList             = 'value should be a list'
    shouldNotExist      = 'value should not exist'
    notInEnumValues     = 'value is not among the enum list'
    notMatchPattern     = 'value does not match the regex pattern'
    exampleOnlyInMock   = 'example value is only used for mocking'


IDENTIFIER = '^[a-zA-Z_][0-9a-zA-Z_]*$'

AssertOptions = {
    'debug': True,  # throw exceptions or not
    'allowmore': False,  # allow redundant properties or not
    'dictkeypattern': 1,
}


class AzzertionError(Exception):
    def __init__(self, *args):
        super(AzzertionError, self).__init__(*args)


class C(object):
    '''Convert'''
    def __init__(self, arg, *args, **kwargs):
        self.exec = arg if callable(arg) else lambda *args, **kwargs: arg
    def __call__(self, data, *args, **kwargs):
        return self.exec(data)


class D(object):
    '''Default'''
    def __init__(self, arg, *args, **kwargs):
        self.exec = arg if callable(arg) else lambda *args, **kwargs: arg
    def __call__(self, *args, **kwargs):
        return self.exec()


class E(object):
    '''Example'''
    def __init__(self, arg, *args, **kwargs):
        self.exec = arg if callable(arg) else lambda *args, **kwargs: arg
    def __call__(self, *args, **kwargs):
        return self.exec()


def wrap_exception(options, message, *args):
    if len(args):
        message += ': ' + ', '.join([str(arg)
                                     if i != 1 and isinstance(arg, (bool, int, float, str))
                                     else json.dumps(arg, ensure_ascii=False)
                                     for i, arg in enumerate(args)])
    if options['debug']:
        raise AzzertionError(message)
    return message


def is_and_schema(schema):
    return type(schema) is tuple and len(schema) > 0 and schema[0] is True


def is_blank_str(v):
    return isinstance(v, string_types) and v.strip() == ''


def _azzert(value, schema, options, path='', **kwargs):
    if isinstance(schema, C):
        try:
            return True, schema(value)
        except Exception as e:
            return False, e

    if isinstance(schema, D):
        return True, schema() if (value is None) or is_blank_str(value) else value

    if isinstance(schema, E):
        if options['mode'] == 'mock':
            return True, schema()
        return False, wrap_exception(options, ErrorInfo.exampleOnlyInMock, path)

    if schema is True:
        return True, value

    if schema is None:
        return False, wrap_exception(options, ErrorInfo.shouldNotExist, path, value)

    st = type_of(schema)

    if st is str:
        if not isinstance(value, string_types):
            return False, wrap_exception(options, ErrorInfo.wrongType, path, value, str(schema))
        if regex.match(schema, value):
            return True, value
        return False, wrap_exception(options, ErrorInfo.notMatchPattern, path, value, str(schema))

    if st is type:
        if schema is str:
            if isinstance(value, string_types):
                return True, value
        elif type(value) is schema:
            return True, value
        return False, wrap_exception(options, ErrorInfo.wrongType, path, value, str(schema))

    if st is set:
        if value in schema:
            return True, value
        return False, wrap_exception(options, ErrorInfo.notInEnumValues, path, value, list(schema))

    if st is tuple:

        _d, _e = None, None
        for s in schema:
            if isinstance(s, D): _d = s
            if isinstance(s, E): _e = s
        if options['mode'] == 'mock':
            if _d is not None: return _d()
            if _e is not None: return _e()

        if is_and_schema(schema):  # AND
            schema = schema[1:]
            v = value
            for s in schema:
                if isinstance(s, E):
                    continue
                re = _azzert(v, s, options, path)
                if not (type(re) is tuple and re[0] is True):
                    return re
                v = re[1]
            return True, v

        for s in schema:  # OR
            if isinstance(s, E):
                continue
            re = None
            try:
                re = _azzert(value, s, options, path)
            except:
                pass
            if type(re) is tuple and re[0] is True:
                return True, re[1]
        return False, wrap_exception(options, ErrorInfo.wrongType, path, value)

    if st is dict:
        if not isinstance(value, dict):
            return False, wrap_exception(options, ErrorInfo.wrongType, path, value)

        opt_dictkeypattern = options.get('dictkeypattern', 0)
        if opt_dictkeypattern:
            value3 = {}
            pattern_in_keys = False
            for k, s in schema.items():
                if not regex.match(IDENTIFIER, k):
                    pattern_in_keys = True
                    break
            if pattern_in_keys:

                def check_kv(k, v):
                    for sk, sv in schema.items():
                        p = path + '[\'' + sk + '\']'
                        if regex.match(IDENTIFIER, sk):
                            if k != sk:
                                continue
                        else:  # sk is a pattern
                            if not regex.match(sk, k):
                                continue
                        re = _azzert(v, sv, options, p)
                        if type(re) is not tuple:
                            return re
                        if re[0] is not True:
                            return re
                        value3[k] = re[1]

                for k, v in value.items():
                    re = check_kv(k, v)
                    if k not in value3:
                        if re is None:
                            if not options['allowmore']:
                                return False, wrap_exception(options, ErrorInfo.redundantProperty, path + '.' + k)
                        else:
                            return re
                    else:  # (k, v) is ok
                        pass

                return True, value3

        value2 = {}
        v = None

        for k, s in schema.items():
            p = path + '.' + k
            if k not in value:
                if s is None: continue
                if type(s) is tuple:
                    d = list(filter(lambda ss: isinstance(ss, D), s))
                    if len(d):
                        v = d[0]()
                    else:
                        continue
                else:
                    return False, wrap_exception(options, ErrorInfo.missingProperty, p)
            else:
                v = value[k]
            re = _azzert(v, s, options, p)
            if type(re) is not tuple:
                return re
            if re[0] is not True:
                return re

            value2[k] = re[1]

        for k, v in value.items():
            p = path + '.' + k
            if k not in schema:
                if not options['allowmore']:
                    return False, wrap_exception(options, ErrorInfo.redundantProperty, p)
                else:
                    value2[k] = v

        return True, value2

    if st is list:
        if not isinstance(value, (list, tuple, set)):
            return False, wrap_exception(options, ErrorInfo.notList, p, value)

        value2 = []

        s = schema[0]
        for i, v in enumerate(value):
            p = path + '[' + str(i) + ']'
            re = _azzert(v, s, options, p)
            if type(re) is not tuple:
                return re
            if re[0] is not True:
                return re

            value2.append(re[1])

        return True, value2

    if callable(schema):
        re = schema(value)
        if re:
            return True, value
        if schema is len:
            return False, wrap_exception(options, ErrorInfo.emptyList, path)
        return False, wrap_exception(options, ErrorInfo.wrongType, path, value, 'judged by lambda')

    return False, wrap_exception(options, ErrorInfo.invalidSchema)


def azzert(value, schema, options={}, **kwargs):
    opts = {}
    opts.update(AssertOptions)
    opts.update(options)
    opts.update(kwargs)
    opts['mode'] = 'assert'

    re = _azzert(value, schema, opts)
    return True if re[0] is True else re[1]


def ensure(value, schema, options={}, **kwargs):
    opts = {}
    opts.update(AssertOptions)
    opts.update(options)
    opts.update(kwargs)
    opts['debug'] = True
    opts['mode'] = 'ensure'

    re = _azzert(value, schema, opts)
    return re[1]


def _mock(schema, options={}):
    none_flag = '<absent>'

    if schema in [int, float]: return 0
    if schema is str: return ''
    if schema is bool: return False
    if schema is type(None): return None
    if schema is None: return none_flag

    st = type_of(schema)

    uncertain_format = '<uncertain format>'

    if st is tuple:
        for s in schema:
            if isinstance(s, D):
                return s()
        for s in schema:
            if isinstance(s, E):
                return s()
        for s in schema:
            if s in [type(None), None]:
                return _mock(s, options)
        if not is_and_schema(schema):
            for s in schema:
                return _mock(s, options)
        return uncertain_format

    if st is set:
        for s in schema:
            return s

    if st is dict:
        re = {}
        for k, s in schema.items():
            v = _mock(s, options)
            if v == none_flag:
                continue
            re[k] = v
        return re

    if st is list:
        return [_mock(schema[0], options)]


def mock(schema, options={}, **kwargs):
    opts = {}
    opts.update(AssertOptions)
    opts.update(options)
    opts.update(kwargs)
    opts['mode'] = 'mock'

    re = _mock(schema, opts)
    return ensure(re, schema, opts)


if __name__ == '__main__':

    AssertOptions['debug'] = False

    id = 123
    name = 'tom'
    user = {'id': id, 'name': name}
    users = [user]

    try:
        print(azzert(id, int))
        print(azzert(id, None))
        print(azzert(id, True))
        print(azzert(id, (None,)))
        print(azzert(id, (int, None)))
        print(azzert(name, str))
        print(azzert(user, dict))
        print(azzert(user, {'id': int}))
        print(azzert(user, {'id': int, 'age': int}))
        print(azzert(user, {'id': int, 'name': str}))
        print(azzert(users, [{'id': int, 'name': str}]))
        print(azzert(users, [{'id': (True, int, lambda v: v > 0), 'name': str}]))
        user['id'] = None
        print(azzert(users, [{'id': (int, type(None)), 'name': (str,)}]))
        print(azzert(users, [{'id': (None,), 'name': (str,)}]))
        print(azzert(users, [{'id': None, 'name': (str,)}]))
        del user['id']
        print(azzert(users, [{'id': (int, None), 'name': (str,)}]))
        users = []
        print(azzert(users, [{'id': (int, None), 'name': (str,)}]))
        print(azzert(users, ([{'id': (int, None), 'name': (str,)}], len)))
        users = [user]
        print(azzert(users, ([{'id': (int, None), 'name': (str,)}], len)))
    except:
        raise
