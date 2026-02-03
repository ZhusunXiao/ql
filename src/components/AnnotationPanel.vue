<template>
  <Teleport to="body">
    <div v-if="modelValue" class="overlay" @click="$emit('update:modelValue', false)"></div>
    <div v-if="modelValue" class="annotation-panel">
      <h3>📝 添加标注</h3>
      <div class="point-info" v-html="pointInfoHtml"></div>
      
      <div class="color-section">
        <label>标签颜色:</label>
        <input type="color" v-model="selectedColor" />
        <span class="color-presets">
          <span 
            v-for="color in colorPresets" 
            :key="color"
            class="color-preset"
            :style="{ background: color }"
            @click="selectedColor = color"
          ></span>
        </span>
      </div>
      
      <div class="quick-fill">
        <span>快速填充:</span>
        <button @click="fillAndSave('cursor')">🎯 Cursor</button>
        <button @click="fillAndSave('msg')">💬 Msg</button>
      </div>
      
      <textarea 
        v-model="annotationText" 
        placeholder="输入标注内容..."
      ></textarea>
      
      <div class="btn-group">
        <button v-if="isEditing" class="btn-delete" @click="handleDelete">删除</button>
        <button class="btn-cancel" @click="$emit('update:modelValue', false)">取消</button>
        <button class="btn-save" @click="handleSave">保存</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTimelineStore } from '@/stores'
import { formatTime, getLayerColor } from '@/utils'
import type { SeriesDataPoint } from '@/types'

const props = defineProps<{
  modelValue: boolean
  point: SeriesDataPoint | null
  isEditing: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useTimelineStore()

const annotationText = ref('')
const selectedColor = ref('#667eea')

const colorPresets = ['#667eea', '#28a745', '#dc3545', '#ffc107', '#17a2b8']

const pointInfoHtml = computed(() => {
  if (!props.point) return ''
  const pointColor = getLayerColor(props.point.layer)
  return `<strong>${props.point.classname}</strong> / ${props.point.subclassname}<br>
          <span style="color:${pointColor}">${formatTime(props.point.value[0])}</span> - Layer ${props.point.layer}`
})

// 当 point 变化时，加载已有标注
watch(() => props.point, (newPoint) => {
  if (newPoint) {
    const existing = store.getAnnotation(newPoint)
    if (existing) {
      annotationText.value = existing.text
      selectedColor.value = existing.color || getLayerColor(newPoint.layer)
    } else {
      annotationText.value = ''
      selectedColor.value = getLayerColor(newPoint.layer)
    }
  }
}, { immediate: true })

function handleSave() {
  if (!props.point) return
  store.saveAnnotation(props.point, annotationText.value.trim(), selectedColor.value)
  emit('update:modelValue', false)
}

function handleDelete() {
  if (!props.point) return
  store.deleteAnnotation(props.point)
  emit('update:modelValue', false)
}

function fillAndSave(field: 'cursor' | 'msg') {
  if (!props.point) return
  const text = field === 'cursor' ? props.point.cursor : props.point.msg
  if (text) {
    store.saveAnnotation(props.point, text, selectedColor.value)
    emit('update:modelValue', false)
  }
}
</script>

<style scoped>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 19999;
}

.annotation-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 20px;
  z-index: 20000;
  min-width: 350px;
}

.annotation-panel h3 {
  margin-bottom: 15px;
  color: #667eea;
}

.point-info {
  margin-bottom: 10px;
  font-size: 12px;
  color: #666;
}

.color-section {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-section label {
  font-size: 12px;
  color: #666;
}

.color-section input[type="color"] {
  width: 60px;
  height: 28px;
  border: none;
  cursor: pointer;
}

.color-presets {
  display: flex;
  gap: 5px;
}

.color-preset {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 3px;
  cursor: pointer;
  vertical-align: middle;
}

.color-preset:hover {
  transform: scale(1.1);
}

.quick-fill {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.quick-fill span {
  font-size: 12px;
  color: #666;
}

.quick-fill button {
  padding: 4px 10px;
  font-size: 11px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.quick-fill button:hover {
  background: #5a6268;
}

.annotation-panel textarea {
  width: 100%;
  height: 100px;
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 10px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}

.btn-group {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-group button {
  padding: 8px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.btn-save {
  background: #667eea;
  color: white;
}

.btn-save:hover {
  background: #5568d3;
}

.btn-cancel {
  background: #6c757d;
  color: white;
}

.btn-cancel:hover {
  background: #5a6268;
}

.btn-delete {
  background: #dc3545;
  color: white;
}

.btn-delete:hover {
  background: #c82333;
}
</style>
