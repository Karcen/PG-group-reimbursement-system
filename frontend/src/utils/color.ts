/**
 * 根据背景色亮度自动返回适合的文字颜色（黑或白）
 * 使用 WCAG 相对亮度公式，保证足够的对比度
 */
export function getTagTextColor(hexColor: string): string {
  const hex = hexColor.replace('#', '')
  if (hex.length !== 6) return '#ffffff'
  const r = parseInt(hex.slice(0, 2), 16)
  const g = parseInt(hex.slice(2, 4), 16)
  const b = parseInt(hex.slice(4, 6), 16)
  // 相对亮度（人眼对绿色最敏感）
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.55 ? '#333333' : '#ffffff'
}
