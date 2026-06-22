import assert from 'node:assert/strict'
import test from 'node:test'

import { filterOrders, getStockTone, pickLowStockProducts, summarizeOrders } from './orderUtils.js'

const orders = [
  {
    id: 1,
    status: 'draft',
    created_by_ai: true,
    ai_confidence_score: 0.82,
    total_amount: 12000,
    items: [{ id: 1 }, { id: 2 }],
  },
  {
    id: 2,
    status: 'confirmed',
    created_by_ai: false,
    ai_confidence_score: 0,
    total_amount: 8000,
    items: [{ id: 3 }],
  },
  {
    id: 3,
    status: 'fulfilled',
    created_by_ai: true,
    ai_confidence_score: 0.9,
    total_amount: 10000,
    items: [],
  },
]

test('summarizeOrders returns revenue, AI count, draft count and average confidence', () => {
  assert.deepEqual(summarizeOrders(orders), {
    totalRevenue: 30000,
    orderCount: 3,
    aiOrderCount: 2,
    draftCount: 1,
    totalItems: 3,
    avgConfidence: 0.86,
  })
})

test('filterOrders supports AI, manual and status filters', () => {
  assert.deepEqual(filterOrders(orders, 'ai').map((order) => order.id), [1, 3])
  assert.deepEqual(filterOrders(orders, 'manual').map((order) => order.id), [2])
  assert.deepEqual(filterOrders(orders, 'confirmed').map((order) => order.id), [2])
  assert.equal(filterOrders(orders, 'all').length, 3)
})

test('pickLowStockProducts sorts products by stock and limits the result', () => {
  const products = [
    { id: 1, stock: 320 },
    { id: 2, stock: 24 },
    { id: 3, stock: 90 },
  ]

  assert.deepEqual(pickLowStockProducts(products, 2).map((product) => product.id), [2, 3])
})

test('getStockTone marks critical and warning inventory levels', () => {
  assert.equal(getStockTone({ stock: 80 }), 'danger')
  assert.equal(getStockTone({ stock: 300 }), 'warning')
  assert.equal(getStockTone({ stock: 301 }), 'success')
})
