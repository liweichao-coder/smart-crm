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
    if (Object.hasOwn(column, 'defaultValue')) {
      return { ...draft, [key]: column.defaultValue }
    }
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

function escapeCsvValue(value) {
  const text = String(value ?? '')
  if (/[",\r\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`
  }
  return text
}

export function buildCsvContent(records, columns) {
  const header = columns.map((column) => escapeCsvValue(column.label)).join(',')
  const rows = records.map((record) =>
    columns.map((column) => escapeCsvValue(record[column.key])).join(','),
  )
  return [header, ...rows].join('\r\n')
}

export function createCsvFilename(title, date = new Date()) {
  const datePart = date instanceof Date ? date.toISOString().slice(0, 10) : String(date).slice(0, 10)
  const safeTitle = String(title || 'resource')
    .trim()
    .replace(/[\\/:*?"<>|\s]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
  return `${safeTitle || 'resource'}-${datePart}.csv`
}

function toSearchParams(searchParams) {
  return searchParams instanceof URLSearchParams ? searchParams : new URLSearchParams(searchParams)
}

function normalizeOption(value, allowedValues, fallback) {
  const text = String(value ?? '').trim()
  return allowedValues.includes(text) ? text : fallback
}

export function parseListSearchState(searchParams, options = {}) {
  const params = toSearchParams(searchParams)
  const tabKeys = options.tabKeys ?? []
  const viewKeys = options.viewKeys ?? []
  const selectedKey = options.selectedKey ?? ''
  const defaultTab = options.defaultTab ?? tabKeys[0] ?? ''
  const defaultView = options.defaultView ?? viewKeys[0] ?? ''

  return {
    query: params.get('q') ?? '',
    tab: tabKeys.length ? normalizeOption(params.get('tab'), tabKeys, defaultTab) : defaultTab,
    view: viewKeys.length ? normalizeOption(params.get('view'), viewKeys, defaultView) : defaultView,
    selectedId: selectedKey ? (params.get(selectedKey) ?? '') : '',
  }
}

export function patchListSearchParams(searchParams, updates = {}, defaults = {}) {
  const nextParams = new URLSearchParams(toSearchParams(searchParams))

  for (const [key, value] of Object.entries(updates)) {
    const text = String(value ?? '').trim()
    const defaultText = String(defaults[key] ?? '').trim()
    if (!text || text === defaultText) {
      nextParams.delete(key)
    } else {
      nextParams.set(key, text)
    }
  }

  return nextParams
}

export function normalizeVisibleColumnKeys(columns, savedKeys) {
  const allKeys = columns.map((column) => column.key)
  if (!Array.isArray(savedKeys)) {
    return allKeys
  }
  const visibleKeys = savedKeys.filter((key) => allKeys.includes(key))
  return visibleKeys.length ? visibleKeys : allKeys
}

export function normalizeSortState(columns, savedSort = {}) {
  const allKeys = columns.map((column) => column.key)
  const key = allKeys.includes(savedSort?.key) ? savedSort.key : ''
  const direction = savedSort?.direction === 'desc' ? 'desc' : 'asc'
  return { key, direction }
}

function normalizeSortValue(value) {
  if (value === null || value === undefined) {
    return ''
  }
  const numberValue = Number(value)
  if (Number.isFinite(numberValue) && String(value).trim() !== '') {
    return numberValue
  }
  return String(value).toLowerCase()
}

export function sortRecordsByColumn(records, sortKey, sortDirection = 'asc') {
  if (!sortKey) {
    return records
  }
  const directionMultiplier = sortDirection === 'desc' ? -1 : 1
  return [...records].sort((leftRecord, rightRecord) => {
    const leftValue = normalizeSortValue(leftRecord[sortKey])
    const rightValue = normalizeSortValue(rightRecord[sortKey])
    if (leftValue === rightValue) {
      return 0
    }
    if (typeof leftValue === 'number' && typeof rightValue === 'number') {
      return (leftValue - rightValue) * directionMultiplier
    }
    return String(leftValue).localeCompare(String(rightValue), 'zh-Hans-CN') * directionMultiplier
  })
}

export function toggleSelectedKey(selectedKeys, key) {
  const selectedSet = new Set(selectedKeys)
  if (selectedSet.has(key)) {
    selectedSet.delete(key)
  } else {
    selectedSet.add(key)
  }
  return [...selectedSet]
}

export function toggleVisibleSelection(selectedKeys, visibleKeys) {
  const visibleSet = new Set(visibleKeys)
  const selectedSet = new Set(selectedKeys)
  const allVisibleSelected = visibleKeys.length > 0 && visibleKeys.every((key) => selectedSet.has(key))
  if (allVisibleSelected) {
    return selectedKeys.filter((key) => !visibleSet.has(key))
  }
  visibleKeys.forEach((key) => selectedSet.add(key))
  return [...selectedSet]
}

export function summarizeBulkSettledResults(results) {
  return results.reduce(
    (summary, result) => ({
      succeeded: summary.succeeded + (result.status === 'fulfilled' ? 1 : 0),
      failed: summary.failed + (result.status === 'rejected' ? 1 : 0),
    }),
    { succeeded: 0, failed: 0 },
  )
}

export function createBulkEditDraft(columns) {
  return columns.reduce(
    (draft, column) => ({
      ...draft,
      [column.key]: {
        enabled: false,
        value: Object.hasOwn(column, 'defaultValue') ? column.defaultValue : '',
      },
    }),
    {},
  )
}

export function buildBulkEditPatch(draft, columns) {
  return columns.reduce((patch, column) => {
    const field = draft[column.key]
    if (!field?.enabled) {
      return patch
    }
    return {
      ...patch,
      [column.key]: normalizeDraftValue(field.value, column),
    }
  }, {})
}
