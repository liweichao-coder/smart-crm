import { toDraftOwner } from './ownerUtils.js'

const leadStageLabelMap = {
  new: '新线索',
  contacted: '已联系',
  qualified: '已评估',
  proposal: '方案中',
  negotiation: '谈判中',
  won: '已赢单',
  lost: '已丢单',
}

const caseStatusValueMap = {
  Open: 'open',
  Pending: 'working',
  Resolved: 'closed',
  open: 'open',
  working: 'working',
  closed: 'closed',
}

const caseStatusLabelMap = {
  open: 'Open',
  working: 'Pending',
  closed: 'Resolved',
}

const taskStatusValueMap = {
  今天: 'today',
  本周: 'week',
  逾期: 'overdue',
  today: 'today',
  week: 'week',
  overdue: 'overdue',
}

const taskStatusLabelMap = {
  today: '今天',
  week: '本周',
  overdue: '逾期',
}

export function cleanText(value, fallback = '') {
  const text = String(value ?? '').trim()
  return text || fallback
}

export function cleanNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function normalizeLeadStage(stage) {
  const text = cleanText(stage, 'new')
  const matchedEntry = Object.entries(leadStageLabelMap).find(([key, label]) => key === text || label === text)
  return matchedEntry?.[0] ?? text
}

export function buildCustomerPayload(draft, ownerFallback) {
  const owner = toDraftOwner(draft.owner, ownerFallback)
  const company = cleanText(draft.name)
  const contactPerson = cleanText(draft.contactPerson)
  return {
    company,
    name: contactPerson,
    owner,
    industry: cleanText(draft.industry),
    city: cleanText(draft.city, '深圳'),
    contact_person: contactPerson,
    phone: cleanText(draft.phone),
    email: cleanText(draft.email),
    source: cleanText(draft.source, '前端录入'),
    level: cleanText(draft.level, 'B'),
    annual_revenue: cleanNumber(draft.revenue),
    status: cleanText(draft.status, 'active'),
  }
}

export function buildContactPayload(draft, ownerFallback) {
  return {
    name: cleanText(draft.name),
    company: cleanText(draft.company),
    role: cleanText(draft.role, '待确认'),
    email: cleanText(draft.email),
    phone: cleanText(draft.phone),
    owner: toDraftOwner(draft.owner, ownerFallback),
    status: cleanText(draft.status, 'active'),
  }
}

export function buildProductPayload(draft) {
  return {
    name: cleanText(draft.name),
    sku: cleanText(draft.sku),
    category: cleanText(draft.category, '软件'),
    unit_price: cleanNumber(draft.unitPrice, 0),
    stock: Math.max(0, Math.round(cleanNumber(draft.stock, 0))),
  }
}

export function buildLeadPayload(draft, ownerFallback) {
  const payload = {
    title: cleanText(draft.name),
    customer_name: cleanText(draft.company ?? draft.account),
    owner: toDraftOwner(draft.owner, ownerFallback),
    region: cleanText(draft.region, '华南'),
    expected_amount: cleanNumber(draft.amount),
    stage: normalizeLeadStage(draft.stage),
    next_action: cleanText(draft.nextStep),
    ai_assisted: false,
  }
  const dueDate = cleanText(draft.closeDate)
  if (dueDate) {
    payload.due_date = dueDate
  }
  return payload
}

export function buildCasePayload(draft, ownerFallback) {
  const statusText = cleanText(draft.status)
  const statusLabelText = cleanText(draft.statusLabel)
  const status = caseStatusValueMap[statusLabelText] ?? caseStatusValueMap[statusText] ?? 'open'
  return {
    title: cleanText(draft.title),
    account: cleanText(draft.account),
    owner: toDraftOwner(draft.owner, ownerFallback),
    priority: cleanText(draft.priority, 'warm'),
    status,
    status_label: statusLabelText || caseStatusLabelMap[status],
  }
}

export function buildTaskPayload(draft, ownerFallback) {
  const status = taskStatusValueMap[cleanText(draft.statusLabel || draft.status)] ?? 'week'
  return {
    title: cleanText(draft.title),
    description: cleanText(draft.description),
    owner: toDraftOwner(draft.owner, ownerFallback),
    due_date: cleanText(draft.dueDate),
    priority: cleanText(draft.priority, 'warm'),
    status,
    status_label: taskStatusLabelMap[status],
  }
}

export function buildGoalPayload(draft, ownerFallback) {
  return {
    name: cleanText(draft.name),
    period: cleanText(draft.period),
    owner: toDraftOwner(draft.owner, ownerFallback),
    current: cleanNumber(draft.current),
    target: cleanNumber(draft.target),
    note: cleanText(draft.note),
  }
}

export function buildTeamMemberPayload(draft, isEditing = false) {
  const payload = {
    full_name: cleanText(draft.fullName),
    email: cleanText(draft.email),
    phone: cleanText(draft.phone),
    role: cleanText(draft.role, '销售'),
    position: cleanText(draft.position),
    department: cleanText(draft.department),
    location: cleanText(draft.location),
    status: cleanText(draft.status, 'active'),
  }
  const hasPasswordChange = cleanText(draft.password) || cleanText(draft.confirmPassword)
  if (!isEditing || hasPasswordChange) {
    payload.password = draft.password ?? ''
    payload.confirm_password = draft.confirmPassword ?? ''
  }
  return payload
}
