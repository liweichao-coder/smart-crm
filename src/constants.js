// 业务枚举与中文标签（与后端语义保持一致）
export const LEAD_STAGES = [
  { value: 'new', label: '新建', color: 'default' },
  { value: 'qualified', label: '已确认', color: 'cyan' },
  { value: 'proposal', label: '方案', color: 'blue' },
  { value: 'negotiation', label: '商务谈判', color: 'gold' },
  { value: 'won', label: '赢单', color: 'green' },
  { value: 'lost', label: '丢单', color: 'red' },
]

export const ORDER_STATUS = [
  { value: 'draft', label: '草稿', color: 'default' },
  { value: 'confirmed', label: '已确认', color: 'blue' },
  { value: 'fulfilled', label: '已交付', color: 'green' },
]

export const CUSTOMER_STATUS = [
  { value: 'active', label: '活跃', color: 'green' },
  { value: 'nurturing', label: '培育中', color: 'blue' },
  { value: 'risk_watch', label: '风险关注', color: 'red' },
  { value: 'closed', label: '已关闭', color: 'default' },
]

export function labelOf(list, value) {
  return list.find((i) => i.value === value)?.label ?? value
}

export function colorOf(list, value) {
  return list.find((i) => i.value === value)?.color ?? 'default'
}

export function formatCurrency(value, currency = 'CNY') {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  const symbol = currency === 'CNY' ? '¥' : ''
  return symbol + Number(value).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}
