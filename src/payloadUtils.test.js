import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildCasePayload,
  buildContactPayload,
  buildCustomerPayload,
  buildGoalPayload,
  buildLeadPayload,
  buildOrderUpdatePayload,
  buildProductPayload,
  buildTaskPayload,
  buildTeamMemberPayload,
} from './payloadUtils.js'

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

test('buildCustomerPayload leaves missing customer industry empty for backend validation', () => {
  const payload = buildCustomerPayload({
    name: '深圳真实客户有限公司',
    industry: '',
    contactPerson: '张客户',
    phone: '',
    email: '',
    city: '',
    source: '',
    level: 'B',
    owner: '',
    revenue: '',
    status: 'active',
  }, '李伟超')

  assert.equal(payload.industry, '')
  assert.equal(payload.phone, '')
  assert.equal(payload.email, '')
  assert.equal(payload.city, '深圳')
  assert.equal(payload.source, '前端录入')
  assert.equal(payload.owner, '李伟超')
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

test('buildProductPayload preserves catalog master data without generated SKU', () => {
  const payload = buildProductPayload({
    name: '  智能巡检终端 Pro  ',
    sku: ' EDGE-AI-2026 ',
    category: '硬件',
    unitPrice: '16800',
    stock: '42.7',
  })

  assert.deepEqual(payload, {
    name: '智能巡检终端 Pro',
    sku: 'EDGE-AI-2026',
    category: '硬件',
    unit_price: 16800,
    stock: 43,
  })
})

test('buildProductPayload leaves missing required catalog fields empty for backend validation', () => {
  const payload = buildProductPayload({
    name: '',
    sku: '',
    category: '',
    unitPrice: '',
    stock: '',
  })

  assert.deepEqual(payload, {
    name: '',
    sku: '',
    category: '软件',
    unit_price: 0,
    stock: 0,
  })
})

test('buildLeadPayload preserves real lead fields without placeholder customer', () => {
  const payload = buildLeadPayload({
    name: '  深圳园区续费线索  ',
    company: ' 深圳园区科技 ',
    owner: '未分配',
    region: '华南',
    amount: '96000',
    stage: '已联系',
    nextStep: '约产品负责人确认预算',
  }, '李伟超')

  assert.deepEqual(payload, {
    title: '深圳园区续费线索',
    customer_name: '深圳园区科技',
    owner: '李伟超',
    region: '华南',
    expected_amount: 96000,
    stage: 'contacted',
    next_action: '约产品负责人确认预算',
    ai_assisted: false,
  })
})

test('buildLeadPayload leaves missing lead title and customer empty for backend validation', () => {
  const payload = buildLeadPayload({
    name: '',
    account: '',
    owner: '',
    region: '',
    amount: '',
    stage: '',
    nextStep: '',
    closeDate: '',
  }, '徐柠')

  assert.deepEqual(payload, {
    title: '',
    customer_name: '',
    owner: '徐柠',
    region: '华南',
    expected_amount: 0,
    stage: 'new',
    next_action: '',
    ai_assisted: false,
  })
})

test('buildCasePayload preserves real case fields without placeholder account', () => {
  const payload = buildCasePayload({
    title: '  续费审批阻塞  ',
    account: ' 深圳园区科技 ',
    owner: '待分配',
    priority: 'hot',
    statusLabel: 'Pending',
  }, '李伟超')

  assert.deepEqual(payload, {
    title: '续费审批阻塞',
    account: '深圳园区科技',
    owner: '李伟超',
    priority: 'hot',
    status: 'working',
    status_label: 'Pending',
  })
})

test('buildTaskPayload preserves real task text and leaves missing required fields empty', () => {
  assert.deepEqual(buildTaskPayload({
    title: '  准备 ROI 测算  ',
    description: '  下周例会前补齐测算表  ',
    owner: '新负责人',
    dueDate: '2026-06-30 18:00',
    priority: 'warm',
    statusLabel: '今天',
  }, '徐柠'), {
    title: '准备 ROI 测算',
    description: '下周例会前补齐测算表',
    owner: '徐柠',
    due_date: '2026-06-30 18:00',
    priority: 'warm',
    status: 'today',
    status_label: '今天',
  })

  assert.deepEqual(buildTaskPayload({
    title: '',
    description: '',
    owner: '',
    dueDate: '',
    priority: '',
    statusLabel: '',
  }, '徐柠'), {
    title: '',
    description: '',
    owner: '徐柠',
    due_date: '',
    priority: 'warm',
    status: 'week',
    status_label: '本周',
  })
})

test('buildGoalPayload keeps real goal fields and lets backend reject empty target data', () => {
  const payload = buildGoalPayload({
    name: '  华南续费目标  ',
    period: '  2026 Q3  ',
    owner: '未分配',
    current: '120000',
    target: '',
    note: '  聚焦存量续费  ',
  }, '李伟超')

  assert.deepEqual(payload, {
    name: '华南续费目标',
    period: '2026 Q3',
    owner: '李伟超',
    current: 120000,
    target: 0,
    note: '聚焦存量续费',
  })
})

test('buildOrderUpdatePayload preserves real order edit fields without default notes or dates', () => {
  const payload = buildOrderUpdatePayload({
    owner: ' 未分配 ',
    region: ' 华南 ',
    status: 'confirmed',
    dueDate: '2026-07-08',
    notes: '  客户确认分批交付  ',
    items: [
      { productId: '3', quantity: '2', unitPrice: '12800' },
    ],
  }, '李伟超')

  assert.deepEqual(payload, {
    owner: '李伟超',
    region: '华南',
    status: 'confirmed',
    due_date: '2026-07-08',
    notes: '客户确认分批交付',
    items: [
      { product_id: 3, quantity: 2, unit_price: 12800 },
    ],
  })
})

test('buildOrderUpdatePayload leaves missing order edit fields empty for backend validation', () => {
  const payload = buildOrderUpdatePayload({
    owner: '',
    region: '',
    status: '',
    dueDate: '',
    notes: '',
    items: [
      { productId: '', quantity: '', unitPrice: '' },
    ],
  }, '徐柠')

  assert.deepEqual(payload, {
    owner: '徐柠',
    region: '',
    status: '',
    due_date: '',
    notes: '',
    items: [
      { product_id: 0, quantity: 1, unit_price: 0.01 },
    ],
  })
})

test('buildTeamMemberPayload preserves real account fields for member creation', () => {
  const payload = buildTeamMemberPayload({
    fullName: '  张远  ',
    email: ' zhangyuan@example.com ',
    phone: ' 13700137000 ',
    role: '销售经理',
    position: '区域负责人',
    department: '华南客户成功部',
    location: '深圳 · 粤海',
    status: 'active',
    password: 'SmartCRM@2026',
    confirmPassword: 'SmartCRM@2026',
  })

  assert.deepEqual(payload, {
    full_name: '张远',
    email: 'zhangyuan@example.com',
    phone: '13700137000',
    role: '销售经理',
    position: '区域负责人',
    department: '华南客户成功部',
    location: '深圳 · 粤海',
    status: 'active',
    password: 'SmartCRM@2026',
    confirm_password: 'SmartCRM@2026',
  })
})

test('buildTeamMemberPayload does not invent demo email or reset password on edit', () => {
  const payload = buildTeamMemberPayload({
    fullName: '',
    email: '',
    phone: '',
    role: '',
    position: '',
    department: '',
    location: '',
    status: '',
    password: '',
    confirmPassword: '',
  }, true)

  assert.deepEqual(payload, {
    full_name: '',
    email: '',
    phone: '',
    role: '销售',
    position: '',
    department: '',
    location: '',
    status: 'active',
  })
})
