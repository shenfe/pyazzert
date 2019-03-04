# coding: utf8

"""
################ assertion schema ################

schema = int  # a single type

schema = lambda v: v in {0, 1}  # a judging function

schema = (int, float, str)  # OR

schema = (int, float, str, NoneType)  # can be `null`

schema = (int, float, str, NoneType, None)  # can be missing

schema = (True, (int, float), lambda v: v >= 0)  # AND

schema = {0, 1, 2}  # enum

schema = {'id': idSchema, 'name': nameSchema}  # a dict

schema = [elementScheme]  # a list

schema = ([elementScheme], len)  # a nonempty list

##################################################
"""

from __future__ import print_function

import sys
import types
import json
import re as regex

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring


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


AssertOptions = {
    'debug': True,  # throw exceptions or not
    'allowmore': False,  # allow redundant properties or not
}


class AzzertionError(Exception):
    def __init__(self, *args):
        super(AzzertionError, self).__init__(*args)


class C(object):
    def __init__(self, conv):
        self.conv = conv


class D(object):
    def __init__(self, value):
        self.value = value


class E(object):
    def __init__(self, value):
        self.value = value


def wrap_exception(options, message, *args):
    if len(args):
        message += ': ' + ', '.join([str(arg)
                                     if i != 1 and isinstance(arg, (bool, int, float, str))
                                     else json.dumps(arg)
                                     for i, arg in enumerate(args)])
    if options['debug']:
        raise AzzertionError(message)
    return message


def is_and_schema(schema):
    return type(schema) is tuple and len(schema) > 0 and schema[0] is True


def is_blank_str(v):
    return isinstance(v, string_types) and v.strip() == ''


def _azzert(value, schema, options, path=''):
    if isinstance(schema, C):
        try:
            return True, schema.conv(value)
        except Exception as e:
            return False, e

    if isinstance(schema, D):
        return True, schema.value if value is None or is_blank_str(value) else value

    if isinstance(schema, E):
        if options['mode'] == 'mock':
            return True, schema.value
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
        if is_and_schema(schema):  # AND
            schema = schema[1:]
            v = value
            for s in schema:
                if isinstance(s, E):
                    continue
                re = _azzert(v, s, options, path)
                if type(re) is not tuple:
                    return re
                if re[0] is not True:
                    return re
                v = re[1]
            return True, v

        for s in schema:  # OR
            re = None
            try:
                re = _azzert(value, s, options, path)
            except Exception:
                pass
            if type(re) is tuple and re[0] is True:
                return True, re[1]
        return False, wrap_exception(options, ErrorInfo.wrongType, path, value)

    if st is dict:
        if not isinstance(value, dict):
            return False, wrap_exception(options, ErrorInfo.wrongType, path, value)

        value2 = {}
        v = None

        for k, s in schema.items():
            p = path + '.' + k
            if k not in value:
                if s is None: continue
                if type(s) is tuple:
                    d = filter(lambda ss: isinstance(ss, D), s)
                    if len(d):
                        v = d[0].value
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

        if not options['allowmore']:
            for k, v in value.items():
                p = path + '.' + k
                if k not in schema:
                    return False, wrap_exception(options, ErrorInfo.redundantProperty, p)

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
    if schema is types.NoneType: return None
    if schema is None: return none_flag

    st = type_of(schema)

    uncertain_format = '<uncertain format>'

    if st is tuple:
        for s in schema:
            if isinstance(s, E):
                return s.value
        for s in schema:
            if isinstance(s, D):
                return s.value
        for s in schema:
            if s in [types.NoneType, None]:
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
        print(azzert(users, [{'id': (int, types.NoneType), 'name': (str,)}]))
        print(azzert(users, [{'id': (None,), 'name': (str,)}]))
        print(azzert(users, [{'id': None, 'name': (str,)}]))
        del user['id']
        print(azzert(users, [{'id': (int, None), 'name': (str,)}]))
        users = []
        print(azzert(users, [{'id': (int, None), 'name': (str,)}]))
        print(azzert(users, ([{'id': (int, None), 'name': (str,)}], len)))
        users = [user]
        print(azzert(users, ([{'id': (int, None), 'name': (str,)}], len)))
    except Exception as e:
        raise e
