const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

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

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || '请求失败')
  }

  return response.json()
}

export function fetchCopilotSummary() {
  return request('/api/copilot/summary')
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

export function fetchProducts() {
  return request('/api/products')
}

export function fetchContacts() {
  return request('/api/contacts')
}

export function fetchLeads() {
  return request('/api/leads')
}

export function fetchCases() {
  return request('/api/cases')
}

export function fetchTasks() {
  return request('/api/tasks')
}

export function fetchGoals() {
  return request('/api/goals')
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
