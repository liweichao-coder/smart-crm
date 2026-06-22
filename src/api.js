const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
export const AUTH_STORAGE_KEY = 'smart-crm:auth-session'

function readStoredAuthToken() {
  if (typeof window === 'undefined') {
    return ''
  }
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) {
      return ''
    }
    return JSON.parse(raw)?.token ?? ''
  } catch {
    return ''
  }
}

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
  const token = readStoredAuthToken()
  const authHeader = token ? { Authorization: `Bearer ${token}` } : {}
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: isFormData
      ? {
          ...authHeader,
          ...(init?.headers ?? {}),
        }
      : {
          'Content-Type': 'application/json',
          ...authHeader,
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

function buildQueryString(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    query.set(key, String(value))
  })
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

export function fetchCopilotSummary() {
  return request('/api/copilot/summary')
}

export function fetchCopilotRecommendations(params) {
  return request(`/api/copilot/recommendations${buildQueryString(params)}`)
}

export function convertCopilotRecommendationToTask(recommendationId) {
  return request(`/api/copilot/recommendations/${recommendationId}/task`, {
    method: 'POST',
  })
}

export function login(payload) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function register(payload) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchCurrentUser() {
  return request('/api/auth/me')
}

export function fetchNotifications(params) {
  return request(`/api/notifications${buildQueryString(params)}`)
}

export function logout() {
  return request('/api/auth/logout', {
    method: 'POST',
  })
}

export function fetchAiAuditLogs(params) {
  return request(`/api/ai-audit-logs${buildQueryString(params)}`)
}

export function fetchBusinessAuditLogs(params) {
  return request(`/api/business-audit-logs${buildQueryString(params)}`)
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

export function fetchSalesPerformanceReport(params) {
  return request(`/api/reports/sales-performance${buildQueryString(params)}`)
}

export function fetchPermissionMatrix() {
  return request('/api/admin/permission-matrix')
}

export function fetchCustomers(params) {
  return request(`/api/customers${buildQueryString(params)}`)
}

export function fetchCustomerWorkspace(customerId) {
  return request(`/api/customers/${customerId}/workspace`)
}

export function createCustomerActivity(customerId, payload) {
  return request(`/api/customers/${customerId}/activities`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
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

export function fetchProducts(params) {
  return request(`/api/products${buildQueryString(params)}`)
}

export function createProduct(payload) {
  return request('/api/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProduct(productId, payload) {
  return request(`/api/products/${productId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteProduct(productId) {
  return request(`/api/products/${productId}`, {
    method: 'DELETE',
  })
}

export function fetchRestockAlerts() {
  return request('/api/inventory/restock-alerts')
}

export function fetchInventoryMovements(params) {
  return request(`/api/inventory/movements${buildQueryString(params)}`)
}

export function fetchOrderInventoryMovements(orderId) {
  return request(`/api/orders/${orderId}/inventory-movements`)
}

export function restockProduct(productId, payload) {
  return request(`/api/products/${productId}/restock`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchContacts(params) {
  return request(`/api/contacts${buildQueryString(params)}`)
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

export function fetchLeads(params) {
  return request(`/api/leads${buildQueryString(params)}`)
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

export function fetchCases(params) {
  return request(`/api/cases${buildQueryString(params)}`)
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

export function fetchTasks(params) {
  return request(`/api/tasks${buildQueryString(params)}`)
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

export function fetchGoals(params) {
  return request(`/api/goals${buildQueryString(params)}`)
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

export function fetchOrders(params) {
  return request(`/api/orders${buildQueryString(params)}`)
}

export function fetchOrderApprovals(params) {
  return request(`/api/order-approvals${buildQueryString(params)}`)
}

export function submitOrderApproval(orderId, payload) {
  return request(`/api/orders/${orderId}/approval-requests`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function decideOrderApproval(approvalId, payload) {
  return request(`/api/order-approvals/${approvalId}/decision`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function exportOrdersCsv() {
  const token = readStoredAuthToken()
  const response = await fetch(`${API_BASE_URL}/api/orders/export.csv`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) {
    const payload = await readResponsePayload(response)
    throw new Error(typeof payload === 'string' ? payload : payload?.detail ?? '订单导出失败')
  }
  return response.blob()
}

export function createOrder(payload) {
  return request('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateOrder(orderId, payload) {
  return request(`/api/orders/${orderId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
