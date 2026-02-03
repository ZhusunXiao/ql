<template>
  <Teleport to="body">
    <div v-if="modelValue" class="overlay" @click="$emit('update:modelValue', false)"></div>
    <div v-if="modelValue" class="vline-panel">
      <h3>📍 添加垂直线</h3>
      <div class="time-info">
        <strong>时间:</strong> 
        <span style="color: #ff6b6b">{{ displayTime }}</span>
      </div>
      
      <div class="color-section">
        <label>线条颜色:</label>
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
      
      <div class="label-section">
        <label>标签 (可选，默认显示时间):</label>
      </div>
      <input 
        type="text" 
        v-model="labelText" 
        placeholder="留空则显示时间标签..."
        class="label-input"
      />
      
      <div class="btn-group">
        <button v-if="existingKey" class="btn-delete" @click="handleDelete">删除</button>
        <button class="btn-cancel" @click="$emit('update:modelValue', false)">取消</button>
        <button class="btn-save" @click="handleSave">保存</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTimelineStore } from '@/stores'
import { formatTime } from '@/utils'

const props = defineProps<{
  modelValue: boolean
  time: number | null
  existingKey: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useTimelineStore()

const labelText = ref('')
const selectedColor = ref('#ff6b6b')

const colorPresets = ['#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3', '#a29bfe']

const displayTime = computed(() => {
  if (props.time === null || isNaN(props.time)) return '未知'
  return formatTime(props.time)
})

// 当 time 或 existingKey 变化时，加载已有数据
watch([() => props.time, () => props.existingKey], ([_, key]) => {
  if (key && store.vlines[key]) {
    const vline = store.vlines[key]
    labelText.value = vline.text || ''
    selectedColor.value = vline.color || '#ff6b6b'
  } else {
    labelText.value = ''
    selectedColor.value = '#ff6b6b'
  }
}, { immediate: true })

function handleSave() {
  if (props.time === null) return
  store.saveVline(
    props.time,
    labelText.value.trim() || null,
    selectedColor.value,
    props.existingKey || undefined
  )
  emit('update:modelValue', false)
}

function handleDelete() {
  if (props.existingKey) {
    store.deleteVline(props.existingKey)
  }
  emit('update:modelValue', false)
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

.vline-panel {
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

.vline-panel h3 {
  margin-bottom: 15px;
  color: #667eea;
}

.time-info {
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

.label-section {
  margin-bottom: 10px;
}

.label-section label {
  font-size: 12px;
  color: #666;
}

.label-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-bottom: 10px;
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
