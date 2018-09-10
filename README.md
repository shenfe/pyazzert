# azzert

数据格式检查。

## 使用

定义数据格式schema：

```py
schema = int                                    # 必须为整数

schema = lambda v: v > 0                        # 必须被函数返回真值

schema = (int, float, str)                      # 或；可以为整数或浮点数或字符串

schema = (int, float, str, NoneType)            # ...还可以为空值

schema = (int, float, str, NoneType, None)      # ...还可以不存在

schema = (True, int, lambda v: v >= 0)          # 与（同“或”的区别在于必须将True作为元组首个元素）；必须为整数且大于等于0

schema = {'id': idSchema, 'name': nameSchema}   # 字典；字段值为字段的schema

schema = {'id': None, 'name': nameSchema}       # 不可以有id字段

schema = [elementScheme]                        # 列表；元素为元素的schema

schema = ([elementScheme], len)                 # 非空列表
```

执行断言：

```py
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
    print(e)
```

格式正确会返回True，否则抛出错误。

### 选项

```py
result = azzert(data, schema, debug=False)  # 有错不抛出异常，而是返回错误信息
result = azzert(data, schema, allowmore=True)  # 允许data中的dict值包含对应schema中不存在的字段
```
