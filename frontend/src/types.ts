export type LeadStage =
  | 'new'
  | 'qualified'
  | 'proposal'
  | 'negotiation'
  | 'won'
  | 'lost'

export type OrderStatus = 'draft' | 'confirmed' | 'fulfilled'

export interface Customer {
  id: number
  name: string
  company: string
  industry: string
  city: string
  contact_person: string
  phone: string
  email: string
  source: string
  level: string
  created_at: string
}

export interface Product {
  id: number
  name: string
  sku: string
  category: string
  unit_price: number
  stock: number
}

export interface Lead {
  id: number
  title: string
  customer_name: string
  owner: string
  region: string
  expected_amount: number
  stage: LeadStage
  next_action: string
  due_date: string
  ai_assisted: boolean
  created_at: string
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  quantity: number
  unit_price: number
  line_total: number
}

export interface Order {
  id: number
  customer_id: number
  customer_name: string
  owner: string
  region: string
  currency: string
  status: OrderStatus
  order_date: string
  due_date: string
  notes: string
  created_by_ai: boolean
  ai_confidence_score: number
  total_amount: number
  created_at: string
  items: OrderItem[]
}

export interface DashboardMetric {
  label: string
  value: string
  hint: string
}

export interface RevenuePoint {
  month: string
  revenue: number
}

export interface DashboardData {
  metrics: DashboardMetric[]
  revenue_trend: RevenuePoint[]
  stage_distribution: Array<{ stage: string; count: number }>
  ai_orders_ratio: number
  urgent_leads: Lead[]
  recent_orders: Order[]
}

export interface VisionItem {
  product_name: string
  quantity: number
  unit_price: number
}

export interface VisionResult {
  customer_name: string
  company: string
  confidence: number
  summary: string
  items: VisionItem[]
  suggested_notes: string
}

export interface OrderItemPayload {
  product_id: number
  quantity: number
  unit_price: number
}

export interface OrderPayload {
  customer_id: number
  owner: string
  region: string
  currency: string
  status: OrderStatus
  order_date: string
  due_date: string
  notes: string
  created_by_ai: boolean
  ai_confidence_score: number
  items: OrderItemPayload[]
}
