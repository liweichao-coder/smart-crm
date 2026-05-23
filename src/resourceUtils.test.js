import assert from 'node:assert/strict'
import test from 'node:test'

import { buildClientRecord, createDraftFromColumns, normalizeDraftValue } from './resourceUtils.js'

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
