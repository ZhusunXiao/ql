import type {
  RawData,
  TimelinePoint,
  ClassHierarchy,
  SeriesConfig,
  ChartData,
  SeriesDataPoint
} from '@/types'
import { formatTime } from './time'
import { getLayerColor, getLayerName } from './colors'

/**
 * 处理原始 JSON 数据，转换为图表所需格式
 */
export function processRawData(data: RawData): ChartData {
  const allPoints: TimelinePoint[] = []
  const yAxisCategories: string[] = []
  const categoryMap: Record<string, number> = {}
  const classHierarchy: ClassHierarchy[] = []

  // 遍历所有类和子类
  for (const item of data.all) {
    if (!item) continue

    const classname = item.classname || 'Unnamed'
    const subclasses = item.subclasses || []

    const classInfo: ClassHierarchy = {
      classname,
      subclasses: []
    }

    for (const subclass of subclasses) {
      const subclassname = subclass.subclassname || 'Unnamed'
      // 使用 classname|subclassname 作为唯一标识
      const categoryLabel = `${classname}|${subclassname}`

      if (!(categoryLabel in categoryMap)) {
        categoryMap[categoryLabel] = yAxisCategories.length
        yAxisCategories.push(categoryLabel)
      }
      const categoryIndex = categoryMap[categoryLabel]

      classInfo.subclasses.push({
        subclassname,
        categoryLabel
      })

      const points = subclass.points || []
      for (const point of points) {
        const timestampMs = point.timestamp
        const timestamp = timestampMs * 0.001

        allPoints.push({
          timestamp,
          displayTimestampMs: timestampMs,
          cursor: point.cursor || 'N/A',
          msg: point.msg || '',
          line: point.line || 0,
          layer: point.layer || 1,
          classname,
          subclassname,
          category: categoryLabel,
          categoryIndex,
          timeStr: formatTime(timestampMs),
          displayY: categoryIndex
        })
      }
    }

    classHierarchy.push(classInfo)
  }

  // 按时间戳、类别索引、行号排序
  allPoints.sort((a, b) =>
    a.displayTimestampMs - b.displayTimestampMs ||
    a.categoryIndex - b.categoryIndex ||
    a.line - b.line
  )

  // 处理同一毫秒同一类别的点，添加X轴偏移
  const timestampCategoryGroups: Record<string, TimelinePoint[]> = {}
  for (const point of allPoints) {
    const key = `${point.displayTimestampMs}_${point.categoryIndex}`
    if (!timestampCategoryGroups[key]) {
      timestampCategoryGroups[key] = []
    }
    timestampCategoryGroups[key].push(point)
  }

  // 为每组中的点分配偏移量
  for (const points of Object.values(timestampCategoryGroups)) {
    const n = points.length
    if (n > 1) {
      const totalRange = 0.9 // 使用0.9ms范围
      const step = totalRange / (n - 1)
      const offsetStart = -totalRange / 2

      for (let i = 0; i < n; i++) {
        points[i].displayTimestampMs = points[i].displayTimestampMs + offsetStart + (i * step)
        points[i].displayY = points[i].categoryIndex
      }
    }
  }

  // 按 (subclassname, layer) 分组创建系列
  const subclassLayerSeries: Record<string, SeriesDataPoint[]> = {}

  for (const point of allPoints) {
    const key = `${point.subclassname}_${point.layer}`
    if (!subclassLayerSeries[key]) {
      subclassLayerSeries[key] = []
    }

    subclassLayerSeries[key].push({
      value: [point.displayTimestampMs, point.displayY, point.cursor],
      cursor: point.cursor,
      msg: point.msg,
      line: point.line,
      layer: point.layer,
      classname: point.classname,
      subclassname: point.subclassname,
      timeStr: point.timeStr
    })
  }

  // 创建 ECharts 系列配置
  const seriesConfig: SeriesConfig[] = []
  const sortedKeys = Object.keys(subclassLayerSeries).sort()

  for (const key of sortedKeys) {
    const [subclassname, layerStr] = key.split('_')
    const layer = parseInt(layerStr)
    const layerColor = getLayerColor(layer)
    const dataPoints = subclassLayerSeries[key]
    const isLargeData = dataPoints.length > 500

    seriesConfig.push({
      name: `${subclassname} - ${getLayerName(layer)}`,
      type: 'scatter',
      data: dataPoints,
      symbolSize: isLargeData ? 6 : 10,
      large: true,
      largeThreshold: 200,
      progressive: 400,
      progressiveThreshold: 1000,
      itemStyle: {
        color: layerColor,
        borderColor: isLargeData ? 'transparent' : '#fff',
        borderWidth: isLargeData ? 0 : 2
      },
      emphasis: {
        scale: 1.5,
        itemStyle: {
          shadowBlur: 8,
          shadowColor: layerColor,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    })
  }

  // 计算时间范围
  let minTime = 0
  let maxTime = 0
  if (allPoints.length > 0) {
    const timestamps = allPoints.map(p => p.displayTimestampMs)
    minTime = Math.min(...timestamps)
    maxTime = Math.max(...timestamps)
  }

  return {
    yAxisData: yAxisCategories,
    series: seriesConfig,
    rawData: allPoints,
    classHierarchy,
    minTime,
    maxTime
  }
}

/**
 * 根据可见子类重新计算图表系列
 */
export function recalculateSeries(
  rawData: TimelinePoint[],
  yAxisData: string[],
  visibleSubclasses: Set<string>
): { filteredCategories: string[]; series: SeriesConfig[]; categoryIndexMap: Record<string, number> } {
  // 过滤可见的类别
  const filteredCategories: string[] = []
  const categoryIndexMap: Record<string, number> = {}

  for (const cat of yAxisData) {
    if (visibleSubclasses.has(cat)) {
      categoryIndexMap[cat] = filteredCategories.length
      filteredCategories.push(cat)
    }
  }

  // 重建系列
  const subclassLayerSeries: Record<string, { subclassname: string; layer: number; data: SeriesDataPoint[] }> = {}

  for (const point of rawData) {
    if (!visibleSubclasses.has(point.category)) continue

    const key = `${point.subclassname}_${point.layer}`
    if (!subclassLayerSeries[key]) {
      subclassLayerSeries[key] = {
        subclassname: point.subclassname,
        layer: point.layer,
        data: []
      }
    }

    subclassLayerSeries[key].data.push({
      value: [point.displayTimestampMs, categoryIndexMap[point.category], point.cursor],
      cursor: point.cursor,
      msg: point.msg,
      line: point.line,
      layer: point.layer,
      classname: point.classname,
      subclassname: point.subclassname,
      timeStr: point.timeStr
    })
  }

  const series: SeriesConfig[] = []
  for (const group of Object.values(subclassLayerSeries)) {
    const layerColor = getLayerColor(group.layer)
    const isLargeData = group.data.length > 500
    
    series.push({
      name: `${group.subclassname} - ${getLayerName(group.layer)}`,
      type: 'scatter',
      data: group.data,
      symbolSize: isLargeData ? 6 : 12,
      large: true,
      largeThreshold: 200,
      progressive: 400,
      progressiveThreshold: 1000,
      itemStyle: {
        color: layerColor,
        borderColor: isLargeData ? 'transparent' : '#fff',
        borderWidth: isLargeData ? 0 : 2
      },
      emphasis: {
        scale: 1.5,
        itemStyle: {
          shadowBlur: 10,
          shadowColor: layerColor,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    })
  }

  return { filteredCategories, series, categoryIndexMap }
}

/**
 * 判断点是否在多边形内（射线法）
 */
export function isPointInPolygon(point: [number, number], polygon: [number, number][]): boolean {
  if (polygon.length < 3) return false

  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0], yi = polygon[i][1]
    const xj = polygon[j][0], yj = polygon[j][1]

    if (((yi > point[1]) !== (yj > point[1])) &&
        (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi)) {
      inside = !inside
    }
  }
  return inside
}
