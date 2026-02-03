<template>
  <div class="app-container">
    <div v-if="isLoading" class="loading-screen">
      <div class="loading-card">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>
    </div>

    <div v-else-if="!isDataLoaded" class="welcome-screen">
      <div class="welcome-card">
        <h1>📊 Quick Log</h1>
        <p>日志时间线可视化工具</p>
        
        <div class="upload-section">
          <div 
            class="upload-area"
            :class="{ 'drag-over': isDragOver }"
            @dragover.prevent="isDragOver = true"
            @dragleave="isDragOver = false"
            @drop.prevent="handleFileDrop"
            @click="fileInput?.click()"
          >
            <span class="upload-icon">📁</span>
            <p>拖放 JSON 文件到这里</p>
            <p class="upload-hint">或点击选择文件</p>
          </div>
          <input 
            ref="fileInput"
            type="file" 
            accept=".json"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>

        <div class="demo-section">
          <p>或者加载示例数据:</p>
          <button class="demo-btn" @click="loadDemoData">🎯 加载示例</button>
        </div>
      </div>
    </div>

    <div v-else class="main-layout">
      <CategorySidebar />
      
      <div class="container">
        <div class="header">
          <h1>{{ store.title }}</h1>
          <p>日志时间线可视化 - ECharts</p>
        </div>
        
        <div class="content">
          <Toolbar @reset-view="chartRef?.resetView()" />
          <TimelineChart 
            ref="chartRef"
            @dblclick="handlePointDblClick"
            @vline-click="handleVlineClick"
            @annotation-click="handleAnnotationClick"
          />
        </div>
      </div>
    </div>

    <!-- 标注面板 -->
    <AnnotationPanel
      v-model="showAnnotationPanel"
      :point="currentAnnotationPoint"
      :is-editing="isEditingAnnotation"
    />

    <!-- 垂直线面板 -->
    <VLinePanel
      v-model="showVlinePanel"
      :time="currentVlineTime"
      :existing-key="currentVlineKey"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTimelineStore } from '@/stores'
import { CategorySidebar, Toolbar, TimelineChart, AnnotationPanel, VLinePanel } from '@/components'
import type { SeriesDataPoint, RawData } from '@/types'

const store = useTimelineStore()

const fileInput = ref<HTMLInputElement | null>(null)
const chartRef = ref<InstanceType<typeof TimelineChart> | null>(null)
const isDragOver = ref(false)
const isLoading = ref(false)

// 标注相关
const showAnnotationPanel = ref(false)
const currentAnnotationPoint = ref<SeriesDataPoint | null>(null)
const isEditingAnnotation = ref(false)

// 垂直线相关
const showVlinePanel = ref(false)
const currentVlineTime = ref<number | null>(null)
const currentVlineKey = ref<string | null>(null)

const isDataLoaded = computed(() => store.chartData !== null)

// 启动时检查 URL 参数或自动加载
onMounted(async () => {
  // 检查 URL 参数 ?file=xxx.json
  const urlParams = new URLSearchParams(window.location.search)
  const fileParam = urlParams.get('file')
  
  if (fileParam) {
    await loadFromUrl(fileParam)
  }
})

// 从 URL 加载 JSON 文件
async function loadFromUrl(url: string) {
  isLoading.value = true
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json() as RawData
    
    // 从 URL 提取文件名
    const fileName = url.split('/').pop()?.replace('.json', '') || 'timeline'
    
    store.loadData(data)
    store.setFileName(fileName)
  } catch (err) {
    console.error('加载失败:', err)
    alert('❌ 加载 JSON 文件失败: ' + (err as Error).message)
  } finally {
    isLoading.value = false
  }
}

// 处理文件选择
function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    loadFile(file)
  }
}

// 处理文件拖放
function handleFileDrop(event: DragEvent) {
  isDragOver.value = false
  const file = event.dataTransfer?.files[0]
  if (file && file.name.endsWith('.json')) {
    loadFile(file)
  }
}

// 加载文件
function loadFile(file: File) {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target?.result as string) as RawData
      store.loadData(data)
      store.setFileName(file.name.replace('.json', ''))
    } catch (err) {
      alert('❌ 文件解析失败: ' + (err as Error).message)
    }
  }
  reader.readAsText(file)
}

// 加载示例数据
async function loadDemoData() {
  // 生成示例数据
  const demoData = generateDemoData()
  store.loadData(demoData)
  store.setFileName('demo')
}

// 生成示例数据
function generateDemoData(): RawData {
  const baseTime = Date.now() - 60000 // 1分钟前开始
  const classes = [
    {
      classname: '系统启动',
      subclasses: [
        { subclassname: '初始化', count: 20 },
        { subclassname: '配置加载', count: 15 },
        { subclassname: '服务注册', count: 10 }
      ]
    },
    {
      classname: '网络通信',
      subclasses: [
        { subclassname: 'TCP连接', count: 25 },
        { subclassname: 'HTTP请求', count: 30 },
        { subclassname: '数据传输', count: 20 }
      ]
    },
    {
      classname: '数据处理',
      subclasses: [
        { subclassname: '数据解析', count: 15 },
        { subclassname: '数据转换', count: 12 },
        { subclassname: '数据存储', count: 18 }
      ]
    }
  ]

  const levels = ['I', 'D', 'W', 'E']

  return {
    name: '示例数据 - Quick Log Demo',
    all: classes.map(cls => ({
      classname: cls.classname,
      subclasses: cls.subclasses.map(sub => ({
        subclassname: sub.subclassname,
        points: Array.from({ length: sub.count }, (_, i) => ({
          cursor: `${cls.classname.charAt(0)}${sub.subclassname.charAt(0)}_${i}`,
          msg: `${levels[Math.floor(Math.random() * 4)]} ${cls.classname}: ${sub.subclassname} 操作 #${i} - 测试消息`,
          line: i + 1,
          timestamp: baseTime + Math.random() * 60000,
          layer: Math.floor(Math.random() * 3) + 1
        }))
      }))
    }))
  }
}

// 双击点添加标注
function handlePointDblClick(point: SeriesDataPoint) {
  currentAnnotationPoint.value = point
  isEditingAnnotation.value = !!store.getAnnotation(point)
  showAnnotationPanel.value = true
}

// 点击图表添加垂直线
function handleVlineClick(time: number) {
  currentVlineTime.value = time
  currentVlineKey.value = null
  showVlinePanel.value = true
}

// 点击标注
function handleAnnotationClick(key: string) {
  // 判断是点标注还是垂直线
  if (key.startsWith('vline_')) {
    const vline = store.vlines[key]
    if (vline) {
      currentVlineTime.value = vline.time
      currentVlineKey.value = key
      showVlinePanel.value = true
    }
  } else {
    const ann = store.annotations[key]
    if (ann) {
      currentAnnotationPoint.value = ann.pointData
      isEditingAnnotation.value = true
      showAnnotationPanel.value = true
    }
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

/* 欢迎页面 */
.welcome-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 40px);
}

.welcome-card {
  background: white;
  border-radius: 20px;
  padding: 40px 60px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.welcome-card h1 {
  font-size: 2.5em;
  color: #667eea;
  margin-bottom: 10px;
}

.welcome-card > p {
  color: #666;
  margin-bottom: 30px;
}

.upload-section {
  margin-bottom: 30px;
}

.upload-area {
  border: 3px dashed #667eea;
  border-radius: 15px;
  padding: 40px;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover,
.upload-area.drag-over {
  background: #f8f9ff;
  border-color: #764ba2;
}

.upload-icon {
  font-size: 3em;
  display: block;
  margin-bottom: 15px;
}

.upload-area p {
  color: #667eea;
  font-size: 1.1em;
  margin: 5px 0;
}

.upload-hint {
  color: #999 !important;
  font-size: 0.9em !important;
}

.demo-section {
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.demo-section p {
  color: #666;
  margin-bottom: 15px;
}

.demo-btn {
  padding: 12px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.demo-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* 加载页面 */
.loading-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 40px);
}

.loading-card {
  background: white;
  border-radius: 20px;
  padding: 40px 60px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-card p {
  color: #667eea;
  font-size: 1.1em;
}

/* 主布局 */
.main-layout {
  display: flex;
  gap: 20px;
  max-width: 2000px;
  margin: 0 auto;
}

.container {
  flex: 1;
  min-width: 0;
  background: white;
  border-radius: 15px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  text-align: center;
}

.header h1 {
  font-size: 2.5em;
  margin-bottom: 10px;
}

.content {
  padding: 30px;
}
</style>
