/**
 * 颜色相关工具函数
 */

// Layer 颜色调色板
export const LAYER_COLOR_PALETTE = [
  '#667eea', // 紫蓝
  '#28a745', // 绿色
  '#ffc107', // 黄色
  '#dc3545', // 红色
  '#17a2b8', // 青色
  '#fd7e14', // 橙色
  '#6f42c1', // 紫色
  '#20c997', // 蓝绿
  '#e83e8c', // 粉色
  '#007bff', // 蓝色
  '#6610f2', // 靛蓝
  '#795548', // 棕色
  '#607d8b', // 蓝灰
  '#4caf50', // 浅绿
  '#ff5722', // 深橙
  '#9c27b0', // 深紫
  '#00bcd4', // 浅青
  '#8bc34a', // 青柠
  '#ff9800', // 琥珀
  '#3f51b5'  // 靛青蓝
]

// 主类颜色（用于区分不同主类区域）
export const CLASS_COLORS = [
  '#e3f2fd', '#f3e5f5', '#e8f5e9', '#fff3e0', '#fce4ec',
  '#e0f7fa', '#f1f8e9', '#ede7f6', '#fff8e1', '#e1f5fe'
]

/**
 * 获取 Layer 颜色
 */
export function getLayerColor(layer: number): string {
  return LAYER_COLOR_PALETTE[(layer - 1) % LAYER_COLOR_PALETTE.length]
}

/**
 * 获取 Layer 显示名称
 */
export function getLayerName(layer: number): string {
  return `Layer ${layer}`
}

/**
 * 获取主类颜色
 */
export function getClassColor(index: number): string {
  return CLASS_COLORS[index % CLASS_COLORS.length]
}
