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

import types
import json
import re as regex


__all__ = ['azzert']


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


AssertOptions = {
    'debug': True,  # throw exceptions or not
    'allowmore': False,  # allow redundant properties or not
}


class AzzertionError(Exception):
    def __init__(self, *args):
        super(AzzertionError, self).__init__(*args)


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


def _azzert(value, schema, options, path=''):
    if schema is True:
        return True

    if schema is None:
        return wrap_exception(options, ErrorInfo.shouldNotExist, path, value)

    st = type_of(schema)

    if st is str:
        if not isinstance(value, (str, unicode)):
            return wrap_exception(options, ErrorInfo.wrongType, path, value, str(schema))
        if regex.match(schema, value):
            return True
        return wrap_exception(options, ErrorInfo.notMatchPattern, path, value, str(schema))

    if st is type:
        if type(value) is schema:
            return True
        return wrap_exception(options, ErrorInfo.wrongType, path, value, str(schema))

    if callable(schema):
        re = schema(value)
        if re:
            return True
        if schema is len:
            return wrap_exception(options, ErrorInfo.emptyList, path)
        return wrap_exception(options, ErrorInfo.wrongType, path, value, 'judged by lambda')

    if st is set:
        if value in schema:
            return True
        return wrap_exception(options, ErrorInfo.notInEnumValues, path, value, list(schema))

    if st is tuple:
        if is_and_schema(schema):  # AND
            schema = schema[1:]
            for s in schema:
                re = _azzert(value, s, options, path)
                if re is not True:
                    return re
            return True

        for s in schema:  # OR
            re = None
            try:
                re = _azzert(value, s, options, path)
            except Exception:
                pass
            if re is True:
                return True
        return wrap_exception(options, ErrorInfo.wrongType, path, value)

    if st is dict:
        if not isinstance(value, dict):
            return wrap_exception(options, ErrorInfo.wrongType, path, value)

        for k, s in schema.items():
            p = path + '.' + k
            if k not in value:
                if s is None:
                    continue
                if type(s) is tuple and None in s:
                    continue
                return wrap_exception(options, ErrorInfo.missingProperty, p)
            v = value[k]
            re = _azzert(v, s, options, p)
            if re is not True:
                return re

        if not options['allowmore']:
            for k, v in value.items():
                p = path + '.' + k
                if k not in schema:
                    return wrap_exception(options, ErrorInfo.redundantProperty, p)

        return True

    if st is list:
        if not isinstance(value, (list, tuple, set)):
            return wrap_exception(options, ErrorInfo.notList, p, value)

        s = schema[0]
        for i, v in enumerate(value):
            p = path + '[' + str(i) + ']'
            re = _azzert(v, s, options, p)
            if re is not True:
                return re

        return True

    return wrap_exception(options, ErrorInfo.invalidSchema)


def azzert(value, schema, options={}, **kwargs):
    opts = {}
    opts.update(AssertOptions)
    opts.update(options)
    opts.update(kwargs)

    return _azzert(value, schema, opts)
