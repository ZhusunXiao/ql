# json2html_echarts.py 使用说明

## 概述

`json2html_echarts.py` 是一个 Python 脚本，用于将结构化的 JSON 日志数据转换为交互式 HTML 时间线可视化页面。生成的 HTML 使用 ECharts 图表库，支持缩放、筛选、标注等丰富的交互功能。

## 命令行用法

```bash
python json2html_echarts.py <input.json> [output.html]
```

- `<input.json>`: 必需，输入的 JSON 文件路径
- `[output.html]`: 可选，输出的 HTML 文件路径。如果不指定，将使用输入文件名并替换扩展名为 `.html`

### 示例

```bash
python json2html_echarts.py rules.json                    # 输出 rules.html
python json2html_echarts.py logs/data.json output.html    # 指定输出文件
```

---

## JSON 输入格式规范

### 完整结构定义

```
{
    "name": <string>,           // 图表标题，显示在页面顶部
    "all": [                    // 一级分类数组（必需）
        {
            "classname": <string>,      // 一级分类名称
            "subclasses": [             // 二级分类数组
                {
                    "subclassname": <string>,   // 二级分类名称
                    "points": [                  // 时间点数组
                        {
                            "cursor": <string>,      // 点的唯一标识/简短名称
                            "msg": <string>,         // 详细描述信息
                            "line": <integer>,       // 原始日志行号
                            "timestamp": <integer>,  // 时间戳（毫秒级整数）
                            "layer": <integer>       // 层级（1, 2, 或 3）
                        },
                        ...更多时间点
                    ]
                },
                ...更多二级分类
            ]
        },
        ...更多一级分类
    ]
}
```

### 字段详细说明

| 字段路径 | 类型 | 必需 | 说明 |
|---------|------|------|------|
| `name` | string | 是 | 图表标题，显示在 HTML 页面顶部 |
| `all` | array | 是 | 一级分类的数组，每个元素代表一个主要类别 |
| `all[].classname` | string | 是 | 一级分类的名称，用于分组显示 |
| `all[].subclasses` | array | 是 | 该一级分类下的二级分类数组 |
| `all[].subclasses[].subclassname` | string | 是 | 二级分类的名称，对应 Y 轴的一行 |
| `all[].subclasses[].points` | array | 是 | 该二级分类下的所有时间点 |
| `all[].subclasses[].points[].cursor` | string | 是 | 时间点的唯一标识符/简短名称，显示在 tooltip 中 |
| `all[].subclasses[].points[].msg` | string | 是 | 时间点的详细描述信息 |
| `all[].subclasses[].points[].line` | integer | 是 | 原始日志文件中的行号 |
| `all[].subclasses[].points[].timestamp` | integer | 是 | **Unix 时间戳，单位为毫秒**（13位整数） |
| `all[].subclasses[].points[].layer` | integer | 是 | 层级编号，取值 1、2 或 3，用于颜色区分 |

### layer 字段说明

`layer` 用于在同一二级分类内区分不同层级的事件，每个层级使用不同的颜色：

| layer 值 | 颜色 | 十六进制 | 典型用途 |
|---------|------|---------|---------|
| 1 | 蓝色 | #667eea | 主要/核心事件 |
| 2 | 绿色 | #28a745 | 次要/关联事件 |
| 3 | 黄色 | #ffc107 | 辅助/详细事件 |

当鼠标悬停在某个点上时，会自动用虚线连接同一 `classname + subclassname + layer` 的所有点，展示同类事件的时序关系。

---

## JSON 示例

### 最小有效示例

```json
{
    "name": "简单示例",
    "all": [
        {
            "classname": "模块A",
            "subclasses": [
                {
                    "subclassname": "功能1",
                    "points": [
                        {
                            "cursor": "START",
                            "msg": "功能1开始执行",
                            "line": 1,
                            "timestamp": 1722149707096,
                            "layer": 1
                        },
                        {
                            "cursor": "END",
                            "msg": "功能1执行完成",
                            "line": 10,
                            "timestamp": 1722149707196,
                            "layer": 1
                        }
                    ]
                }
            ]
        }
    ]
}
```

### 完整示例（多层级）

```json
{
    "name": "Android系统日志分析",
    "all": [
        {
            "classname": "系统启动",
            "subclasses": [
                {
                    "subclassname": "Init进程",
                    "points": [
                        {
                            "cursor": "INIT_START",
                            "msg": "Init进程启动",
                            "line": 1,
                            "timestamp": 1722149706000,
                            "layer": 1
                        },
                        {
                            "cursor": "SELINUX_LOAD",
                            "msg": "加载SELinux策略",
                            "line": 5,
                            "timestamp": 1722149706100,
                            "layer": 2
                        },
                        {
                            "cursor": "PROPERTY_SET",
                            "msg": "设置系统属性",
                            "line": 8,
                            "timestamp": 1722149706100,
                            "layer": 3
                        }
                    ]
                },
                {
                    "subclassname": "Zygote进程",
                    "points": [
                        {
                            "cursor": "ZYGOTE_START",
                            "msg": "Zygote启动",
                            "line": 100,
                            "timestamp": 1722149707000,
                            "layer": 1
                        },
                        {
                            "cursor": "PRELOAD_CLASSES",
                            "msg": "预加载Java类",
                            "line": 105,
                            "timestamp": 1722149707500,
                            "layer": 2
                        }
                    ]
                }
            ]
        },
        {
            "classname": "应用层",
            "subclasses": [
                {
                    "subclassname": "Launcher",
                    "points": [
                        {
                            "cursor": "LAUNCHER_START",
                            "msg": "Launcher应用启动",
                            "line": 500,
                            "timestamp": 1722149710000,
                            "layer": 1
                        }
                    ]
                }
            ]
        }
    ]
}
```

---

## 时间戳格式说明

**重要**：`timestamp` 字段必须是 **毫秒级 Unix 时间戳**（13位整数）。

### 转换示例

| 可读时间 | 毫秒级时间戳 |
|---------|-------------|
| 2024-07-28 14:15:07.096 | 1722149707096 |
| 2024-07-28 14:15:06.139 | 1722149706139 |

### 各语言生成毫秒时间戳的方法

```python
# Python
import time
timestamp_ms = int(time.time() * 1000)

# 或从 datetime 对象
from datetime import datetime
dt = datetime.now()
timestamp_ms = int(dt.timestamp() * 1000)
```

```javascript
// JavaScript
const timestamp_ms = Date.now();
// 或
const timestamp_ms = new Date().getTime();
```

```java
// Java
long timestamp_ms = System.currentTimeMillis();
```

---

## 生成的 HTML 功能

生成的 HTML 文件包含以下交互功能：

1. **时间轴视图**：X 轴为时间（格式 HH:MM:SS.mmm），Y 轴为二级分类
2. **缩放功能**：
   - X 轴：底部滑块 + 鼠标滚轮
   - Y 轴：右侧滑块
3. **筛选功能**：左侧边栏可勾选/取消勾选分类
4. **标注功能**：双击点可添加标注，标注会保存到浏览器 localStorage
5. **选区功能**：可绘制不规则选区选择多个点
6. **层级连线**：悬停时显示同层级点的连接线
7. **密集点提示**：像素距离接近的点会在 tooltip 中合并显示

---

## 数据结构可视化

```
JSON 结构                          对应 HTML 显示
─────────────────────────────────────────────────────────
name ─────────────────────────────→ 页面标题

all[]                              左侧边栏分组
  ├── classname ──────────────────→ 一级分类（可折叠）
  │     │                           背景色区分不同分类
  │     │
  │     └── subclasses[]
  │           ├── subclassname ───→ Y 轴标签（一行）
  │           │                     二级分类（可勾选）
  │           │
  │           └── points[]
  │                 ├── timestamp → X 轴位置（时间）
  │                 ├── layer ────→ 点的颜色
  │                 ├── cursor ───→ 点的标题
  │                 ├── msg ──────→ tooltip 详情
  │                 └── line ─────→ tooltip 显示行号
```

---

## 注意事项

1. **timestamp 必须是整数**：不要使用浮点数或字符串
2. **layer 取值范围**：1-3，超出范围会显示灰色
3. **同一毫秒的事件**：脚本会自动在 ±0.45ms 范围内均匀分布，避免完全重叠
4. **大数据量**：支持 10000+ 个点，已启用 ECharts 的 large 模式优化
5. **文件编码**：JSON 文件必须使用 UTF-8 编码
6. **空数组**：`subclasses` 和 `points` 可以为空数组，但不能省略

---

## 错误排查

| 错误信息 | 可能原因 |
|---------|---------|
| `JSON 解析错误` | JSON 格式不正确，检查逗号、引号、括号 |
| `文件不存在` | 输入文件路径错误 |
| 时间轴显示异常 | timestamp 不是毫秒级整数 |
| 点不显示 | layer 值不是 1、2、3 或 points 数组为空 |

---

## TypeScript/JSON Schema（供程序验证使用）

```typescript
interface LogVisualizationData {
    name: string;
    all: ClassItem[];
}

interface ClassItem {
    classname: string;
    subclasses: SubclassItem[];
}

interface SubclassItem {
    subclassname: string;
    points: PointItem[];
}

interface PointItem {
    cursor: string;      // 点的标识符
    msg: string;         // 详细信息
    line: number;        // 整数，原始行号
    timestamp: number;   // 整数，毫秒级Unix时间戳
    layer: 1 | 2 | 3;    // 层级
}
```

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "all"],
    "properties": {
        "name": { "type": "string" },
        "all": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["classname", "subclasses"],
                "properties": {
                    "classname": { "type": "string" },
                    "subclasses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["subclassname", "points"],
                            "properties": {
                                "subclassname": { "type": "string" },
                                "points": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["cursor", "msg", "line", "timestamp", "layer"],
                                        "properties": {
                                            "cursor": { "type": "string" },
                                            "msg": { "type": "string" },
                                            "line": { "type": "integer" },
                                            "timestamp": { "type": "integer" },
                                            "layer": { "type": "integer", "enum": [1, 2, 3] }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```
