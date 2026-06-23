import assert from 'node:assert/strict'
import test from 'node:test'

import {
  exportAiAuditLogsCsv,
  exportAuthAuditLogsCsv,
  exportBusinessAuditLogsCsv,
  fetchAiAuditLogs,
  fetchAuthAuditLogs,
  fetchAuthSessions,
  fetchBusinessAuditLogs,
  fetchCaptureDrafts,
  revokeAuthSession,
  revokeOtherAuthSessions,
  updateCaptureDraft,
  updateLeadStage,
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

test('auth session helpers list and revoke current user sessions', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    const body = url.includes('/api/auth/sessions/revoke-others')
      ? { revoked_sessions: 3 }
      : url.includes('/api/auth/sessions/2')
      ? {
          id: 2,
          current: false,
          status: 'revoked',
          created_at: '2026-06-23T12:00:00',
          expires_at: '2026-06-30T12:00:00',
          revoked_at: '2026-06-23T13:00:00',
        }
      : [
          {
            id: 1,
            current: true,
            status: 'active',
            created_at: '2026-06-23T11:00:00',
            expires_at: '2026-06-30T11:00:00',
            revoked_at: null,
          },
          {
            id: 2,
            current: false,
            status: 'active',
            created_at: '2026-06-23T12:00:00',
            expires_at: '2026-06-30T12:00:00',
            revoked_at: null,
          },
        ]
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  const sessions = await fetchAuthSessions()
  const revoked = await revokeAuthSession(2)
  const bulkRevoked = await revokeOtherAuthSessions()

  assert.equal(calls.length, 3)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/auth/sessions')
  assert.equal(calls[0].init.method, undefined)
  assert.equal(calls[1].url, 'http://127.0.0.1:8000/api/auth/sessions/2')
  assert.equal(calls[1].init.method, 'DELETE')
  assert.equal(calls[2].url, 'http://127.0.0.1:8000/api/auth/sessions/revoke-others')
  assert.equal(calls[2].init.method, 'POST')
  assert.equal(sessions.length, 2)
  assert.equal(sessions[0].current, true)
  assert.equal(revoked.status, 'revoked')
  assert.ok(revoked.revoked_at)
  assert.equal(bulkRevoked.revoked_sessions, 3)
})

test('audit list helpers send filtered AI and business audit params', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    return new Response(JSON.stringify({
      items: [],
      total: 0,
      page: 1,
      per_page: 20,
      pages: 1,
      has_next: false,
      has_previous: false,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  await fetchAiAuditLogs({
    page: 2,
    per_page: 20,
    q: 'DeepSeek',
    operation: 'copilot_summary',
    entity_type: 'lead',
    fallback_used: false,
  })
  await fetchBusinessAuditLogs({
    page: 3,
    per_page: 20,
    q: '订单',
    action: 'update',
    entity_type: 'order',
    operator: '李伟超',
    status: 'success',
  })

  assert.equal(calls.length, 2)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/ai-audit-logs?page=2&per_page=20&q=DeepSeek&operation=copilot_summary&entity_type=lead&fallback_used=false')
  assert.equal(calls[1].url, 'http://127.0.0.1:8000/api/business-audit-logs?page=3&per_page=20&q=%E8%AE%A2%E5%8D%95&action=update&entity_type=order&operator=%E6%9D%8E%E4%BC%9F%E8%B6%85&status=success')
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

test('capture draft helpers list and update persisted drafts', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    return new Response(JSON.stringify({
      id: 7,
      status: 'submitted',
      submitted_order_id: 13,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  await fetchCaptureDrafts({ page: 1, per_page: 6, status: 'draft' })
  await updateCaptureDraft(7, { status: 'submitted', submitted_order_id: 13 })
  await updateCaptureDraft(8, { status: 'discarded' })

  assert.equal(calls.length, 3)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/vision-extract/drafts?page=1&per_page=6&status=draft')
  assert.equal(calls[1].url, 'http://127.0.0.1:8000/api/vision-extract/drafts/7')
  assert.equal(calls[1].init.method, 'PATCH')
  assert.equal(calls[1].init.body, JSON.stringify({ status: 'submitted', submitted_order_id: 13 }))
  assert.equal(calls[2].url, 'http://127.0.0.1:8000/api/vision-extract/drafts/8')
  assert.equal(calls[2].init.method, 'PATCH')
  assert.equal(calls[2].init.body, JSON.stringify({ status: 'discarded' }))
})

test('updateLeadStage patches only the pipeline stage', async (t) => {
  const originalFetch = globalThis.fetch
  const calls = []

  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    return new Response(JSON.stringify({
      id: 15,
      stage: 'proposal',
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  t.after(() => {
    globalThis.fetch = originalFetch
  })

  const payload = await updateLeadStage(15, 'proposal')

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/leads/15')
  assert.equal(calls[0].init.method, 'PATCH')
  assert.equal(calls[0].init.body, JSON.stringify({ stage: 'proposal' }))
  assert.equal(payload.stage, 'proposal')
})
