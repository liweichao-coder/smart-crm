const fallbackTextByKey = {
  account: '新客户',
  closeDate: '2026-06-01',
  company: '新公司',
  description: '补充任务说明',
  dueDate: '今天 18:00',
  email: 'new-contact@example.com',
  industry: '待补充',
  name: '新建记录',
  nextStep: '补充跟进计划',
  note: '持续跟踪并更新进度',
  owner: '未分配',
  period: '2026 Q3',
  priority: 'warm',
  role: '待确认',
  status: 'active',
  statusLabel: '本周',
  title: '新建事项',
}

const numericDefaults = {
  amount: 0,
  revenue: 0,
}

export function createDraftFromColumns(columns, workflowField) {
  return columns.reduce((draft, column) => {
    const key = column.key
    if (Object.hasOwn(numericDefaults, key) || column.format === 'currency') {
      return { ...draft, [key]: numericDefaults[key] ?? 0 }
    }
    return { ...draft, [key]: fallbackTextByKey[key] ?? '' }
  }, workflowField ? { [workflowField.key]: workflowField.value } : {})
}

export function normalizeDraftValue(value, column) {
  if (column.format === 'currency') {
    const parsedValue = Number(value)
    return Number.isFinite(parsedValue) ? parsedValue : 0
  }
  return String(value ?? '').trim()
}

export function buildClientRecord({ draft, columns, existingCount, workflowField }) {
  const nextRecord = columns.reduce(
    (record, column) => ({
      ...record,
      [column.key]: normalizeDraftValue(draft[column.key], column),
    }),
    {
      id: `local-${existingCount + 1}`,
    },
  )

  if (workflowField) {
    return {
      ...nextRecord,
      [workflowField.key]: draft[workflowField.key] || workflowField.value,
    }
  }

  return nextRecord
}
