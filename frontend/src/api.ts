import type {
  Customer,
  DashboardData,
  Lead,
  Order,
  OrderPayload,
  Product,
  VisionResult,
} from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || '请求失败')
  }

  return response.json() as Promise<T>
}

export function fetchDashboard() {
  return request<DashboardData>('/api/dashboard')
}

export function fetchCustomers() {
  return request<Customer[]>('/api/customers')
}

export function fetchProducts() {
  return request<Product[]>('/api/products')
}

export function fetchLeads() {
  return request<Lead[]>('/api/leads')
}

export function fetchOrders() {
  return request<Order[]>('/api/orders')
}

export function createOrder(payload: OrderPayload) {
  return request<Order>('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function extractVision(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/vision-extract', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || '识别失败')
  }

  return response.json() as Promise<VisionResult>
}
