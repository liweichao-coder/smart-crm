import assert from 'node:assert/strict'
import test from 'node:test'

import {
  exportAiAuditLogsCsv,
  exportAuthAuditLogsCsv,
  exportBusinessAuditLogsCsv,
  fetchAuthAuditLogs,
} from './api.js'

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

test('audit export helpers download filtered AI and business audit CSVs', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    return new Response('日志ID,时间,动作\r\n1,2026-06-23,export', {
      status: 200,
      headers: { 'Content-Type': 'text/csv; charset=utf-8' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  const aiBlob = await exportAiAuditLogsCsv({ operation: 'vision_extract', fallback_used: true })
  const businessBlob = await exportBusinessAuditLogsCsv({ action: 'create', entity_type: 'customer' })

  assert.equal(calls.length, 2)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/ai-audit-logs/export.csv?operation=vision_extract&fallback_used=true')
  assert.equal(calls[1].url, 'http://127.0.0.1:8000/api/business-audit-logs/export.csv?action=create&entity_type=customer')
  assert.equal(aiBlob.type, 'text/csv;charset=utf-8')
  assert.equal(businessBlob.type, 'text/csv;charset=utf-8')
})
