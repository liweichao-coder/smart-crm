const ownerPlaceholderValues = new Set(['未分配', '待分配', '新负责人'])

export function toDraftOwner(value, fallback) {
  const text = String(value ?? '').trim()
  const owner = text || fallback
  return ownerPlaceholderValues.has(owner) ? fallback : owner
}
