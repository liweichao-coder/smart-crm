export const ORDER_FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'ai', label: 'AI 创建' },
  { key: 'manual', label: '人工创建' },
  { key: 'draft', label: '草稿' },
  { key: 'confirmed', label: '已确认' },
  { key: 'fulfilled', label: '已履约' },
]

export function filterOrders(orders, filterKey) {
  if (filterKey === 'ai') {
    return orders.filter((order) => order.created_by_ai)
  }
  if (filterKey === 'manual') {
    return orders.filter((order) => !order.created_by_ai)
  }
  if (['draft', 'confirmed', 'fulfilled'].includes(filterKey)) {
    return orders.filter((order) => order.status === filterKey)
  }
  return orders
}

export function summarizeOrders(orders) {
  const aiOrders = orders.filter((order) => order.created_by_ai)
  const totalRevenue = orders.reduce((total, order) => total + Number(order.total_amount ?? 0), 0)
  const totalItems = orders.reduce((total, order) => total + (order.items?.length ?? 0), 0)
  const avgConfidence = aiOrders.length
    ? aiOrders.reduce((total, order) => total + Number(order.ai_confidence_score ?? 0), 0) / aiOrders.length
    : 0

  return {
    totalRevenue,
    orderCount: orders.length,
    aiOrderCount: aiOrders.length,
    draftCount: orders.filter((order) => order.status === 'draft').length,
    totalItems,
    avgConfidence,
  }
}

export function getStockTone(product) {
  const stock = Number(product.stock ?? 0)
  if (stock <= 80) {
    return 'danger'
  }
  if (stock <= 300) {
    return 'warning'
  }
  return 'success'
}

export function pickLowStockProducts(products, limit = 6) {
  return [...products]
    .sort((first, second) => Number(first.stock ?? 0) - Number(second.stock ?? 0))
    .slice(0, limit)
}
