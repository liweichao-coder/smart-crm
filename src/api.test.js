import assert from 'node:assert/strict'
import test from 'node:test'

import { exportAuthAuditLogsCsv, fetchAuthAuditLogs } from './api.js'

test('fetchAuthAuditLogs sends paginated auth audit filters to the backend', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    return new Response(JSON.stringify({
      items: [],
      total: 0,
      page: 2,
      per_page: 20,
      pages: 1,
      has_next: false,
      has_previous: true,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  const payload = await fetchAuthAuditLogs({
    page: 2,
    per_page: 20,
    q: 'demo@example.com',
    event: 'login',
    status: 'failed',
    empty: '',
  })

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/auth/audit-logs?page=2&per_page=20&q=demo%40example.com&event=login&status=failed')
  assert.equal(calls[0].init.headers['Content-Type'], 'application/json')
  assert.equal(payload.page, 2)
  assert.equal(payload.has_previous, true)
})

test('exportAuthAuditLogsCsv downloads the filtered auth audit CSV', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    return new Response('日志ID,时间,事件,状态,账号\r\n1,2026-06-23,login,failed,demo@smart-crm.local', {
      status: 200,
      headers: { 'Content-Type': 'text/csv; charset=utf-8' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  const blob = await exportAuthAuditLogsCsv({
    q: 'demo@example.com',
    event: 'login',
    status: 'failed',
  })

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/auth/audit-logs/export.csv?q=demo%40example.com&event=login&status=failed')
  assert.equal(calls[0].init.headers?.Authorization, undefined)
  assert.equal(blob.type, 'text/csv;charset=utf-8')
  assert.match(await blob.text(), /login,failed/)
})
