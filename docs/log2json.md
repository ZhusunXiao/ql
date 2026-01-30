# log2json.py 使用说明

## 概述

`log2json.py` 是一个使用 ripgrep (rg) 从日志文件中提取数据的脚本，根据 Python 配置文件的正则规则匹配日志行，生成符合 `json2html.py` 格式要求的 JSON 文件。

配置文件使用 `.py` 格式，支持函数动态处理 `subclassname`、`cursor` 和 `layer`。

## 工作流程

```
日志文件 + 配置文件(.py) → log2json.py → JSON → json2html.py → HTML
```

## 命令行用法

```bash
python log2json.py <log_file> <config1.py> [config2.py ...] [-o output.json] [-n name]
```

### 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `<log_file>` | 是 | 日志文件路径 |
| `<config.py>` | 是 | 配置文件路径，可指定多个，支持通配符 |
| `-o output.json` | 否 | 输出文件路径，默认为 `<log_file>_result.json` |
| `-n name` | 否 | 输出 JSON 的 name 字段 |

### 示例

```bash
# 基本用法
python log2json.py log/1.log configs/audio.py

# 多个配置文件
python log2json.py log/1.log configs/audio.py configs/system.py

# 使用通配符
python log2json.py log/1.log configs/*.py -o result.json

# 完整流程：日志 → JSON → HTML
python log2json.py log/1.log configs/*.py -o result.json
python json2html.py result.json result.html
```

---

## Python 配置文件格式

配置文件使用 Python 语法，支持使用函数动态生成 `subclassname`、`cursor` 和 `layer`。

### 基本结构

```python
"""配置文件说明"""
import re

# ===== 一级分类名称（必需）=====
classname = "分类名称"

# ===== 二级分类配置（必需）=====
subclasses = [
    {
        "subclassname": "子分类名",  # 字符串或函数
        "rules": [
            {
                "pattern": "正则表达式",  # 必需：ripgrep 正则
                "cursor": "标识符",       # 字符串或函数
                "layer": 1                # 整数或函数
            }
        ]
    }
]
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `classname` | str | 是 | 一级分类名称 |
| `subclasses` | list | 是 | 二级分类列表 |
| `subclassname` | str \| function | 是 | 二级分类名，可用函数动态生成 |
| `pattern` | str | 是 | ripgrep 正则表达式 |
| `cursor` | str \| function | 否 | 点标识符，可用函数动态生成 |
| `layer` | int \| function | 否 | 层级(1/2/3)，可用函数动态生成 |

### 函数签名

所有函数接收相同的参数：

```python
def my_function(line: str, match: dict) -> str | int:
    """
    Args:
        line: 匹配到的日志行文本
        match: ripgrep 匹配信息，包含 line_number, submatches 等
    
    Returns:
        str (用于 subclassname, cursor) 或 int (用于 layer)
    """
    pass
```

---

## 配置示例

### 示例 1：静态配置

```python
classname = "音频子系统"

subclasses = [
    {
        "subclassname": "ADSP初始化",
        "rules": [
            {
                "pattern": "DMABUFHEAPS",
                "cursor": "DMABUF_INIT",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*init done",
                "cursor": "INIT_DONE",
                "layer": 1
            }
        ]
    }
]
```

### 示例 2：动态 cursor

从日志内容中提取信息生成 cursor：

```python
import re

classname = "音频子系统"

def get_domain_cursor(line, match):
    """从日志中提取 domain 编号"""
    m = re.search(r'domain (\d+)', line)
    if m:
        return "DOMAIN_" + m.group(1)
    return "DOMAIN_X"

subclasses = [
    {
        "subclassname": "Domain管理",
        "rules": [
            {
                "pattern": "domain_deinit",
                "cursor": get_domain_cursor,  # 函数引用
                "layer": 3
            }
        ]
    }
]
```

生成效果：`DOMAIN_0`, `DOMAIN_1`, `DOMAIN_2`, ...

### 示例 3：动态 subclassname

根据日志内容动态分类：

```python
import re

classname = "系统启动"

def classify_selinux(line, match):
    """根据日志内容决定子分类"""
    if 'enforcing' in line.lower():
        return "SELinux强制模式"
    elif 'denied' in line.lower():
        return "SELinux拒绝"
    else:
        return "SELinux其他"

subclasses = [
    {
        "subclassname": classify_selinux,  # 函数引用
        "rules": [
            {"pattern": "SELinux", "cursor": "SELINUX_EVENT", "layer": 1},
            {"pattern": "avc.*denied", "cursor": "AVC_DENIED", "layer": 2}
        ]
    }
]
```

生成效果：同一组规则的匹配结果会被分到不同的子分类中。

### 示例 4：动态 layer

根据日志级别决定层级：

```python
import re

classname = "错误日志"

def layer_by_severity(line, match):
    """根据日志级别决定 layer"""
    if ' E ' in line:  # Error
        return 1
    elif ' W ' in line:  # Warning
        return 2
    else:
        return 3

subclasses = [
    {
        "subclassname": "应用错误",
        "rules": [
            {
                "pattern": "Exception|Error|failed",
                "cursor": "ERROR",
                "layer": layer_by_severity  # 函数引用
            }
        ]
    }
]
```

### 示例 5：组合使用

```python
import re

classname = "网络模块"

def extract_ip(line, match):
    """提取 IP 地址作为 cursor"""
    m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
    return "IP_" + m.group(1).replace('.', '_') if m else "IP_UNKNOWN"

def classify_by_protocol(line, match):
    """根据协议分类"""
    if 'TCP' in line.upper():
        return "TCP连接"
    elif 'UDP' in line.upper():
        return "UDP连接"
    elif 'HTTP' in line.upper():
        return "HTTP请求"
    return "其他网络"

def layer_by_status(line, match):
    """根据状态决定层级"""
    if 'success' in line.lower() or 'connected' in line.lower():
        return 1
    elif 'timeout' in line.lower() or 'retry' in line.lower():
        return 2
    else:
        return 3

subclasses = [
    {
        "subclassname": classify_by_protocol,
        "rules": [
            {
                "pattern": "connect|socket|bind",
                "cursor": extract_ip,
                "layer": layer_by_status
            }
        ]
    }
]
```

---

## 时间戳解析

脚本自动解析 Android logcat 格式的时间戳：

```
MM-DD HH:MM:SS.mmm
07-28 15:15:07.283
```

- 年份默认使用当前年份
- 返回毫秒级 Unix 时间戳

---

## 依赖

- Python 3.6+
- ripgrep (rg)：需要在 `rg/rg.exe` 或系统 PATH 中

---

## 文件组织建议

```
quicklog/
├── log2json.py          # 日志 → JSON
├── json2html.py         # JSON → HTML
├── configs/             # 配置文件目录
│   ├── audio.py         # 音频相关规则
│   ├── system.py        # 系统启动规则
│   └── network.py       # 网络相关规则
├── log/                 # 日志文件目录
│   └── 1.log
└── rg/                  # ripgrep 可执行文件
    └── rg.exe
```
