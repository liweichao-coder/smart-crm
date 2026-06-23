import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildBulkEditPatch,
  buildCsvContent,
  createBulkEditDraft,
  createCsvFilename,
  createDraftFromColumns,
  normalizeDraftValue,
  normalizeSortState,
  normalizeVisibleColumnKeys,
  parseListSearchState,
  patchListSearchParams,
  sortRecordsByColumn,
  summarizeBulkSettledResults,
  toggleSelectedKey,
  toggleVisibleSelection,
} from './resourceUtils.js'

test('createDraftFromColumns keeps text fields empty unless defaults are explicit', () => {
  const draft = createDraftFromColumns(
    [
      { key: 'name', label: '名称' },
      { key: 'amount', label: '金额', format: 'currency' },
      { key: 'owner', label: '负责人' },
    ],
    { key: 'stage', value: 'Prospecting' },
  )

  assert.deepEqual(draft, {
    name: '',
    amount: 0,
    owner: '',
    stage: 'Prospecting',
  })
})

test('createDraftFromColumns honors explicit column defaults', () => {
  const draft = createDraftFromColumns([
    { key: 'name', label: '客户名称', defaultValue: '' },
    { key: 'industry', label: '行业', defaultValue: '' },
    { key: 'email', label: '邮箱', defaultValue: '' },
    { key: 'status', label: '状态', defaultValue: 'active' },
  ])

  assert.deepEqual(draft, {
    name: '',
    industry: '',
    email: '',
    status: 'active',
  })
})

test('normalizeDraftValue falls back to zero for invalid currency input', () => {
  assert.equal(normalizeDraftValue('not-a-number', { key: 'revenue', format: 'currency' }), 0)
})

test('buildCsvContent exports visible records with escaped values', () => {
  const csv = buildCsvContent(
    [
      { name: '深大 AI CRM', owner: '李伟超', note: '第一行\n第二行' },
      { name: '含,逗号', owner: '王"蕾', note: '' },
    ],
    [
      { key: 'name', label: '客户名称' },
      { key: 'owner', label: '负责人' },
      { key: 'note', label: '备注' },
    ],
  )

  assert.equal(csv, '客户名称,负责人,备注\r\n深大 AI CRM,李伟超,"第一行\n第二行"\r\n"含,逗号","王""蕾",')
})

test('createCsvFilename builds a safe dated file name', () => {
  assert.equal(createCsvFilename('客户 / 线索', '2026-06-23'), '客户-线索-2026-06-23.csv')
})

test('parseListSearchState normalizes resource list URL state', () => {
  const state = parseListSearchState('q=%E5%8C%BB%E7%96%97&tab=active&view=board&order=12', {
    tabKeys: ['all', 'active'],
    defaultTab: 'all',
    viewKeys: ['list', 'board'],
    defaultView: 'list',
    selectedKey: 'order',
  })

  assert.deepEqual(state, {
    query: '医疗',
    tab: 'active',
    view: 'board',
    selectedId: '12',
  })
})

test('parseListSearchState falls back from invalid tab and view values', () => {
  const state = parseListSearchState('tab=archived&view=calendar', {
    tabKeys: ['all', 'active'],
    defaultTab: 'all',
    viewKeys: ['list', 'board'],
    defaultView: 'list',
  })

  assert.deepEqual(state, {
    query: '',
    tab: 'all',
    view: 'list',
    selectedId: '',
  })
})

test('patchListSearchParams updates list URL state while preserving unrelated params', () => {
  const params = patchListSearchParams('page=2&q=old&tab=all', {
    q: '  医疗  ',
    tab: 'active',
    view: 'list',
  }, {
    q: '',
    tab: 'all',
    view: 'list',
  })

  assert.equal(params.toString(), 'page=2&q=%E5%8C%BB%E7%96%97&tab=active')
})

test('normalizeVisibleColumnKeys restores valid saved column preferences', () => {
  const columns = [
    { key: 'name', label: '客户' },
    { key: 'owner', label: '负责人' },
    { key: 'status', label: '状态' },
  ]

  assert.deepEqual(normalizeVisibleColumnKeys(columns, ['owner', 'missing', 'name']), ['owner', 'name'])
  assert.deepEqual(normalizeVisibleColumnKeys(columns, ['missing']), ['name', 'owner', 'status'])
  assert.deepEqual(normalizeVisibleColumnKeys(columns), ['name', 'owner', 'status'])
})

test('normalizeSortState and sortRecordsByColumn apply saved table sorting', () => {
  const columns = [
    { key: 'name', label: '客户' },
    { key: 'amount', label: '金额' },
  ]
  const records = [
    { name: '云舟', amount: 1200 },
    { name: '北辰', amount: 3200 },
    { name: '南山', amount: 900 },
  ]

  assert.deepEqual(normalizeSortState(columns, { key: 'amount', direction: 'desc' }), { key: 'amount', direction: 'desc' })
  assert.deepEqual(normalizeSortState(columns, { key: 'missing', direction: 'desc' }), { key: '', direction: 'desc' })
  assert.deepEqual(sortRecordsByColumn(records, 'amount', 'desc').map((record) => record.name), ['北辰', '云舟', '南山'])
  assert.deepEqual(sortRecordsByColumn(records, 'name', 'asc').map((record) => record.name), ['北辰', '南山', '云舟'])
})

test('selection helpers toggle rows and summarize bulk results', () => {
  assert.deepEqual(toggleSelectedKey(['1', '2'], '2'), ['1'])
  assert.deepEqual(toggleSelectedKey(['1'], '2'), ['1', '2'])
  assert.deepEqual(toggleVisibleSelection(['1'], ['1', '2', '3']), ['1', '2', '3'])
  assert.deepEqual(toggleVisibleSelection(['1', '2', '3', 'x'], ['1', '2', '3']), ['x'])

  const summary = summarizeBulkSettledResults([
    { status: 'fulfilled', value: { deleted: true } },
    { status: 'rejected', reason: new Error('失败') },
    { status: 'fulfilled', value: { deleted: true } },
  ])
  assert.deepEqual(summary, { succeeded: 2, failed: 1 })
})

test('bulk edit helpers keep only enabled fields and normalize values', () => {
  const columns = [
    { key: 'owner', label: '负责人' },
    { key: 'revenue', label: '年度收入', format: 'currency' },
    { key: 'status', label: '状态' },
  ]
  const draft = createBulkEditDraft(columns)

  assert.deepEqual(draft, {
    owner: { enabled: false, value: '' },
    revenue: { enabled: false, value: '' },
    status: { enabled: false, value: '' },
  })

  const patch = buildBulkEditPatch({
    ...draft,
    owner: { enabled: true, value: '  李伟超  ' },
    revenue: { enabled: true, value: '580000' },
    status: { enabled: false, value: 'closed' },
  }, columns)

  assert.deepEqual(patch, {
    owner: '李伟超',
    revenue: 580000,
  })
})

test('bulk edit draft keeps select defaults for enabled fields', () => {
  const columns = [
    { key: 'status', label: '状态', defaultValue: 'active', options: ['active', 'closed'] },
  ]
  const draft = createBulkEditDraft(columns)

  assert.deepEqual(draft, {
    status: { enabled: false, value: 'active' },
  })

  const patch = buildBulkEditPatch({
    status: { enabled: true, value: draft.status.value },
  }, columns)
  assert.deepEqual(patch, { status: 'active' })
})
