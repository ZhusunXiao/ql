<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h3>📂 分类</h3>
      <p>勾选以显示/隐藏</p>
    </div>
    <div class="sidebar-actions">
      <button class="btn-select-all" @click="store.selectAll()">✓ 全选</button>
      <button class="btn-select-none" @click="store.selectNone()">✗ 全不选</button>
    </div>
    <div class="sidebar-content">
      <div 
        v-for="(cls, classIndex) in store.classHierarchy" 
        :key="classIndex" 
        class="class-group"
      >
        <div 
          class="class-header" 
          :class="{ collapsed: collapsedClasses.has(classIndex) }"
          :style="{ background: getClassColor(classIndex) }"
          @click="toggleCollapse(classIndex)"
        >
          <span class="toggle-icon">▼</span>
          <span style="flex: 1">{{ cls.classname }}</span>
          <span 
            class="class-visibility-toggle" 
            :title="isAllVisible(classIndex) ? '隐藏所有子类' : '显示所有子类'"
            @click.stop="store.toggleAllSubclasses(classIndex)"
          >
            {{ isAllVisible(classIndex) ? '✓' : '✗' }}
          </span>
          <span class="point-count">{{ store.pointCountByClass[cls.classname] || 0 }}</span>
        </div>
        <div 
          class="subclass-list" 
          :class="{ collapsed: collapsedClasses.has(classIndex) }"
        >
          <div 
            v-for="(sub, subIndex) in cls.subclasses" 
            :key="subIndex" 
            class="subclass-item"
            :style="{ borderLeft: `3px solid ${getClassColor(classIndex)}` }"
          >
            <input 
              type="checkbox" 
              :id="`check_${classIndex}_${subIndex}`"
              :checked="store.visibleSubclasses.has(sub.categoryLabel)"
              @change="store.toggleSubclass(sub.categoryLabel, ($event.target as HTMLInputElement).checked)"
            />
            <label :for="`check_${classIndex}_${subIndex}`">{{ sub.subclassname }}</label>
            <span class="point-count">{{ store.pointCountByCategory[sub.categoryLabel] || 0 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTimelineStore } from '@/stores'
import { getClassColor } from '@/utils'

const store = useTimelineStore()
const collapsedClasses = ref<Set<number>>(new Set())

function toggleCollapse(classIndex: number) {
  if (collapsedClasses.value.has(classIndex)) {
    collapsedClasses.value.delete(classIndex)
  } else {
    collapsedClasses.value.add(classIndex)
  }
}

function isAllVisible(classIndex: number): boolean {
  const cls = store.classHierarchy[classIndex]
  if (!cls) return false
  return cls.subclasses.every(sub => store.visibleSubclasses.has(sub.categoryLabel))
}
</script>

<style scoped>
.sidebar {
  width: 320px;
  flex-shrink: 0;
  background: white;
  border-radius: 15px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
}

.sidebar-header h3 {
  font-size: 1.2em;
  margin-bottom: 5px;
}

.sidebar-header p {
  font-size: 0.85em;
  opacity: 0.9;
}

.sidebar-actions {
  padding: 10px 15px;
  border-bottom: 1px solid #eee;
  display: flex;
  gap: 8px;
}

.sidebar-actions button {
  flex: 1;
  padding: 8px 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.8em;
  transition: all 0.3s;
}

.btn-select-all {
  background: #667eea;
  color: white;
}

.btn-select-all:hover {
  background: #5568d3;
}

.btn-select-none {
  background: #dc3545;
  color: white;
}

.btn-select-none:hover {
  background: #c82333;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.class-group {
  margin-bottom: 15px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.class-header {
  padding: 12px 15px;
  font-weight: bold;
  font-size: 0.95em;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.3s;
}

.class-header:hover {
  filter: brightness(0.95);
}

.class-header .toggle-icon {
  transition: transform 0.3s;
}

.class-header.collapsed .toggle-icon {
  transform: rotate(-90deg);
}

.class-visibility-toggle {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  font-size: 0.85em;
  cursor: pointer;
  transition: all 0.2s;
}

.class-visibility-toggle:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.subclass-list {
  overflow-y: auto;
  transition: max-height 0.3s ease-out;
  max-height: 500px;
}

.subclass-list.collapsed {
  max-height: 0;
  overflow: hidden;
}

.subclass-item {
  padding: 10px 15px 10px 25px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-top: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.subclass-item:hover {
  background: #f8f9fa;
}

.subclass-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.subclass-item label {
  flex: 1;
  cursor: pointer;
  font-size: 0.85em;
  color: #333;
  word-break: break-word;
}

.point-count {
  font-size: 0.75em;
  background: #e9ecef;
  padding: 2px 8px;
  border-radius: 10px;
  color: #666;
}
</style>
