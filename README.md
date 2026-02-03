# Quick Log - Vue 3 版本

日志时间线可视化工具的 Vue 3 重写版本。

## ✨ 功能特性

- 🚀 **Vue 3 + TypeScript** - 使用最新的 Vue 3 组合式 API 和 TypeScript
- 📊 **ECharts 可视化** - 交互式时间线图表，支持缩放、平移、数据筛选
- 📂 **分类管理** - 侧边栏分类层级展示，支持批量显示/隐藏
- 📌 **标注功能** - 双击添加标注，支持自定义颜色
- 📍 **垂直线标记** - 在时间轴上添加重要时间点标记
- ⭕ **套索选择** - 自由绘制选择区域，框选数据点
- 💾 **数据持久化** - 标注和垂直线自动保存到 localStorage
- 📤 **导入/导出** - 支持标注数据的导入导出

## 📦 安装

```bash
cd ql-vue
npm install
```

## 🚀 开发

```bash
npm run dev
```

## 🏗️ 构建

```bash
npm run build
```

## 📁 项目结构

```
ql-vue/
├── src/
│   ├── components/          # Vue 组件
│   │   ├── CategorySidebar.vue    # 分类侧边栏
│   │   ├── Toolbar.vue            # 工具栏
│   │   ├── TimelineChart.vue      # 时间线图表
│   │   ├── AnnotationPanel.vue    # 标注面板
│   │   └── VLinePanel.vue         # 垂直线面板
│   ├── stores/              # Pinia 状态管理
│   │   └── timeline.ts      # 时间线数据 store
│   ├── types/               # TypeScript 类型定义
│   │   └── index.ts
│   ├── utils/               # 工具函数
│   │   ├── time.ts          # 时间格式化
│   │   ├── colors.ts        # 颜色配置
│   │   └── dataProcessor.ts # 数据处理
│   ├── App.vue              # 主应用组件
│   ├── main.ts              # 入口文件
│   └── style.css            # 全局样式
├── public/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 📊 数据格式

JSON 数据格式与原版保持一致：

```json
{
  "name": "日志分析",
  "all": [
    {
      "classname": "主类名",
      "subclasses": [
        {
          "subclassname": "子类名",
          "points": [
            {
              "cursor": "标识符",
              "msg": "日志消息",
              "line": 1,
              "timestamp": 1722149750970,
              "layer": 1
            }
          ]
        }
      ]
    }
  ]
}
```

## 🎯 使用说明

1. **加载数据**: 拖放 JSON 文件或点击选择文件，或使用示例数据
2. **查看图表**: 使用滚轮缩放，拖拽平移
3. **筛选数据**: 在侧边栏勾选/取消分类
4. **添加标注**: 双击数据点添加标注
5. **添加垂直线**: 点击"添加垂直线"后在图表上点击
6. **框选数据**: 点击"框选"后在图表上绘制选择区域

## 🔧 技术栈

- Vue 3.4
- TypeScript 5
- Vite 5
- Pinia
- ECharts 5.4

## 📝 与原版的差异

Vue 3 版本重构了整体架构：

- 使用 Vue 3 组合式 API 替代原版的纯 JavaScript
- 使用 Pinia 进行状态管理
- 组件化设计，更易维护和扩展
- TypeScript 提供完整的类型支持
- 保持了原版的所有核心功能和视觉风格
