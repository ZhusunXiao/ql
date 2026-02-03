import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChartData, Annotation, VLine, RawData, ClassHierarchy, TimelinePoint, SeriesDataPoint } from '@/types'
import { processRawData, recalculateSeries } from '@/utils'

export const useTimelineStore = defineStore('timeline', () => {
  // 原始数据
  const rawData = ref<RawData | null>(null)
  const chartData = ref<ChartData | null>(null)
  const title = ref('Timeline Visualization')
  const fileName = ref('timeline')

  // 可见性状态
  const visibleSubclasses = ref<Set<string>>(new Set())

  // 标注和垂直线
  const annotations = ref<Record<string, Annotation>>({})
  const vlines = ref<Record<string, VLine>>({})
  const showAnnotations = ref(true)

  // 选择状态
  const selectedPoints = ref<TimelinePoint[]>([])
  const isLassoMode = ref(false)
  const isVlineMode = ref(false)

  // 当前视图时间范围
  const viewTimeRange = ref<{ start: number; end: number }>({ start: 0, end: 100 })

  // 计算属性
  const classHierarchy = computed<ClassHierarchy[]>(() => chartData.value?.classHierarchy || [])

  const pointCountByClass = computed<Record<string, number>>(() => {
    const counts: Record<string, number> = {}
    if (chartData.value) {
      for (const point of chartData.value.rawData) {
        counts[point.classname] = (counts[point.classname] || 0) + 1
      }
    }
    return counts
  })

  const pointCountByCategory = computed<Record<string, number>>(() => {
    const counts: Record<string, number> = {}
    if (chartData.value) {
      for (const point of chartData.value.rawData) {
        counts[point.category] = (counts[point.category] || 0) + 1
      }
    }
    return counts
  })

  // 方法
  function loadData(data: RawData) {
    rawData.value = data
    title.value = data.name || 'Timeline Visualization'
    chartData.value = processRawData(data)

    // 初始化所有子类为可见
    visibleSubclasses.value = new Set(chartData.value.yAxisData)
  }

  function setFileName(name: string) {
    fileName.value = name
    loadStoredData()
  }

  function toggleSubclass(category: string, visible: boolean) {
    if (visible) {
      visibleSubclasses.value.add(category)
    } else {
      visibleSubclasses.value.delete(category)
    }
  }

  function toggleAllSubclasses(classIndex: number) {
    const cls = classHierarchy.value[classIndex]
    if (!cls) return

    const allVisible = cls.subclasses.every(sub =>
      visibleSubclasses.value.has(sub.categoryLabel)
    )

    for (const sub of cls.subclasses) {
      if (allVisible) {
        visibleSubclasses.value.delete(sub.categoryLabel)
      } else {
        visibleSubclasses.value.add(sub.categoryLabel)
      }
    }
  }

  function selectAll() {
    if (chartData.value) {
      visibleSubclasses.value = new Set(chartData.value.yAxisData)
    }
  }

  function selectNone() {
    visibleSubclasses.value.clear()
  }

  function getVisibleSeries() {
    if (!chartData.value) return null

    return recalculateSeries(
      chartData.value.rawData,
      chartData.value.yAxisData,
      visibleSubclasses.value
    )
  }

  // 标注相关方法
  function getAnnotationKey(point: SeriesDataPoint): string {
    return `${point.classname}|${point.subclassname}|${point.value[0]}|${point.layer}`
  }

  function saveAnnotation(point: SeriesDataPoint, text: string, color: string) {
    if (!chartData.value) return

    const key = getAnnotationKey(point)
    if (text) {
      annotations.value[key] = {
        text,
        color,
        x: point.value[0],
        yCategory: chartData.value.yAxisData[point.value[1]],
        pointData: point,
        createdAt: new Date().toISOString()
      }
    } else {
      delete annotations.value[key]
    }
    saveStoredData()
  }

  function deleteAnnotation(point: SeriesDataPoint) {
    const key = getAnnotationKey(point)
    delete annotations.value[key]
    saveStoredData()
  }

  function getAnnotation(point: SeriesDataPoint): Annotation | null {
    const key = getAnnotationKey(point)
    return annotations.value[key] || null
  }

  // 垂直线相关方法
  function saveVline(time: number, text: string | null, color: string, existingKey?: string) {
    const key = existingKey || `vline_${time}`
    // 使用新对象赋值确保响应式触发
    vlines.value = {
      ...vlines.value,
      [key]: {
        time,
        text,
        color,
        createdAt: new Date().toISOString()
      }
    }
    saveStoredData()
  }

  function deleteVline(key: string) {
    const newVlines = { ...vlines.value }
    delete newVlines[key]
    vlines.value = newVlines
    saveStoredData()
  }

  // localStorage 操作
  function loadStoredData() {
    try {
      const annotationsKey = `timeline-annotations-${fileName.value}`
      const vlinesKey = `timeline-vlines-${fileName.value}`

      const storedAnnotations = localStorage.getItem(annotationsKey)
      if (storedAnnotations) {
        annotations.value = JSON.parse(storedAnnotations)
      }

      const storedVlines = localStorage.getItem(vlinesKey)
      if (storedVlines) {
        vlines.value = JSON.parse(storedVlines)
      }
    } catch (e) {
      console.warn('Failed to load stored data:', e)
    }
  }

  function saveStoredData() {
    try {
      const annotationsKey = `timeline-annotations-${fileName.value}`
      const vlinesKey = `timeline-vlines-${fileName.value}`

      localStorage.setItem(annotationsKey, JSON.stringify(annotations.value))
      localStorage.setItem(vlinesKey, JSON.stringify(vlines.value))
    } catch (e) {
      console.warn('Failed to save stored data:', e)
    }
  }

  function exportAnnotations(): string {
    const exportData = {
      fileName: fileName.value,
      exportTime: new Date().toISOString(),
      annotations: annotations.value,
      vlines: vlines.value
    }
    return JSON.stringify(exportData, null, 2)
  }

  function importAnnotations(jsonStr: string): { success: boolean; count: number; error?: string } {
    try {
      const imported = JSON.parse(jsonStr)
      let count = 0

      if (imported.annotations) {
        Object.assign(annotations.value, imported.annotations)
        count += Object.keys(imported.annotations).length
      }

      if (imported.vlines) {
        Object.assign(vlines.value, imported.vlines)
        count += Object.keys(imported.vlines).length
      }

      saveStoredData()
      return { success: true, count }
    } catch (e) {
      return { success: false, count: 0, error: (e as Error).message }
    }
  }

  function exportData(): string {
    if (!chartData.value) return '[]'
    return JSON.stringify(chartData.value.rawData, null, 2)
  }

  return {
    // 状态
    rawData,
    chartData,
    title,
    fileName,
    visibleSubclasses,
    annotations,
    vlines,
    showAnnotations,
    selectedPoints,
    isLassoMode,
    isVlineMode,
    viewTimeRange,

    // 计算属性
    classHierarchy,
    pointCountByClass,
    pointCountByCategory,

    // 方法
    loadData,
    setFileName,
    toggleSubclass,
    toggleAllSubclasses,
    selectAll,
    selectNone,
    getVisibleSeries,
    getAnnotationKey,
    saveAnnotation,
    deleteAnnotation,
    getAnnotation,
    saveVline,
    deleteVline,
    loadStoredData,
    saveStoredData,
    exportAnnotations,
    importAnnotations,
    exportData
  }
})
