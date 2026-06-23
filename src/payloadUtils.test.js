import assert from 'node:assert/strict'
import test from 'node:test'

import { buildContactPayload, buildCustomerPayload } from './payloadUtils.js'

test('buildCustomerPayload preserves real customer master data fields', () => {
  const payload = buildCustomerPayload({
    name: '  深圳未来制造有限公司  ',
    industry: '智能制造',
    contactPerson: ' 陈敏 ',
    phone: ' 13800138000 ',
    email: ' buyer@example.com ',
    city: '深圳',
    source: '展会线索',
    level: 'A',
    owner: '未分配',
    revenue: '680000',
    status: 'proposal',
  }, '李伟超')

  assert.deepEqual(payload, {
    company: '深圳未来制造有限公司',
    name: '陈敏',
    owner: '李伟超',
    industry: '智能制造',
    city: '深圳',
    contact_person: '陈敏',
    phone: '13800138000',
    email: 'buyer@example.com',
    source: '展会线索',
    level: 'A',
    annual_revenue: 680000,
    status: 'proposal',
  })
})

test('buildContactPayload keeps entered phone and email without demo defaults', () => {
  const payload = buildContactPayload({
    name: ' 王蕾 ',
    company: '云舟智能',
    role: '采购负责人',
    email: ' wanglei@example.com ',
    phone: ' 13900139000 ',
    owner: '',
    status: 'nurturing',
  }, '徐柠')

  assert.deepEqual(payload, {
    name: '王蕾',
    company: '云舟智能',
    role: '采购负责人',
    email: 'wanglei@example.com',
    phone: '13900139000',
    owner: '徐柠',
    status: 'nurturing',
  })
})
