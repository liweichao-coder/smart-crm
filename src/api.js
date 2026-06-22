const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function readResponsePayload(response) {
  const text = await response.text()
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

async function request(path, init) {
  const isFormData = typeof FormData !== 'undefined' && init?.body instanceof FormData
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: isFormData
      ? {
          ...(init?.headers ?? {}),
        }
      : {
          'Content-Type': 'application/json',
          ...(init?.headers ?? {}),
        },
    ...init,
  })

  const payload = await readResponsePayload(response)
  if (!response.ok) {
    throw new Error(typeof payload === 'string' ? payload : payload?.detail ?? '请求失败')
  }

  return payload
}

export function fetchCopilotSummary() {
  return request('/api/copilot/summary')
}

export function fetchAiAuditLogs() {
  return request('/api/ai-audit-logs')
}

export function generateFollowUp(leadId) {
  return request('/api/copilot/follow-up', {
    method: 'POST',
    body: JSON.stringify({ lead_id: leadId }),
  })
}

export function extractOrderFromFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/api/vision-extract', {
    method: 'POST',
    body: formData,
  })
}

export function fetchDashboard() {
  return request('/api/dashboard')
}

export function fetchCustomers() {
  return request('/api/customers')
}

export function createCustomer(payload) {
  return request('/api/customers', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateCustomer(customerId, payload) {
  return request(`/api/customers/${customerId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteCustomer(customerId) {
  return request(`/api/customers/${customerId}`, {
    method: 'DELETE',
  })
}

export function fetchProducts() {
  return request('/api/products')
}

export function fetchContacts() {
  return request('/api/contacts')
}

export function createContact(payload) {
  return request('/api/contacts', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateContact(contactId, payload) {
  return request(`/api/contacts/${contactId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteContact(contactId) {
  return request(`/api/contacts/${contactId}`, {
    method: 'DELETE',
  })
}

export function fetchLeads() {
  return request('/api/leads')
}

export function createLead(payload) {
  return request('/api/leads', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateLead(leadId, payload) {
  return request(`/api/leads/${leadId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteLead(leadId) {
  return request(`/api/leads/${leadId}`, {
    method: 'DELETE',
  })
}

export function fetchCases() {
  return request('/api/cases')
}

export function createCase(payload) {
  return request('/api/cases', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateCase(caseId, payload) {
  return request(`/api/cases/${caseId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteCase(caseId) {
  return request(`/api/cases/${caseId}`, {
    method: 'DELETE',
  })
}

export function fetchTasks() {
  return request('/api/tasks')
}

export function createTask(payload) {
  return request('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateTask(taskId, payload) {
  return request(`/api/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteTask(taskId) {
  return request(`/api/tasks/${taskId}`, {
    method: 'DELETE',
  })
}

export function fetchGoals() {
  return request('/api/goals')
}

export function createGoal(payload) {
  return request('/api/goals', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateGoal(goalId, payload) {
  return request(`/api/goals/${goalId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteGoal(goalId) {
  return request(`/api/goals/${goalId}`, {
    method: 'DELETE',
  })
}

export function fetchOrders() {
  return request('/api/orders')
}

export function createOrder(payload) {
  return request('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
