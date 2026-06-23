import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildOrderPayloadFromCapture,
  matchCaptureCustomer,
  matchCaptureProduct,
} from './captureUtils.js'

const customers = [
  { id: 1, company: '云川医疗', contact_person: '陈敏', name: '陈敏', email: 'chenmin@example.com' },
]

const products = [
  { id: 10, name: '智能巡检终端', sku: 'AI-DEVICE-001', unit_price: 16800 },
  { id: 11, name: '客户数据接入服务', sku: 'SERV-API-003', unit_price: 4200 },
]

const captureResult = {
  customer_id: 1,
  company: '云川医疗',
  customer_name: '陈敏',
  confidence: 0.92,
  source: 'llm_text',
  summary: '抽取到 2 个订单条目。',
  items: [
    { product_id: 10, product_name: '智能巡检终端', quantity: 2, unit_price: 16800 },
    { product_id: 11, product_name: '客户数据接入服务', quantity: 1, unit_price: 4200 },
  ],
}

test('matchCaptureCustomer matches company or contact person', () => {
  assert.equal(matchCaptureCustomer(captureResult, customers).id, 1)
  assert.equal(matchCaptureCustomer({ company: '', customer_name: '陈敏' }, customers).id, 1)
  assert.equal(matchCaptureCustomer({ company: '', customer_name: '' }, customers), undefined)
})

test('matchCaptureProduct prefers backend product id and falls back to name or sku', () => {
  assert.equal(matchCaptureProduct({ product_name: '智能巡检终端' }, products).id, 10)
  assert.equal(matchCaptureProduct({ product_name: 'SERV-API-003' }, products).id, 11)
  assert.equal(matchCaptureProduct({ product_id: 11, product_name: '识别别名' }, products).id, 11)
  assert.equal(matchCaptureProduct({ product_name: '' }, products), undefined)
})

test('buildOrderPayloadFromCapture creates backend order payload', () => {
  const payload = buildOrderPayloadFromCapture({
    captureResult,
    customers,
    products,
    owner: '李伟超',
    region: '华南',
    today: '2026-06-22',
  })

  assert.equal(payload.customer_id, 1)
  assert.equal(payload.created_by_ai, true)
  assert.equal(payload.order_date, '2026-06-22')
  assert.equal(payload.due_date, '2026-06-29')
  assert.equal(payload.items[0].product_id, 10)
  assert.equal(payload.items[0].quantity, 2)
})

test('buildOrderPayloadFromCapture uses backend matched ids before fuzzy names', () => {
  const payload = buildOrderPayloadFromCapture({
    captureResult: {
      ...captureResult,
      company: '模型识别别名',
      customer_name: '陈敏',
      items: [{ product_id: 11, product_name: '客户数据服务别名', quantity: 3, unit_price: 4200 }],
    },
    customers,
    products,
    owner: '李伟超',
  })

  assert.equal(payload.customer_id, 1)
  assert.equal(payload.items[0].product_id, 11)
  assert.equal(payload.items[0].quantity, 3)
})

test('buildOrderPayloadFromCapture rejects unmatched products', () => {
  assert.throws(() => {
    buildOrderPayloadFromCapture({
      captureResult: {
        ...captureResult,
        items: [{ product_name: '不存在商品', quantity: 1, unit_price: 1 }],
      },
      customers,
      products,
      owner: '李伟超',
    })
  }, /未能匹配商品/)
})
