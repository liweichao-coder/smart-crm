import assert from 'node:assert/strict'
import test from 'node:test'

import { getSessionOrganizations, resolveSelectedOrg } from './sessionUtils.js'

test('getSessionOrganizations maps backend organization metadata', () => {
  const organizations = getSessionOrganizations({
    organizations: [
      { id: 7, name: '深大 AI CRM 课程组', role: '管理员', slug: 'szu-ai-crm-course', plan: 'course', status: 'active' },
    ],
  })

  assert.deepEqual(organizations, [
    { id: 7, name: '深大 AI CRM 课程组', role: '管理员', slug: 'szu-ai-crm-course', plan: 'course', status: 'active' },
  ])
})

test('resolveSelectedOrg replaces stale local mock organization with backend organization', () => {
  const selectedOrg = resolveSelectedOrg(
    {
      organizations: [
        { id: 1, name: '深大 AI CRM 课程组', role: '管理员', slug: 'szu-ai-crm-course', plan: 'course', status: 'active' },
      ],
    },
    { id: 'org-1', name: '旧版本地组织', role: 'ADMIN' },
  )

  assert.equal(selectedOrg.id, 1)
  assert.equal(selectedOrg.name, '深大 AI CRM 课程组')
})

test('getSessionOrganizations falls back to user organization for older stored sessions', () => {
  const organizations = getSessionOrganizations({
    user: {
      organization_id: 3,
      organization_name: '课程答辩测试组',
      role: '管理员',
      status: 'active',
    },
  })

  assert.equal(organizations[0].id, 3)
  assert.equal(organizations[0].name, '课程答辩测试组')
})
