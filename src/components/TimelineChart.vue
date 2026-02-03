<template>
  <div ref="chartContainer" class="chart-container">
    <div ref="chartDom" class="chart-dom"></div>
    <svg ref="connectionSvg" class="connection-svg"></svg>
    <canvas ref="lassoCanvas" class="lasso-canvas"></canvas>
  </div>

  <!-- 选中点详情面板 -->
  <div 
    v-if="store.selectedPoints.length > 0" 
    class="selection-panel"
    :style="{ top: panelPosition.y + 'px', left: panelPosition.x + 'px' }"
  >
    <div class="selection-header" @mousedown="startDragPanel">
      <div class="selection-title">
        <span class="icon">✅</span>
        <span>已选中 <strong>{{ store.selectedPoints.length }}</strong> 个点</span>
        <span class="drag-hint">⋮⋮</span>
      </div>
      <div class="selection-meta">
        <span v-if="selectionTimeSpan" class="time-span">⏱️ {{ selectionTimeSpan }}</span>
        <span class="time-range">{{ selectionTimeRange }}</span>
      </div>
      <button class="close-btn" @click="clearSelection" title="清除选择">✕</button>
    </div>
    <div class="selection-content">
      <div 
        v-for="(point, index) in sortedSelectedPoints" 
        :key="`${point.value[0]}-${point.line}`"
        class="selection-item"
        :style="{ borderLeftColor: getLayerColor(point.layer) }"
      >
        <div class="item-line"><span class="line-num">{{ point.line }}</span><span class="item-msg">{{ point.msg }}</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useTimelineStore } from '@/stores'
import { formatTime, getLayerColor, getClassColor, CLASS_COLORS, isPointInPolygon } from '@/utils'
import type { SeriesDataPoint } from '@/types'

const emit = defineEmits<{
  dblclick: [point: SeriesDataPoint]
  vlineClick: [time: number]
  annotationClick: [key: string]
}>()

const store = useTimelineStore()

// 计算选中点的时间跨度
const selectionTimeSpan = computed(() => {
  if (store.selectedPoints.length < 2) return ''
  
  const times = store.selectedPoints.map(p => p.value[0])
  const minTime = Math.min(...times)
  const maxTime = Math.max(...times)
  const diffMs = maxTime - minTime
  
  if (diffMs < 1000) {
    return `${diffMs.toFixed(0)}ms`
  } else if (diffMs < 60000) {
    return `${(diffMs / 1000).toFixed(2)}s`
  } else if (diffMs < 3600000) {
    const mins = Math.floor(diffMs / 60000)
    const secs = ((diffMs % 60000) / 1000).toFixed(1)
    return `${mins}m ${secs}s`
  } else {
    const hours = Math.floor(diffMs / 3600000)
    const mins = Math.floor((diffMs % 3600000) / 60000)
    return `${hours}h ${mins}m`
  }
})

// 计算选中点的时间范围显示
const selectionTimeRange = computed(() => {
  if (store.selectedPoints.length === 0) return ''
  
  const times = store.selectedPoints.map(p => p.value[0])
  const minTime = Math.min(...times)
  const maxTime = Math.max(...times)
  
  return `${formatTime(minTime)} → ${formatTime(maxTime)}`
})

// 按行号排序的选中点
const sortedSelectedPoints = computed(() => {
  return [...store.selectedPoints].sort((a, b) => a.line - b.line)
})

// 清除选择
function clearSelection() {
  store.selectedPoints = []
}

// 选中点面板拖动相关
const panelPosition = ref({ x: 240, y: 100 })
let isDraggingPanel = false
let dragStart = { x: 0, y: 0 }

function startDragPanel(e: MouseEvent) {
  isDraggingPanel = true
  dragStart.x = e.clientX - panelPosition.value.x
  dragStart.y = e.clientY - panelPosition.value.y
  document.addEventListener('mousemove', onDragPanel)
  document.addEventListener('mouseup', stopDragPanel)
  e.preventDefault()
}

function onDragPanel(e: MouseEvent) {
  if (!isDraggingPanel) return
  panelPosition.value.x = e.clientX - dragStart.x
  panelPosition.value.y = e.clientY - dragStart.y
  
  // 限制在视窗内
  panelPosition.value.x = Math.max(0, Math.min(panelPosition.value.x, window.innerWidth - 300))
  panelPosition.value.y = Math.max(0, Math.min(panelPosition.value.y, window.innerHeight - 200))
}

function stopDragPanel() {
  isDraggingPanel = false
  document.removeEventListener('mousemove', onDragPanel)
  document.removeEventListener('mouseup', stopDragPanel)
}

const chartContainer = ref<HTMLDivElement | null>(null)
const chartDom = ref<HTMLDivElement | null>(null)
const connectionSvg = ref<SVGSVGElement | null>(null)
const lassoCanvas = ref<HTMLCanvasElement | null>(null)

let chart: echarts.ECharts | null = null
let pointsByCategory: Record<string, { x: number; y: number; layer: number; line: number; cursor: string; msg: string; timeStr: string }[]> = {}
let pointsByCategoryLayer: Record<string, { x: number; y: number }[]> = {}

// 套索相关
let isDrawing = false
let lassoPath: [number, number][] = []
let lassoCtx: CanvasRenderingContext2D | null = null

// 防抖函数
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  let timer: ReturnType<typeof setTimeout> | null = null
  return ((...args: any[]) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }) as T
}

// 初始化图表
function initChart() {
  if (!chartDom.value || !store.chartData) return

  chart = echarts.init(chartDom.value)

  // 构建点的索引
  buildPointIndex()

  // 设置图表选项
  const option = getChartOption()
  chart.setOption(option)

  // 设置正确的图表高度
  updateChartHeight()

  // 绑定事件
  bindChartEvents()
}

// 构建点索引
function buildPointIndex() {
  if (!store.chartData) return

  pointsByCategory = {}
  pointsByCategoryLayer = {}

  for (const series of store.chartData.series) {
    for (const point of series.data) {
      const flatPoint = {
        x: point.value[0],
        y: point.value[1],
        layer: point.layer,
        line: point.line,
        cursor: point.cursor,
        msg: point.msg,
        timeStr: point.timeStr
      }

      // 类别索引
      const categoryKey = `${point.classname}|${point.subclassname}`
      if (!pointsByCategory[categoryKey]) {
        pointsByCategory[categoryKey] = []
      }
      pointsByCategory[categoryKey].push(flatPoint)

      // 类别+层级索引
      const layerKey = `${categoryKey}|${point.layer}`
      if (!pointsByCategoryLayer[layerKey]) {
        pointsByCategoryLayer[layerKey] = []
      }
      pointsByCategoryLayer[layerKey].push({ x: flatPoint.x, y: flatPoint.y })
    }
  }
}

// 获取图表选项
function getChartOption(): echarts.EChartsOption {
  if (!store.chartData) return {}

  const visibleData = store.getVisibleSeries()
  if (!visibleData) return {}

  const { filteredCategories, series } = visibleData

  // 计算主类区域标记
  const markAreaData = calculateMarkAreaData(filteredCategories)

  // 添加区域标记系列
  if (markAreaData.length > 0) {
    series.unshift({
      name: '_markArea',
      type: 'scatter',
      data: [],
      markArea: {
        silent: true,
        data: markAreaData
      }
    } as any)
  }

  // 根据数据量决定是否禁用动画
  const totalPoints = series.reduce((sum, s) => sum + (s.data?.length || 0), 0)
  const isLargeData = totalPoints > 2000

  return {
    animation: !isLargeData,
    animationDuration: isLargeData ? 0 : 300,
    animationDurationUpdate: isLargeData ? 0 : 200,
    title: {
      text: '日志时间线分析',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 20,
        color: '#667eea'
      }
    },
    tooltip: {
      trigger: 'item',
      confine: true,
      enterable: true,
      hideDelay: 100,
      appendToBody: false,
      triggerOn: 'mousemove',
      position: (point: number[], params: any, dom: any, rect: any, size: any) => {
        return calculateTooltipPosition(point, size)
      },
      formatter: (params: any) => {
        if (!params || !params.data) return ''
        return formatTooltip(params)
      },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#667eea',
      borderWidth: 2,
      textStyle: {
        color: '#1a1a1a',
        fontSize: 13,
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        fontWeight: 500
      },
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.15); pointer-events: auto; max-height: 50vh; overflow-y: auto; font-family: Consolas, Monaco, "Courier New", monospace !important; font-size: 13px !important; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; font-weight: 500; user-select: text; -webkit-user-select: text; -moz-user-select: text; cursor: text;'
    },
    grid: {
      left: '220px',
      right: '50px',
      top: '80px',
      bottom: '120px',
      containLabel: false
    },
    xAxis: {
      type: 'time',
      axisPointer: {
        show: true,
        type: 'line',
        lineStyle: {
          color: '#667eea',
          width: 1,
          type: 'solid'
        },
        label: {
          show: true,
          backgroundColor: '#667eea',
          formatter: (params: any) => formatTime(params.value)
        }
      },
      axisLabel: {
        formatter: (value: number) => formatTime(value),
        rotate: 45
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#999'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: filteredCategories,
      axisPointer: {
        show: false,
        type: 'none'
      },
      axisLabel: {
        fontSize: 11,
        width: 200,
        overflow: 'break',
        formatter: (value: string) => {
          const idx = value.indexOf('|')
          return idx >= 0 ? value.substring(idx + 1) : value
        }
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#f0f0f0'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#999'
        }
      }
    },
    dataZoom: [
      {
        id: 'dataZoomX',
        type: 'slider',
        xAxisIndex: 0,
        start: 0,
        end: 100,
        height: 30,
        bottom: 70,
        brushSelect: false,
        handleSize: '80%',
        dataBackground: {
          lineStyle: { color: '#667eea' },
          areaStyle: { color: 'rgba(102, 126, 234, 0.2)' }
        },
        fillerColor: 'rgba(102, 126, 234, 0.2)',
        borderColor: '#667eea',
        handleStyle: { color: '#667eea' },
        moveHandleStyle: { color: '#764ba2' },
        textStyle: { color: '#666' }
      },
      {
        id: 'dataZoomY',
        type: 'inside',
        xAxisIndex: 0,
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
        moveOnMouseWheel: false
      },
      {
        id: 'dataZoomYSlider',
        type: 'slider',
        yAxisIndex: 0,
        start: 0,
        end: 100,
        right: 10,
        width: 20,
        brushSelect: false,
        handleSize: '80%',
        fillerColor: 'rgba(118, 75, 162, 0.2)',
        borderColor: '#764ba2',
        handleStyle: { color: '#764ba2' },
        textStyle: { color: '#666' }
      },
      {
        id: 'dataZoomYInside',
        type: 'inside',
        yAxisIndex: 0,
        start: 0,
        end: 100,
        zoomOnMouseWheel: false,
        moveOnMouseMove: false
      }
    ],
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none',
          title: { zoom: '区域缩放', back: '还原' }
        },
        restore: { title: '重置' },
        saveAsImage: {
          title: '保存图片',
          name: `timeline-${Date.now()}`,
          pixelRatio: 2
        }
      },
      right: 20,
      top: 20
    },
    series
  }
}

// 计算主类区域标记
function calculateMarkAreaData(filteredCategories: string[]): any[] {
  const markAreaData: any[] = []
  let currentIndex = 0

  for (let clsIdx = 0; clsIdx < store.classHierarchy.length; clsIdx++) {
    const cls = store.classHierarchy[clsIdx]
    let visibleCount = 0

    for (const sub of cls.subclasses) {
      if (store.visibleSubclasses.has(sub.categoryLabel)) {
        visibleCount++
      }
    }

    if (visibleCount > 0) {
      const opacity = (clsIdx % 2 === 0) ? '20' : '40'
      markAreaData.push([
        {
          yAxis: currentIndex,
          itemStyle: { color: CLASS_COLORS[clsIdx % CLASS_COLORS.length] + opacity }
        },
        { yAxis: currentIndex + visibleCount - 1 }
      ])
      currentIndex += visibleCount
    }
  }

  return markAreaData
}

// 计算tooltip位置
function calculateTooltipPosition(point: number[], size: any): [number, number] {
  const chartRect = chartDom.value?.getBoundingClientRect()
  if (!chartRect) return [point[0] + 5, point[1] + 5]

  const tooltipWidth = size.contentSize[0] || 300
  const tooltipHeight = size.contentSize[1] || 200

  let x = point[0] + 10
  let y = point[1] + 10

  if (x + tooltipWidth > chartRect.width - 20) {
    x = point[0] - tooltipWidth - 10
  }
  
  if (y + tooltipHeight > chartRect.height - 20) {
    y = point[1] - tooltipHeight - 10
  }

  x = Math.max(10, x)
  y = Math.max(10, y)

  return [x, y]
}

// 格式化工具提示
function formatTooltip(params: any): string {
  const data = params.data
  const currentSubclass = data.subclassname
  const currentClassname = data.classname
  const currentX = data.value[0]
  const currentY = data.value[1]

  // 检查当前点是否在选中集合中
  const isInSelection = store.selectedPoints.some(p => 
    p.value[0] === currentX && p.line === data.line && p.subclassname === currentSubclass
  )

  // 如果有选中的点且当前点在选中集合中，显示所有选中的点
  if (store.selectedPoints.length > 0 && isInSelection) {
    return formatSelectedPointsTooltip(data, params.color)
  }

  // 获取当前点像素位置
  const currentPixel = chart?.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [currentX, currentY])
  const pixelThreshold = 40

  // 获取同类别的点
  const categoryKey = `${currentClassname}|${currentSubclass}`
  const categoryPoints = pointsByCategory[categoryKey] || []

  // 收集像素距离近的点
  let nearbyPoints: any[] = []

  for (const point of categoryPoints) {
    const pointPixel = chart?.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [point.x, point.y])
    if (pointPixel && currentPixel) {
      const pixelDistance = Math.abs(pointPixel[0] - currentPixel[0])
      if (pixelDistance <= pixelThreshold) {
        nearbyPoints.push(point)
      }
    }
  }

  // 按时间和行号排序
  nearbyPoints.sort((a, b) => {
    if (a.x !== b.x) return a.x - b.x
    return a.line - b.line
  })

  // 如果只有1个点，显示单点详情
  if (nearbyPoints.length <= 1) {
    return formatSinglePointTooltip(data, params.color)
  }

  // 多个点，显示密集区域列表
  return formatDenseAreaTooltip(nearbyPoints, data, currentX)
}

// 格式化单点tooltip
function formatSinglePointTooltip(data: any, color: string): string {
  const layerColor = getLayerColor(data.layer)
  const fontStyle = "font-family: Consolas, Monaco, 'Courier New', monospace; -webkit-font-smoothing: antialiased; font-weight: 500;"
  let html = `<div style="padding: 10px; max-width: 500px; ${fontStyle}">`
  html += '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
  html += `<span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${layerColor};"></span>`
  html += `<span style="font-weight: 600; color: #000; font-size: 14px;">L${data.layer}</span>`
  html += `<span style="color: #222; font-size: 14px; font-weight: 500;">Line ${data.line}</span>`
  html += `<span style="color: #444; font-size: 13px;">${data.timeStr}</span>`
  html += '</div>'
  html += `<div style="padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 13px; color: #000; font-weight: 500; word-wrap: break-word; white-space: pre-wrap; border-left: 4px solid ${layerColor}; line-height: 1.5;">`
  html += data.msg
  html += '</div></div>'
  return html
}

// 格式化密集区域tooltip（新格式：一行显示 layer line log）
function formatDenseAreaTooltip(nearbyPoints: any[], currentData: any, currentX: number): string {
  const fontStyle = "font-family: Consolas, Monaco, 'Courier New', monospace; -webkit-font-smoothing: antialiased; font-weight: 500;"
  let html = `<div id="tooltip-scroll-container" style="padding: 10px; max-width: 550px; max-height: 40vh; overflow-y: auto; ${fontStyle}">`
  html += `<div style="font-weight: 700; font-size: 14px; margin-bottom: 8px; color: #667eea;">🔍 密集区域 (${nearbyPoints.length} 个点)</div>`
  html += '<div style="font-size: 13px; line-height: 1.5;">'

  nearbyPoints.forEach((point) => {
    const layerColor = getLayerColor(point.layer)
    const isCurrentPoint = (point.x === currentX && point.line === currentData.line)
    const bgColor = isCurrentPoint ? '#e7f1ff' : 'transparent'
    
    html += `<div style="display: flex; padding: 5px 6px; background: ${bgColor}; border-radius: 3px; margin: 3px 0; align-items: flex-start;">`
    html += `<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${layerColor}; margin-top: 5px; flex-shrink: 0;"></span>`
    html += `<span style="width: 32px; text-align: right; color: #111; flex-shrink: 0; margin-left: 6px; font-weight: 600;">L${point.layer}</span>`
    html += `<span style="width: 55px; text-align: right; color: #333; flex-shrink: 0; margin-left: 6px;">${point.line}</span>`
    html += `<span style="margin-left: 10px; color: #000; word-wrap: break-word; white-space: pre-wrap; flex: 1;">${point.msg}</span>`
    html += '</div>'
  })

  html += '</div></div>'
  return html
}

// 格式化选中点的tooltip
function formatSelectedPointsTooltip(currentData: any, color: string): string {
  const selectedPoints = store.selectedPoints
  
  // 计算时间跨度
  const times = selectedPoints.map(p => p.value[0])
  const minTime = Math.min(...times)
  const maxTime = Math.max(...times)
  const diffMs = maxTime - minTime
  let timeSpanStr = ''
  if (diffMs < 1000) {
    timeSpanStr = `${diffMs.toFixed(0)}ms`
  } else if (diffMs < 60000) {
    timeSpanStr = `${(diffMs / 1000).toFixed(2)}s`
  } else {
    const mins = Math.floor(diffMs / 60000)
    const secs = ((diffMs % 60000) / 1000).toFixed(1)
    timeSpanStr = `${mins}m ${secs}s`
  }

  // 按时间排序
  const sortedPoints = [...selectedPoints].sort((a, b) => a.value[0] - b.value[0])

  const fontStyle = "font-family: Consolas, Monaco, 'Courier New', monospace; -webkit-font-smoothing: antialiased; font-weight: 500;"
  let html = `<div id="tooltip-scroll-container" style="padding: 10px; max-width: 550px; max-height: 40vh; overflow-y: auto; ${fontStyle}">`
  html += `<div style="font-weight: 700; font-size: 14px; margin-bottom: 6px; color: #667eea;">✅ 已选中 ${selectedPoints.length} 个点</div>`
  html += `<div style="font-size: 13px; color: #333; margin-bottom: 8px;">时间跨度: ${timeSpanStr} (${formatTime(minTime)} - ${formatTime(maxTime)})</div>`
  html += '<div style="font-size: 13px; line-height: 1.5;">'

  sortedPoints.forEach((point) => {
    const layerColor = getLayerColor(point.layer)
    const isCurrentPoint = (point.value[0] === currentData.value[0] && point.line === currentData.line)
    const bgColor = isCurrentPoint ? '#e7f1ff' : 'transparent'
    
    html += `<div style="display: flex; padding: 5px 6px; background: ${bgColor}; border-radius: 3px; margin: 3px 0; align-items: flex-start;">`
    html += `<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${layerColor}; margin-top: 5px; flex-shrink: 0;"></span>`
    html += `<span style="width: 32px; text-align: right; color: #111; flex-shrink: 0; margin-left: 6px; font-weight: 600;">L${point.layer}</span>`
    html += `<span style="width: 55px; text-align: right; color: #333; flex-shrink: 0; margin-left: 6px;">${point.line}</span>`
    html += `<span style="margin-left: 10px; color: #000; word-wrap: break-word; white-space: pre-wrap; flex: 1;">${point.msg}</span>`
    html += '</div>'
  })

  html += '</div></div>'
  return html
}

// 绑定图表事件
function bindChartEvents() {
  if (!chart) return

  // 双击添加标注
  chart.on('dblclick', (params: any) => {
    if (params.componentType === 'series' && params.data) {
      emit('dblclick', params.data)
    }
  })

  // 鼠标悬停绘制连接线
  chart.on('mouseover', (params: any) => {
    if (params.componentType === 'series' && params.data) {
      drawConnectionLines(params.data)
    }
  })

  chart.on('mouseout', (params: any) => {
    if (params.componentType === 'series') {
      clearConnectionLines()
    }
  })

  // 缩放时清除连接线并更新时间范围
  chart.on('dataZoom', () => {
    clearConnectionLines()
    updateTimeRange()
    renderAnnotations()
    // 清除套索画布上的残留
    if (lassoCtx && lassoCanvas.value) {
      lassoCtx.clearRect(0, 0, lassoCanvas.value.width, lassoCanvas.value.height)
    }
  })

  // VLine 模式点击
  chart.getZr().on('click', (params: any) => {
    if (!store.isVlineMode) return

    const pointInPixel = [params.offsetX, params.offsetY]
    if (chart?.containPixel('grid', pointInPixel)) {
      const dataPoint = chart.convertFromPixel({ xAxisIndex: 0, yAxisIndex: 0 }, pointInPixel)
      const xValue = dataPoint[0]

      if (typeof xValue === 'number' && !isNaN(xValue)) {
        store.isVlineMode = false
        emit('vlineClick', xValue)
      }
    }
  })
}

// 绘制连接线
function drawConnectionLines(data: SeriesDataPoint) {
  if (!chart || !connectionSvg.value) return

  const hoveredLayer = data.layer
  const hoveredClassname = data.classname
  const hoveredSubclass = data.subclassname
  const hoveredLine = data.line

  const layerKey = `${hoveredClassname}|${hoveredSubclass}|${hoveredLayer}`
  const layerPoints = pointsByCategoryLayer[layerKey] || []

  // 清除旧线条
  connectionSvg.value.innerHTML = ''

  const visibleData = store.getVisibleSeries()
  const yAxisData = visibleData?.filteredCategories || []

  // 1. 绘制同一分类同一层级的水平连接线
  if (layerPoints.length >= 2) {
    const sortedPoints = [...layerPoints].sort((a, b) => a.x - b.x)
    const color = getLayerColor(hoveredLayer)

    for (let i = 0; i < sortedPoints.length - 1; i++) {
      const p1 = sortedPoints[i]
      const p2 = sortedPoints[i + 1]

      const yCategory1 = yAxisData[p1.y]
      const yCategory2 = yAxisData[p2.y]

      const pixel1 = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [p1.x, yCategory1])
      const pixel2 = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [p2.x, yCategory2])

      if (pixel1 && pixel2 && !isNaN(pixel1[0]) && !isNaN(pixel1[1]) &&
          !isNaN(pixel2[0]) && !isNaN(pixel2[1])) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
        line.setAttribute('x1', String(pixel1[0]))
        line.setAttribute('y1', String(pixel1[1]))
        line.setAttribute('x2', String(pixel2[0]))
        line.setAttribute('y2', String(pixel2[1]))
        line.setAttribute('stroke', color)
        line.setAttribute('stroke-width', '3')
        line.setAttribute('stroke-dasharray', '8,4')
        line.setAttribute('stroke-linecap', 'round')
        connectionSvg.value.appendChild(line)
      }
    }
  }

  // 2. 查找不同分类中相同行号的点，用竖线连接
  const sameLinePoints: { x: number; y: number; category: string; pixel?: number[] }[] = []
  
  // 遍历所有可见分类，找相同行号的点
  for (const category of yAxisData) {
    const points = pointsByCategory[category] || []
    for (const point of points) {
      if (point.line === hoveredLine) {
        const yIndex = yAxisData.indexOf(category)
        if (yIndex >= 0) {
          const pixel = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [point.x, category])
          if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {
            sameLinePoints.push({
              x: point.x,
              y: yIndex,
              category,
              pixel: [pixel[0], pixel[1]]
            })
          }
        }
      }
    }
  }

  // 如果有多个不同分类的点有相同行号，绘制竖线连接
  if (sameLinePoints.length > 1) {
    // 按 Y 坐标排序
    sameLinePoints.sort((a, b) => a.y - b.y)

    // 绘制相邻点之间的竖线
    for (let i = 0; i < sameLinePoints.length - 1; i++) {
      const p1 = sameLinePoints[i]
      const p2 = sameLinePoints[i + 1]

      if (p1.pixel && p2.pixel) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
        line.setAttribute('x1', String(p1.pixel[0]))
        line.setAttribute('y1', String(p1.pixel[1]))
        line.setAttribute('x2', String(p2.pixel[0]))
        line.setAttribute('y2', String(p2.pixel[1]))
        line.setAttribute('stroke', '#ff6b6b')
        line.setAttribute('stroke-width', '2')
        line.setAttribute('stroke-dasharray', '4,2')
        line.setAttribute('stroke-linecap', 'round')
        line.setAttribute('opacity', '0.8')
        connectionSvg.value.appendChild(line)

        // 在连接线中点添加行号标签
        if (i === 0) {
          const midX = (p1.pixel[0] + p2.pixel[0]) / 2
          const midY = (p1.pixel[1] + p2.pixel[1]) / 2
          
          const text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
          text.setAttribute('x', String(midX + 8))
          text.setAttribute('y', String(midY))
          text.setAttribute('fill', '#ff6b6b')
          text.setAttribute('font-size', '10')
          text.setAttribute('font-weight', 'bold')
          text.textContent = `L${hoveredLine}`
          connectionSvg.value.appendChild(text)
        }
      }
    }
  }
}

// 清除连接线
function clearConnectionLines() {
  if (connectionSvg.value) {
    connectionSvg.value.innerHTML = ''
  }
}

// 更新时间范围
function updateTimeRange() {
  if (!chart) return

  try {
    const option = chart.getOption() as any
    const dataZoomOption = option.dataZoom?.[0]
    if (dataZoomOption) {
      store.viewTimeRange = {
        start: dataZoomOption.start,
        end: dataZoomOption.end
      }
    }
  } catch (e) {
    console.warn('Failed to update time range:', e)
  }
}

// 更新图表高度
function updateChartHeight() {
  if (!chartDom.value || !store.chartData) return

  const visibleData = store.getVisibleSeries()
  const categoryCount = visibleData?.filteredCategories.length || 0
  const height = Math.max(400, categoryCount * 60 + 200)

  chartDom.value.style.height = `${height}px`
  chart?.resize()
}

// 渲染标注
function renderAnnotations() {
  if (!chart || !store.chartData) return

  const elements: any[] = []
  const visibleData = store.getVisibleSeries()
  const yAxisData = visibleData?.filteredCategories || []

  // 渲染选中点的高亮圈
  if (store.selectedPoints.length > 0) {
    for (const point of store.selectedPoints) {
      const yCategory = yAxisData[point.value[1]]
      if (!yCategory) continue
      
      const pixel = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [point.value[0], yCategory])
      
      if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {
        // 选中点外圈高亮
        elements.push({
          type: 'circle',
          shape: {
            cx: pixel[0],
            cy: pixel[1],
            r: 12
          },
          style: {
            fill: 'rgba(102, 126, 234, 0.2)',
            stroke: '#667eea',
            lineWidth: 2
          },
          z: 80,
          silent: true
        })
      }
    }
  }

  // 渲染点标注
  if (store.showAnnotations && Object.keys(store.annotations).length > 0) {
    for (const [key, ann] of Object.entries(store.annotations)) {
      if (!store.visibleSubclasses.has(ann.yCategory)) continue

      const pixel = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [ann.x, ann.yCategory])

      if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {
        const text = ann.text.length > 15 ? ann.text.substring(0, 15) + '…' : ann.text
        const color = ann.color || '#667eea'
        const textWidth = Math.max(text.length * 7 + 16, 40)

        // 标签背景
        elements.push({
          type: 'rect',
          shape: {
            x: pixel[0] - textWidth / 2,
            y: pixel[1] - 28,
            width: textWidth,
            height: 20,
            r: 3
          },
          style: {
            fill: color,
            shadowBlur: 3,
            shadowOffsetY: 1,
            shadowColor: 'rgba(0,0,0,0.15)'
          },
          z: 100,
          silent: false,
          onclick: () => emit('annotationClick', key)
        })

        // 标签文字
        elements.push({
          type: 'text',
          style: {
            text,
            x: pixel[0],
            y: pixel[1] - 18,
            textAlign: 'center',
            textVerticalAlign: 'middle',
            fill: '#fff',
            fontSize: 11
          },
          z: 101,
          silent: true
        })
      }
    }
  }

  // 渲染垂直线
  if (store.showAnnotations && Object.keys(store.vlines).length > 0) {
    try {
      const gridModel = (chart as any).getModel().getComponent('grid')
      if (gridModel && gridModel.coordinateSystem) {
        const gridInfo = gridModel.coordinateSystem.getRect()

        for (const [key, vline] of Object.entries(store.vlines)) {
          const pixel = chart.convertToPixel({ xAxisIndex: 0 }, vline.time)

          if (pixel === undefined || isNaN(pixel as number)) continue

          const labelText = vline.text || formatTime(vline.time)
          const color = vline.color || '#ff6b6b'

          // 垂直线
          elements.push({
            type: 'line',
            z: 50,
            shape: {
              x1: pixel,
              y1: gridInfo.y,
              x2: pixel,
              y2: gridInfo.y + gridInfo.height
            },
            style: {
              stroke: color,
              lineWidth: 2,
              lineDash: [5, 3]
            }
          })

          // 顶部标签
          elements.push({
            type: 'text',
            z: 51,
            x: pixel,
            y: gridInfo.y - 5,
            style: {
              text: labelText,
              fill: color,
              fontSize: 11,
              textAlign: 'center',
              textVerticalAlign: 'bottom',
              backgroundColor: 'rgba(255,255,255,0.9)',
              padding: [2, 4],
              borderRadius: 2
            },
            onclick: () => emit('annotationClick', key),
            cursor: 'pointer'
          })
        }
      }
    } catch (e) {
      console.warn('Failed to render vlines:', e)
    }
  }

  chart.setOption({
    graphic: {
      elements
    }
  }, { replaceMerge: ['graphic'] })
}

// 套索选择相关
function initLassoCanvas() {
  if (!lassoCanvas.value || !chartContainer.value) return

  const rect = chartContainer.value.getBoundingClientRect()
  lassoCanvas.value.width = rect.width
  lassoCanvas.value.height = rect.height
  lassoCtx = lassoCanvas.value.getContext('2d')

  // 绑定套索事件
  lassoCanvas.value.addEventListener('mousedown', onLassoMouseDown)
  lassoCanvas.value.addEventListener('mousemove', onLassoMouseMove)
  lassoCanvas.value.addEventListener('mouseup', onLassoMouseUp)
}

function onLassoMouseDown(e: MouseEvent) {
  if (!store.isLassoMode || !lassoCanvas.value || !lassoCtx) return

  const rect = lassoCanvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  isDrawing = true
  lassoPath = [[x, y]]

  lassoCtx.clearRect(0, 0, lassoCanvas.value.width, lassoCanvas.value.height)
  lassoCtx.beginPath()
  lassoCtx.moveTo(x, y)
  lassoCtx.strokeStyle = '#667eea'
  lassoCtx.lineWidth = 2
  lassoCtx.setLineDash([5, 5])
}

function onLassoMouseMove(e: MouseEvent) {
  if (!store.isLassoMode || !isDrawing || !lassoCanvas.value || !lassoCtx) return

  const rect = lassoCanvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  lassoPath.push([x, y])

  // 重绘路径
  lassoCtx.clearRect(0, 0, lassoCanvas.value.width, lassoCanvas.value.height)
  lassoCtx.beginPath()
  lassoCtx.moveTo(lassoPath[0][0], lassoPath[0][1])
  for (let i = 1; i < lassoPath.length; i++) {
    lassoCtx.lineTo(lassoPath[i][0], lassoPath[i][1])
  }
  lassoCtx.stroke()

  // 填充半透明区域
  lassoCtx.fillStyle = 'rgba(102, 126, 234, 0.1)'
  lassoCtx.fill()
}

function onLassoMouseUp() {
  if (!store.isLassoMode || !isDrawing || !lassoCanvas.value || !lassoCtx || !chart) return
  isDrawing = false

  // 禁用 canvas 事件，恢复图表交互
  lassoCanvas.value.style.pointerEvents = 'none'

  if (lassoPath.length < 3) {
    lassoCtx.clearRect(0, 0, lassoCanvas.value.width, lassoCanvas.value.height)
    return
  }

  // 闭合路径
  lassoPath.push(lassoPath[0])

  // 查找选中的点
  const newSelected: any[] = []
  const visibleData = store.getVisibleSeries()
  const yAxisData = visibleData?.filteredCategories || []

  for (const series of store.chartData?.series || []) {
    for (const point of series.data) {
      const yCategory = yAxisData[point.value[1]]
      const pixel = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [point.value[0], yCategory])

      if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {
        if (isPointInPolygon([pixel[0], pixel[1]], lassoPath)) {
          newSelected.push(point)
        }
      }
    }
  }

  // 叠加到已选中的点（去重）
  const existingKeys = new Set(
    store.selectedPoints.map(p => `${p.value[0]}|${p.line}|${p.subclassname}`)
  )
  const combined = [...store.selectedPoints]
  for (const point of newSelected) {
    const key = `${point.value[0]}|${point.line}|${point.subclassname}`
    if (!existingKeys.has(key)) {
      combined.push(point)
      existingKeys.add(key)
    }
  }
  store.selectedPoints = combined

  // 清除套索画布
  lassoCtx.clearRect(0, 0, lassoCanvas.value.width, lassoCanvas.value.height)

  // 退出套索模式
  store.isLassoMode = false
}

// 更新图表
function updateChart() {
  if (!chart || !store.chartData) return

  const visibleData = store.getVisibleSeries()
  if (!visibleData) return

  const { filteredCategories, series } = visibleData

  // 计算区域标记
  const markAreaData = calculateMarkAreaData(filteredCategories)
  if (markAreaData.length > 0) {
    series.unshift({
      name: '_markArea',
      type: 'scatter',
      data: [],
      markArea: {
        silent: true,
        data: markAreaData
      }
    } as any)
  }

  // 更新高度
  updateChartHeight()

  // 应用新配置
  chart.setOption({
    yAxis: {
      data: filteredCategories
    },
    series
  }, { replaceMerge: ['series'] })

  // 清除连接线
  clearConnectionLines()

  // 重新渲染标注
  setTimeout(renderAnnotations, 100)
}

// 重置视图
function resetView() {
  if (!chart) return
  chart.dispatchAction({
    type: 'dataZoom',
    start: 0,
    end: 100
  })
}

// 监听可见性变化
watch(() => [...store.visibleSubclasses], () => {
  updateChart()
}, { deep: true })

// 监听标注变化 - 使用浅监听因为 store 中已经使用新对象赋值
watch(
  [() => store.annotations, () => store.vlines, () => store.showAnnotations],
  () => {
    nextTick(() => renderAnnotations())
  },
  { deep: false }
)

// 监听选中点变化，更新高亮显示
watch(() => store.selectedPoints, () => {
  nextTick(() => renderAnnotations())
}, { deep: true })

// 监听套索模式
watch(() => store.isLassoMode, (isLasso) => {
  if (lassoCanvas.value) {
    lassoCanvas.value.style.pointerEvents = isLasso ? 'auto' : 'none'
  }
  if (chartDom.value) {
    chartDom.value.style.cursor = isLasso ? 'crosshair' : (store.isVlineMode ? 'crosshair' : 'default')
  }

  if (chart) {
    chart.setOption({
      dataZoom: [
        { id: 'dataZoomX', zoomLock: isLasso },
        { id: 'dataZoomY', zoomLock: isLasso }
      ]
    })
  }
})

// 监听 VLine 模式
watch(() => store.isVlineMode, (isVline) => {
  if (chartDom.value) {
    chartDom.value.style.cursor = isVline ? 'crosshair' : (store.isLassoMode ? 'crosshair' : 'default')
  }
})

// 监听数据变化
watch(() => store.chartData, () => {
  nextTick(() => {
    if (chart) {
      chart.dispose()
    }
    initChart()
    setTimeout(renderAnnotations, 200)
  })
})

// 窗口大小变化 (带防抖)
const handleResize = debounce(() => {
  chart?.resize()
  clearConnectionLines()

  if (lassoCanvas.value && chartContainer.value) {
    const rect = chartContainer.value.getBoundingClientRect()
    lassoCanvas.value.width = rect.width
    lassoCanvas.value.height = rect.height
  }

  if (store.showAnnotations) {
    renderAnnotations()
  }
}, 150)

// 暴露方法
defineExpose({
  resetView,
  updateChart,
  renderAnnotations
})

onMounted(() => {
  initChart()
  initLassoCanvas()
  window.addEventListener('resize', handleResize)

  // 初始渲染标注
  setTimeout(renderAnnotations, 200)
  setTimeout(updateTimeRange, 100)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  min-height: 600px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.chart-dom {
  width: 100%;
  height: calc(100vh - 180px);
  min-height: 600px;
}

.connection-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 50;
}

.lasso-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 60;
}

/* 选中点详情面板 */
.selection-panel {
  position: fixed;
  width: calc(100vw - 300px);
  max-width: 1600px;
  max-height: calc(100vh - 140px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.selection-header {
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  position: relative;
  cursor: move;
  user-select: none;
}

.selection-title {
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-title .icon {
  font-size: 18px;
}

.selection-title strong {
  font-size: 20px;
}

.selection-title .drag-hint {
  margin-left: auto;
  opacity: 0.6;
  font-size: 14px;
  letter-spacing: 2px;
}

.selection-meta {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.9;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selection-meta .time-span {
  font-weight: 600;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.selection-content {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.selection-item {
  padding: 4px 8px;
  margin-bottom: 2px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #667eea;
  font-size: 12px;
}

.selection-item:last-child {
  margin-bottom: 0;
}

.item-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
}

.line-num {
  color: #667eea;
  font-weight: 600;
  flex-shrink: 0;
}

.item-msg {
  color: #1a1a1a;
  font-weight: 400;
  letter-spacing: 0.3px;
}
</style>
