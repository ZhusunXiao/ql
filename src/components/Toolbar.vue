<template>
  <div class="toolbar">
    <div class="toolbar-group">
      <span class="toolbar-label">⌚ 时间范围:</span>
      <span class="time-range-display">{{ timeRangeText }}</span>
    </div>
    <div class="toolbar-group">
      <span class="toolbar-label">📌 标注 (双击添加):</span>
      <button 
        class="toolbar-btn" 
        :class="{ active: store.showAnnotations }"
        @click="store.showAnnotations = !store.showAnnotations"
      >
        👁 {{ store.showAnnotations ? '隐藏' : '显示' }}标注
      </button>
      <button 
        class="toolbar-btn" 
        :class="{ active: store.isVlineMode }"
        @click="toggleVlineMode"
      >
        📍 {{ store.isVlineMode ? '点击图表...' : '添加垂直线' }}
      </button>
      <button class="toolbar-btn" @click="handleExportAnnotations">💾 导出</button>
      <button class="toolbar-btn" @click="handleImportAnnotations">📂 导入</button>
    </div>
    <div class="toolbar-group">
      <span class="toolbar-label">✂️ 选择:</span>
      <button 
        class="toolbar-btn" 
        :class="{ active: store.isLassoMode }"
        @click="toggleLassoMode"
      >
        ⭕ 框选
      </button>
      <button 
        v-show="store.selectedPoints.length > 0" 
        class="toolbar-btn danger"
        @click="clearSelection"
      >
        ✖ 清除选择
      </button>
      <button class="toolbar-btn" @click="$emit('resetView')">🔄 重置视图</button>
      <button class="toolbar-btn" @click="handleExportData">💾 导出数据</button>
    </div>
  </div>

  <!-- 隐藏的文件输入 -->
  <input 
    ref="importFileInput" 
    type="file" 
    accept=".json" 
    style="display: none"
    @change="handleFileImport"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTimelineStore } from '@/stores'
import { formatTime, formatDuration } from '@/utils'

const emit = defineEmits<{
  resetView: []
}>()

const store = useTimelineStore()
const importFileInput = ref<HTMLInputElement | null>(null)

const timeRangeText = computed(() => {
  if (!store.chartData) return '加载中...'

  const { minTime, maxTime } = store.chartData
  const timeRange = maxTime - minTime
  const startPercent = store.viewTimeRange.start / 100
  const endPercent = store.viewTimeRange.end / 100

  const viewStart = minTime + timeRange * startPercent
  const viewEnd = minTime + timeRange * endPercent
  const duration = viewEnd - viewStart

  return `${formatTime(viewStart)} ~ ${formatTime(viewEnd)} (时长: ${formatDuration(duration)})`
})

function toggleVlineMode() {
  store.isVlineMode = !store.isVlineMode
  if (store.isVlineMode) {
    store.isLassoMode = false
  }
}

function toggleLassoMode() {
  store.isLassoMode = !store.isLassoMode
  if (store.isLassoMode) {
    store.isVlineMode = false
  }
}

function clearSelection() {
  store.selectedPoints = []
  store.isLassoMode = false
}

function handleExportAnnotations() {
  const dataStr = store.exportAnnotations()
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `annotations-${store.fileName}-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function handleImportAnnotations() {
  importFileInput.value?.click()
}

function handleFileImport(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const result = store.importAnnotations(e.target?.result as string)
    if (result.success) {
      alert(`✅ 成功导入 ${result.count} 个项目`)
    } else {
      alert(`❌ 导入失败: ${result.error}`)
    }
  }
  reader.readAsText(file)
  
  // 清除以允许重新选择
  ;(event.target as HTMLInputElement).value = ''
}

function handleExportData() {
  const dataStr = store.exportData()
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `timeline-data-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.toolbar-group {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 0 10px;
  border-right: 1px solid #ddd;
}

.toolbar-group:last-child {
  border-right: none;
}

.toolbar-label {
  font-size: 0.9em;
  color: #666;
  margin-right: 5px;
}

.toolbar-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.3s;
}

.toolbar-btn:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.toolbar-btn.active {
  background: #28a745;
}

.toolbar-btn.danger {
  background: #dc3545;
}

.toolbar-btn.danger:hover {
  background: #c82333;
}

.time-range-display {
  padding: 8px 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 5px;
  font-size: 0.9em;
  font-weight: bold;
}
</style>
