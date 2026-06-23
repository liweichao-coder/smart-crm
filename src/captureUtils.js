function normalizeText(value) {
  return String(value ?? '').trim().toLowerCase()
}

function addDays(dateText, days) {
  const [year, month, day] = dateText.split('-').map(Number)
  const date = new Date(Date.UTC(year, month - 1, day))
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

export function matchCaptureCustomer(captureResult, customers) {
  const customerId = Number(captureResult?.customer_id)
  if (Number.isFinite(customerId) && customerId > 0) {
    const matchedById = customers.find((customer) => Number(customer.id) === customerId)
    if (matchedById) {
      return matchedById
    }
  }

  const company = normalizeText(captureResult?.company)
  const customerName = normalizeText(captureResult?.customer_name)
  const requestedNames = [company, customerName].filter(Boolean)
  if (!requestedNames.length) {
    return undefined
  }
  return customers.find((customer) => {
    const candidates = [
      customer.company,
      customer.contact_person,
      customer.name,
      customer.email,
    ].map(normalizeText)
    return candidates.some((candidate) => (
      candidate && requestedNames.some((name) => candidate === name || name.includes(candidate) || candidate.includes(name))
    ))
  })
}

export function matchCaptureProduct(captureItem, products) {
  const productId = Number(captureItem?.product_id)
  if (Number.isFinite(productId) && productId > 0) {
    const matchedById = products.find((product) => Number(product.id) === productId)
    if (matchedById) {
      return matchedById
    }
  }

  const productName = normalizeText(captureItem?.product_name)
  if (!productName) {
    return undefined
  }
  return products.find((product) => {
    const candidates = [product.name, product.sku].map(normalizeText)
    return candidates.some((candidate) => candidate && (candidate === productName || productName.includes(candidate) || candidate.includes(productName)))
  })
}

export function buildOrderPayloadFromCapture({
  captureResult,
  customers,
  products,
  owner,
  region = '华南',
  today = new Date().toISOString().slice(0, 10),
}) {
  const customer = matchCaptureCustomer(captureResult, customers)
  if (!customer) {
    throw new Error('未能匹配客户，请先检查智能录单的客户名称')
  }

  const items = (captureResult?.items ?? []).map((item) => {
    const product = matchCaptureProduct(item, products)
    if (!product) {
      throw new Error(`未能匹配商品：${item.product_name}`)
    }
    return {
      product_id: product.id,
      quantity: Math.max(Number(item.quantity) || 1, 1),
      unit_price: Number(item.unit_price || product.unit_price),
    }
  })

  if (!items.length) {
    throw new Error('草稿中没有可提交的订单条目')
  }

  return {
    customer_id: customer.id,
    owner,
    region,
    currency: 'CNY',
    status: 'draft',
    order_date: today,
    due_date: addDays(today, 7),
    notes: `AI Capture 生成：${captureResult.summary || '智能录单草稿'}；来源 ${captureResult.source || 'unknown'}。`,
    created_by_ai: true,
    ai_confidence_score: Number(captureResult.confidence ?? 0),
    items,
  }
}
