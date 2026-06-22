export function getSessionOrganizations(authSession) {
  const organizations = authSession?.organizations ?? []
  if (organizations.length) {
    return organizations.map((org) => ({
      id: org.id,
      name: org.name,
      role: org.role,
      slug: org.slug,
      plan: org.plan,
      status: org.status,
    }))
  }
  if (authSession?.user?.organization_id) {
    return [
      {
        id: authSession.user.organization_id,
        name: authSession.user.organization_name,
        role: authSession.user.role,
        slug: '',
        plan: 'course',
        status: authSession.user.status,
      },
    ]
  }
  return []
}

export function resolveSelectedOrg(authSession, currentOrg = null) {
  const organizations = getSessionOrganizations(authSession)
  if (!organizations.length) {
    return currentOrg ?? { id: 'current', name: '深大 AI CRM', role: '未选择组织', slug: '', plan: 'course', status: 'active' }
  }
  const matchedOrg = organizations.find((org) => String(org.id) === String(currentOrg?.id))
  return matchedOrg ?? organizations[0]
}
