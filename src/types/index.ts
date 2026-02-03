// 原始 JSON 数据中的点
export interface RawPoint {
  cursor: string
  msg: string
  line: number
  timestamp: number // 毫秒时间戳
  layer: number
}

// 原始 JSON 数据中的子类
export interface RawSubClass {
  subclassname: string
  points: RawPoint[]
}

// 原始 JSON 数据中的类
export interface RawClass {
  classname: string
  subclasses: RawSubClass[]
}

// 原始 JSON 数据结构
export interface RawData {
  name: string
  all: RawClass[]
}

// 处理后的时间点数据
export interface TimelinePoint {
  timestamp: number          // 毫秒时间戳
  displayTimestampMs: number // 显示用时间戳（处理密集点偏移后）
  cursor: string
  msg: string
  line: number
  layer: number
  classname: string
  subclassname: string
  category: string           // classname|subclassname 格式
  categoryIndex: number      // Y轴索引
  timeStr: string           // HH:MM:SS.mmm 格式
  displayY: number          // 显示用Y坐标
}

// 类层级信息（用于侧边栏）
export interface ClassHierarchy {
  classname: string
  subclasses: {
    subclassname: string
    categoryLabel: string
  }[]
}

// ECharts 系列数据点
export interface SeriesDataPoint {
  value: [number, number, string] // [timestamp, categoryIndex, cursor]
  cursor: string
  msg: string
  line: number
  layer: number
  classname: string
  subclassname: string
  timeStr: string
}

// ECharts 系列配置
export interface SeriesConfig {
  name: string
  type: 'scatter'
  data: SeriesDataPoint[]
  symbolSize: number
  large?: boolean
  largeThreshold?: number
  progressive?: number
  progressiveThreshold?: number
  itemStyle: {
    color: string
    borderColor?: string
    borderWidth?: number
  }
  emphasis?: {
    scale: number
    itemStyle: {
      shadowBlur: number
      shadowColor: string
      borderColor?: string
      borderWidth?: number
    }
  }
}

// 图表数据
export interface ChartData {
  yAxisData: string[]
  series: SeriesConfig[]
  rawData: TimelinePoint[]
  classHierarchy: ClassHierarchy[]
  minTime: number
  maxTime: number
}

// 标注数据
export interface Annotation {
  text: string
  color: string
  x: number
  yCategory: string
  pointData: SeriesDataPoint
  createdAt: string
}

// 垂直线数据
export interface VLine {
  time: number
  text: string | null
  color: string
  createdAt: string
}

// 存储数据结构
export interface StorageData {
  annotations: Record<string, Annotation>
  vlines: Record<string, VLine>
}

// 选中的点
export interface SelectedPoint {
  x: number
  y: number
  cursor: string
  msg: string
  line: number
  layer: number
  classname: string
  subclassname: string
  timeStr: string
}
