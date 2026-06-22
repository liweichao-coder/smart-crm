import assert from 'node:assert/strict'
import test from 'node:test'

import { buildClientRecord, buildCsvContent, createCsvFilename, createDraftFromColumns, normalizeDraftValue } from './resourceUtils.js'

test('createDraftFromColumns builds sensible defaults for resource forms', () => {
  const draft = createDraftFromColumns(
    [
      { key: 'name', label: '名称' },
      { key: 'amount', label: '金额', format: 'currency' },
      { key: 'owner', label: '负责人' },
    ],
    { key: 'stage', value: 'Prospecting' },
  )

  assert.deepEqual(draft, {
    name: '新建记录',
    amount: 0,
    owner: '未分配',
    stage: 'Prospecting',
  })
})

test('buildClientRecord normalizes text and currency values', () => {
  const record = buildClientRecord({
    existingCount: 3,
    draft: {
      name: '  新商机  ',
      amount: '128000',
      stage: 'Proposal',
    },
    columns: [
      { key: 'name', label: '名称' },
      { key: 'amount', label: '金额', format: 'currency' },
    ],
    workflowField: { key: 'stage', value: 'Prospecting' },
  })

  assert.deepEqual(record, {
    id: 'local-4',
    name: '新商机',
    amount: 128000,
    stage: 'Proposal',
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
