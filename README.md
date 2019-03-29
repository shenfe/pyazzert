# azzert

数据格式检查。

## 断言

定义数据格式schema：

```py
schema = int                                    # 必须为整数

schema = lambda v: v > 0                        # 必须被函数返回真值

schema = (int, float, str)                      # 或；可以为整数或浮点数或字符串

schema = (int, float, str, type(None))          # ...还可以为空值

schema = (int, float, str, type(None), None)    # ...还可以不存在

schema = (True, int, lambda v: v >= 0)          # 与（同“或”的区别在于必须将True作为元组首个元素）；必须为整数且大于等于0

schema = {'id': idSchema, 'name': nameSchema}   # 字典；字段值为字段的schema

schema = {'id': None, 'name': nameSchema}       # 不可以有id字段

schema = [elementScheme]                        # 列表；元素为元素的schema

schema = (True, [elementScheme], len)           # 非空列表

schema = {'a', 'b'}                             # 枚举值

schema = r'^\d+$'                               # 正则表达式（pattern字符串）
```

执行断言：

```py
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

try:
    result = azzert(data, schema)
except Exception as e:
    print(e)
```

格式正确会返回True，否则抛出错误。

### 选项

```py
result = azzert(data, schema, debug=False)  # 有错不抛出异常，而是返回错误信息
result = azzert(data, schema, allowmore=True)  # 允许data中的dict值包含对应schema中不存在的字段
```

## 使用C、D、E功能

C（Convert，转换），D（Default，默认值），E（Example，示例值）。这些功能可以将断言扩展出数据保证、数据mock等功能。

### 转换

```py
from azzert import C

schema = True, str, C(lambda s: s.lower())
```

### 默认值

```py
from azzert import D

schema = True, str, D('default')
```

### 示例值

```py
from azzert import E

schema = True, str, E('example')
```

### 数据保证

数据保证与断言的区别在于，前者返回数据，后者返回断言结果。

```py
from azzert import ensure, D

schema = {
    'id': int,
    'name': (str, D('')),
}

data = {'id': 123}

data2 = ensure(data, schema)

assert data2 == {'id': 123, 'name': ''}
```

### 数据mock

数据mock，根据schema中定义的示例值生成示例数据。

```py
from azzert import mock, E

schema = {
    'id': (int, E(123)),
    'name': (str, E('tom')),
}

data = mock(schema)

assert data == {'id': 123, 'name': 'tom'}
```
