/**
 * 时间格式化工具函数
 */

/**
 * 时间戳转换为 HH:MM:SS.mmm 格式
 */
export function formatTime(ms: number): string {
  const date = new Date(ms)
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  const msStr = String(date.getMilliseconds()).padStart(3, '0')
  return `${h}:${m}:${s}.${msStr}`
}

/**
 * 时间戳转换为可读时间字符串
 */
export function timestampToStr(timestamp: number): string {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 持续时间格式化（自适应单位）
 */
export function formatDuration(ms: number): string {
  if (ms < 0) ms = Math.abs(ms)
  if (ms === 0) return '0ms'

  const units = [
    { name: 'd', value: 86400000 },
    { name: 'h', value: 3600000 },
    { name: 'm', value: 60000 },
    { name: 's', value: 1000 },
    { name: 'ms', value: 1 }
  ]

  const result: string[] = []
  let remaining = ms

  for (const unit of units) {
    if (remaining >= unit.value) {
      const count = Math.floor(remaining / unit.value)
      remaining = remaining % unit.value
      result.push(`${count}${unit.name}`)
      // 最多显示2个单位
      if (result.length >= 2) break
    }
  }

  return result.join('') || '0ms'
}
