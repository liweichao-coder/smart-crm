import assert from 'node:assert/strict'
import test from 'node:test'

import { toDraftOwner } from './ownerUtils.js'

test('toDraftOwner falls back to the current authenticated user for empty owners', () => {
  assert.equal(toDraftOwner('', '李伟超'), '李伟超')
  assert.equal(toDraftOwner('   ', '李伟超'), '李伟超')
})

test('toDraftOwner replaces resource form placeholders with the current user', () => {
  assert.equal(toDraftOwner('未分配', '李伟超'), '李伟超')
  assert.equal(toDraftOwner('待分配', '李伟超'), '李伟超')
  assert.equal(toDraftOwner('新负责人', '李伟超'), '李伟超')
})

test('toDraftOwner preserves explicit owner names', () => {
  assert.equal(toDraftOwner('王蕾', '李伟超'), '王蕾')
})
