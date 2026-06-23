import { toDraftOwner } from './ownerUtils.js'

export function cleanText(value, fallback = '') {
  const text = String(value ?? '').trim()
  return text || fallback
}

export function cleanNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
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
