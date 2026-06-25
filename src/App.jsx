import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bell,
  Bot,
  Briefcase,
  Building2,
  Calendar,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  ClipboardList,
  Download,
  Filter,
  FileText,
  Flame,
  LayoutDashboard,
  LayoutGrid,
  LayoutList,
  KeyRound,
  LogOut,
  Menu,
  Package,
  PanelLeftClose,
  Pencil,
  Phone,
  Plus,
  Save,
  Search,
  Shield,
  Sparkles,
  RefreshCw,
  Target,
  TrendingUp,
  Trash2,
  Trophy,
  UploadCloud,
  Users,
  X,
  Building,
} from 'lucide-react'
import {
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useOutletContext,
  useParams,
  useSearchParams,
} from 'react-router-dom'
import smartCrmLogo from './assets/smart-crm-logo.png'
import {
  AUTH_STORAGE_KEY,
  assignOrderApproval,
  askCopilot,
  changeAuthPassword,
  fetchAuthSessions,
  fetchCases,
  fetchAuthAuditLogs,
  fetchAiAuditLogs,
  fetchAiQualityReport,
  fetchApprovalPerformanceReport,
  fetchBusinessAuditLogs,
  fetchCaptureDrafts,
  fetchContacts,
  fetchConsistencyChecks,
  fetchCopilotRecommendations,
  fetchCopilotSummary,
  fetchCurrentUser,
  fetchNotifications,
  convertCopilotRecommendationToTask,
  convertCustomerActivityToTask,
  submitCopilotRecommendationFeedback,
  createCase,
  createContact,
  createCustomerActivity,
  createCustomer,
  createGoal,
  createLead,
  createOrder,
  createProduct,
  createReportSnapshot,
  createTeamMember,
  createTask,
  decideOrderApproval,
  deleteCase,
  deleteContact,
  deleteCustomer,
  deleteGoal,
  deleteLead,
  deleteProduct,
  deleteReportSnapshot,
  deleteTask,
  exportAuthAuditLogsCsv,
  exportAiAuditLogsCsv,
  exportBusinessAuditLogsCsv,
  exportOrdersCsv,
  fetchCustomers,
  fetchCustomerWorkspace,
  fetchDashboard,
  fetchSalesPerformanceReport,
  fetchPermissionMatrix,
  fetchTeamMembers,
  fetchGoals,
  fetchInventoryMovements,
  fetchLeads,
  fetchOrderInventoryMovements,
  fetchOrderApprovals,
  fetchOrders,
  fetchProducts,
  fetchReportSnapshots,
  fetchRestockAlerts,
  fetchTasks,
  fetchUserPreference,
  extractOrderFromFile,
  generateOrderDraft,
  generateFollowUp,
  login,
  logout,
  markAllNotificationsRead,
  register,
  restockProduct,
  revokeAuthSession,
  revokeOtherAuthSessions,
  remindOrderApproval,
  saveUserPreference,
  submitOrderApproval,
  updateAuthProfile,
  updateCaptureDraft,
  updateCase,
  updateContact,
  updateCustomer,
  updateGoal,
  updateLead,
  updateLeadStage,
  updateNotificationState,
  updateOrder,
  updateProduct,
  updateTeamMember,
  updateTask,
} from './api.js'
import { buildOrderPayloadFromCapture } from './captureUtils.js'
import { ORDER_FILTERS, filterOrders, getStockTone, pickLowStockProducts, summarizeOrders } from './orderUtils.js'
import { toDraftOwner } from './ownerUtils.js'
import {
  buildCasePayload,
  buildContactPayload,
  buildCustomerPayload,
  buildGoalPayload,
  buildLeadPayload,
  normalizeLeadStage,
  buildOrderUpdatePayload,
  buildProductPayload,
  buildTaskPayload,
  buildTeamMemberPayload,
} from './payloadUtils.js'
import {
  buildBulkEditPatch,
  buildCsvContent,
  createBulkEditDraft,
  createCsvFilename,
  createDraftFromColumns,
  normalizeSortState,
  normalizeVisibleColumnKeys,
  parseListSearchState,
  patchListSearchParams,
  sortRecordsByColumn,
  summarizeBulkSettledResults,
  toggleSelectedKey,
  toggleVisibleSelection,
} from './resourceUtils.js'
import { getSessionOrganizations, resolveSelectedOrg } from './sessionUtils.js'

const STORAGE_KEY = 'huahenuancrm:selected-org'

const navItems = [
  { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard, title: 'Dashboard | 深大 AI CRM', permission: 'dashboard:read' },
  { path: '/reports', label: '销售报表', icon: BarChart3, title: 'Reports | 深大 AI CRM', permission: 'reports:read' },
  { path: '/team', label: '团队成员', icon: Users, title: 'Team | 深大 AI CRM', permission: 'team:manage' },
  { path: '/copilot', label: 'AI 副驾', icon: Bot, title: 'AI Copilot | 深大 AI CRM', permission: 'ai:use' },
  { path: '/auth-audit', label: '认证审计', icon: KeyRound, title: 'Auth Audit | 深大 AI CRM', permission: 'audit:read' },
  { path: '/ai-audit', label: 'AI 审计', icon: Shield, title: 'AI Audit | 深大 AI CRM', permission: 'audit:read' },
  { path: '/business-audit', label: '操作审计', icon: ClipboardList, title: 'Business Audit | 深大 AI CRM', permission: 'audit:read' },
  { path: '/permissions', label: '权限矩阵', icon: KeyRound, title: 'Permissions | 深大 AI CRM', permission: 'permissions:read' },
  { path: '/capture', label: '智能录单', icon: FileText, title: 'AI Capture | 深大 AI CRM', permission: 'ai:use' },
  { path: '/orders', label: '订单', icon: Activity, title: 'Orders | 深大 AI CRM', permission: 'order:manage' },
  { path: '/products', label: '商品', icon: Package, title: 'Products | 深大 AI CRM', permission: 'catalog:manage' },
  { path: '/leads', label: '线索', icon: Target, title: 'Leads | 深大 AI CRM', permission: 'crm:read' },
  { path: '/contacts', label: '联系人', icon: Users, title: 'Contacts | 深大 AI CRM', permission: 'crm:read' },
  { path: '/accounts', label: '客户', icon: Building2, title: 'Accounts | 深大 AI CRM', permission: 'crm:read' },
  { path: '/opportunities', label: '商机', icon: Sparkles, title: 'Opportunities | 深大 AI CRM', permission: 'crm:read' },
  { path: '/goals', label: '销售目标', icon: Trophy, title: 'Sales Goals | 深大 AI CRM', permission: 'crm:read' },
  { path: '/cases', label: '工单', icon: Briefcase, title: 'Cases | 深大 AI CRM', permission: 'crm:read' },
  { path: '/tasks', label: '任务', icon: CheckSquare, title: 'Tasks | 深大 AI CRM', permission: 'crm:read' },
]

const pageItems = [...navItems, { path: '/profile', label: '个人主页', title: 'Profile | 深大 AI CRM' }]

const userProfile = {
  id: null,
  name: 'ZRC 673468472',
  email: 'zrc673468472@gmail.com',
  phone: '+86 186 0000 2048',
  role: '管理员',
  position: 'CRM 运营管理员',
  department: '客户增长中心',
  location: '上海 · 浦东',
  status: 'active',
  joinDate: '2024 年 2 月 18 日',
  permissions: ['*'],
  dataScope: 'all',
}

function BrandMark() {
  return <img className="crm-brand-mark" src={smartCrmLogo} alt="" aria-hidden="true" />
}

const statusToneMap = {
  active: 'success',
  inactive: 'neutral',
  nurturing: 'neutral',
  proposal: 'accent',
  won: 'success',
  overdue: 'danger',
  today: 'warning',
  week: 'info',
  new: 'accent',
  hot: 'danger',
  warm: 'warning',
  cold: 'neutral',
  open: 'accent',
  working: 'warning',
  closed: 'neutral',
  draft: 'warning',
  confirmed: 'accent',
  fulfilled: 'success',
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  llm: 'success',
  fallback: 'warning',
}

const dataScopeLabelMap = {
  all: '全量数据',
  own: '本人数据',
}

const teamRoleOptions = ['管理员', '销售经理', '销售', '支持', '审计员']

const teamStatusOptions = ['active', 'inactive']

const teamStatusLabelMap = {
  active: '启用',
  inactive: '停用',
}

const teamMemberExportColumns = [
  { key: 'fullName', label: '姓名' },
  { key: 'email', label: '邮箱' },
  { key: 'phone', label: '手机' },
  { key: 'role', label: '角色' },
  { key: 'status', label: '状态' },
  { key: 'department', label: '部门' },
  { key: 'position', label: '岗位' },
]

const boardToneMap = {
  New: 'new',
  Qualified: 'qualified',
  Contacted: 'contacted',
  Proposal: 'proposal',
  Negotiation: 'negotiation',
  Won: 'won',
  Prospecting: 'new',
  Qualification: 'qualified',
  Review: 'proposal',
  Open: 'qualified',
  Pending: 'negotiation',
  Resolved: 'won',
  Lost: 'neutral',
}

const stageLabelMap = {
  new: 'New',
  contacted: 'Contacted',
  qualified: 'Qualified',
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  won: 'Won',
  lost: 'Lost',
}
const leadPipelineStages = Object.entries(stageLabelMap).map(([value, label]) => ({ value, label }))
const leadPipelineLabels = leadPipelineStages.map((stage) => stage.label)

const dashboardStageMeta = {
  new: { label: '新线索', tone: 'new' },
  contacted: { label: '已联系', tone: 'contacted' },
  qualified: { label: '资格确认', tone: 'qualified' },
  proposal: { label: '方案提案', tone: 'proposal' },
  negotiation: { label: '商务谈判', tone: 'negotiation' },
  won: { label: '已成交', tone: 'won' },
  lost: { label: '已丢单', tone: 'neutral' },
}

const dashboardMetricMeta = {
  本月订单额: { icon: TrendingUp, tone: 'accent' },
  'AI参与订单': { icon: Sparkles, tone: 'proposal' },
  'AI 参与订单': { icon: Sparkles, tone: 'proposal' },
  在跟进商机: { icon: Target, tone: 'qualified' },
  客户总数: { icon: Users, tone: 'won' },
  订单收入: { icon: BarChart3, tone: 'accent' },
  平均客单价: { icon: TrendingUp, tone: 'qualified' },
  'AI 收入占比': { icon: Sparkles, tone: 'proposal' },
  在管商机额: { icon: Target, tone: 'negotiation' },
  赢单商机额: { icon: Trophy, tone: 'won' },
  库存风险: { icon: Package, tone: 'warning' },
  审批总量: { icon: ClipboardList, tone: 'qualified' },
  待审批: { icon: Calendar, tone: 'warning' },
  高风险审批: { icon: Shield, tone: 'danger' },
  审批通过率: { icon: CheckSquare, tone: 'won' },
  平均处理时长: { icon: Activity, tone: 'accent' },
  'SLA 逾期率': { icon: Flame, tone: 'danger' },
  'AI 调用总量': { icon: Activity, tone: 'accent' },
  'LLM 成功率': { icon: Sparkles, tone: 'won' },
  兜底率: { icon: Shield, tone: 'warning' },
  平均耗时: { icon: Flame, tone: 'qualified' },
  场景覆盖: { icon: Bot, tone: 'proposal' },
  推荐转任务率: { icon: CheckSquare, tone: 'won' },
  人工好评率: { icon: Trophy, tone: 'won' },
}

const orderStatusLabelMap = {
  draft: '草稿',
  confirmed: '已确认',
  fulfilled: '已履约',
}

const approvalStatusLabelMap = {
  pending: '待审批',
  approved: '已通过',
  rejected: '已驳回',
}

const approvalRiskLabelMap = {
  critical: '关键风险',
  high: '高风险',
  medium: '中风险',
  low: '低风险',
}

const approvalRiskToneMap = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'neutral',
}

const approvalSlaLabelMap = {
  overdue: 'SLA 已逾期',
  due_soon: 'SLA 临近',
  on_track: 'SLA 正常',
  closed: 'SLA 已关闭',
  unset: 'SLA 未设置',
}

const approvalSlaToneMap = {
  overdue: 'danger',
  due_soon: 'warning',
  on_track: 'success',
  closed: 'neutral',
  unset: 'neutral',
}

const inventorySourceLabelMap = {
  manual_restock: '人工补货',
  order_deduction: '订单扣减',
  seed_order_deduction: '演示订单扣减',
  order_adjustment: '订单调整',
}

const aiOperationLabelMap = {
  copilot_summary: '副驾摘要',
  copilot_follow_up: '跟进话术',
  copilot_ask: '经营问答',
  copilot_order_draft: '订单草稿',
  vision_extract: '智能录单',
  customer_account_plan: '客户经营计划',
}

const copilotFeedbackLabelMap = {
  accepted: '已采纳',
  helpful: '有帮助',
  not_helpful: '不匹配',
  dismissed: '已忽略',
}

const authAuditEventLabelMap = {
  login: '登录',
  register: '注册',
  profile_update: '资料更新',
  password_change: '密码修改',
  logout: '退出登录',
  session_revoke: '会话撤销',
  team_create: '团队成员创建',
  team_update: '团队成员更新',
}

const authAuditStatusLabelMap = {
  success: '成功',
  failed: '失败',
  blocked: '临时锁定',
}

const authSessionStatusLabelMap = {
  active: '活跃',
  expired: '已过期',
  revoked: '已撤销',
}

const authSessionStatusToneMap = {
  active: 'success',
  expired: 'warning',
  revoked: 'neutral',
}

const businessActionLabelMap = {
  create: '新建',
  update: '更新',
  delete: '删除',
  convert: '转任务',
  feedback: '人工反馈',
  restock: '补货',
  submit_approval: '提交审批',
  remind_approval: '审批催办',
  assign_approval: '审批转派',
  approve: '审批通过',
  reject: '审批驳回',
}

const businessEntityLabelMap = {
  customer: '客户',
  contact: '联系人',
  lead: '线索/商机',
  case: '工单',
  task: '任务',
  goal: '销售目标',
  customer_activity: '客户互动',
  copilot_recommendation: 'Copilot 推荐',
  product: '商品',
  order: '订单',
  order_approval: '订单审批',
  report_snapshot: '报表快照',
  crm: 'CRM 上下文',
}

function mapStageLabel(stage) {
  return stageLabelMap[stage] ?? stage
}

function normalizeStage(stage) {
  const matchedEntry = Object.entries(stageLabelMap).find(([, label]) => label === stage)
  return matchedEntry?.[0] ?? stage
}

function buildDashboardStages(leads) {
  const buckets = Object.keys(dashboardStageMeta).map((stage) => ({
    stage,
    ...dashboardStageMeta[stage],
    amount: 0,
    count: 0,
  }))
  const bucketMap = new Map(buckets.map((bucket) => [bucket.stage, bucket]))

  leads.forEach((lead) => {
    const stage = normalizeStage(lead.stage)
    const bucket = bucketMap.get(stage)
    if (!bucket) {
      return
    }
    bucket.count += 1
    bucket.amount += Number(lead.expected_amount ?? lead.amount ?? 0)
  })

  const maxAmount = Math.max(...buckets.map((bucket) => bucket.amount), 1)
  return buckets
    .filter((bucket) => bucket.count > 0 || bucket.stage !== 'lost')
    .map((bucket) => ({
      ...bucket,
      progress: Math.max(8, Math.round((bucket.amount / maxAmount) * 100)),
    }))
}

function buildDashboardMetrics(dashboard) {
  if (!dashboard?.metrics?.length) {
    return []
  }

  return dashboard.metrics.map((metric) => {
    const meta = dashboardMetricMeta[metric.label] ?? { icon: Activity, tone: 'neutral' }
    return {
      ...metric,
      icon: meta.icon,
      tone: meta.tone,
    }
  })
}

function buildDashboardFocus({ dashboard, leads, tasks }) {
  const todayTasks = tasks.filter((task) => task.status === 'today').length
  const overdueTasks = tasks.filter((task) => task.status === 'overdue').length
  const urgentLeads = dashboard?.urgent_leads?.length ?? leads.filter((lead) => normalizeStage(lead.stage) !== 'won' && normalizeStage(lead.stage) !== 'lost').slice(0, 5).length
  const forecastAmount = leads
    .filter((lead) => !['won', 'lost'].includes(normalizeStage(lead.stage)))
    .reduce((total, lead) => total + Number(lead.expected_amount ?? 0), 0)

  return [
    { label: '今天任务', value: todayTasks, href: '/tasks', icon: Calendar },
    { label: '逾期任务', value: overdueTasks, href: '/tasks', icon: Flame },
    { label: '需要跟进', value: urgentLeads, href: '/leads', icon: Phone },
    { label: '未结预测', value: formatCompactCurrency(forecastAmount), href: '/opportunities', icon: Sparkles },
  ]
}

function buildHotLeads(leads) {
  return [...leads]
    .filter((lead) => !['won', 'lost'].includes(normalizeStage(lead.stage)))
    .sort((first, second) => {
      const scoreA = Number(first.expected_amount ?? 0) + (first.ai_assisted ? 50000 : 0)
      const scoreB = Number(second.expected_amount ?? 0) + (second.ai_assisted ? 50000 : 0)
      return scoreB - scoreA
    })
    .slice(0, 5)
    .map(mapLeadRecord)
}

function buildRecentActivities(dashboard) {
  const orderActivities = (dashboard?.recent_orders ?? []).slice(0, 4).map((order) => ({
    id: `order-${order.id}`,
    title: `${order.customer_name} 订单已更新`,
    description: `${order.owner} 创建 ${formatCurrency(order.total_amount)} 订单，状态为 ${order.status}。`,
    time: order.order_date,
    icon: Activity,
  }))

  const leadActivities = (dashboard?.urgent_leads ?? []).slice(0, 2).map((lead) => ({
    id: `lead-${lead.id}`,
    title: `${lead.customer_name} 需要跟进`,
    description: `${lead.title} 下一步：${lead.next_action}`,
    time: lead.due_date,
    icon: Flame,
  }))

  return [...orderActivities, ...leadActivities].slice(0, 5)
}

function toDraftText(value, fallback = '') {
  const text = String(value ?? '').trim()
  return text || fallback
}

function toDraftNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

function normalizePaginatedPayload(payload, fallbackPage = 1, fallbackPerPage = 20) {
  const items = Array.isArray(payload) ? payload : payload?.items ?? []
  return {
    items,
    total: Array.isArray(payload) ? items.length : payload?.total ?? items.length,
    page: Array.isArray(payload) ? 1 : payload?.page ?? fallbackPage,
    per_page: Array.isArray(payload) ? items.length : payload?.per_page ?? fallbackPerPage,
    pages: Array.isArray(payload) ? 1 : payload?.pages ?? 1,
    has_next: Array.isArray(payload) ? false : Boolean(payload?.has_next),
    has_previous: Array.isArray(payload) ? false : Boolean(payload?.has_previous),
  }
}

function downloadResourceCsv(title, records, columns) {
  if (!records.length) {
    return
  }
  const csvContent = buildCsvContent(records, columns)
  const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = createCsvFilename(title)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function createTeamMemberDraft(member = null) {
  return {
    fullName: member?.fullName ?? '',
    email: member?.email ?? '',
    phone: member?.phone ?? '',
    role: member?.role ?? '销售',
    position: member?.position ?? '销售顾问',
    department: member?.department ?? '客户增长中心',
    location: member?.location ?? '深圳 · 南山',
    status: member?.status ?? 'active',
    password: '',
    confirmPassword: '',
  }
}

function createProfileDraft(profile = userProfile) {
  return {
    fullName: profile.name ?? '',
    email: profile.email ?? '',
    phone: profile.phone ?? '',
    position: profile.position ?? '',
    department: profile.department ?? '',
    location: profile.location ?? '',
  }
}

function buildProfilePayload(draft) {
  return {
    full_name: toDraftText(draft.fullName),
    email: toDraftText(draft.email),
    phone: toDraftText(draft.phone),
    position: toDraftText(draft.position),
    department: toDraftText(draft.department),
    location: toDraftText(draft.location),
  }
}

function createPasswordDraft() {
  return {
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  }
}

function buildPasswordPayload(draft) {
  return {
    current_password: draft.currentPassword,
    new_password: draft.newPassword,
    confirm_password: draft.confirmPassword,
  }
}

function buildOrderDraft(order, ownerFallback = userProfile.name) {
  return {
    owner: order?.owner ?? ownerFallback,
    region: order?.region ?? '',
    status: order?.status ?? '',
    dueDate: order?.due_date ?? '',
    notes: order?.notes ?? '',
    items: (order?.items ?? []).map((item, index) => ({
      draftId: `existing-${item.id ?? index}`,
      productId: String(item.product_id ?? ''),
      quantity: String(item.quantity ?? 1),
      unitPrice: String(item.unit_price ?? 1),
    })),
  }
}

function buildOrderLineDraft(product) {
  return {
    draftId: `new-${product?.id ?? 'product'}-${Date.now()}`,
    productId: String(product?.id ?? ''),
    quantity: '1',
    unitPrice: String(product?.unit_price ?? 1),
  }
}

function dateOffsetString(days = 0) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

function buildOrderPayloadFromCopilotDraft(draft, customer, ownerFallback = userProfile.name) {
  return {
    customer_id: draft.customer_id,
    owner: toDraftOwner(customer?.owner, ownerFallback),
    region: '华南',
    currency: 'CNY',
    status: 'draft',
    order_date: dateOffsetString(0),
    due_date: dateOffsetString(7),
    notes: [draft.suggested_notes, draft.llm_summary].filter(Boolean).join('\n'),
    created_by_ai: true,
    ai_confidence_score: draft.fallback_used ? 0.74 : 0.9,
    items: (draft.items ?? []).map((item) => ({
      product_id: item.product_id,
      quantity: Math.max(1, Math.round(Number(item.quantity) || 1)),
      unit_price: Math.max(0.01, Number(item.unit_price) || 1),
    })),
  }
}

function calculateOrderLineTotal(item) {
  return Math.max(1, Math.round(toDraftNumber(item.quantity, 1))) * Math.max(0.01, toDraftNumber(item.unitPrice, 1))
}

function buildDraftFromRecord(columns, record, workflowField) {
  const draft = columns.reduce(
    (nextDraft, column) => ({
      ...nextDraft,
      [column.key]: record[column.key] ?? '',
    }),
    workflowField ? { [workflowField.key]: record[workflowField.key] ?? workflowField.value } : {},
  )
  return draft
}

function mapCustomerRecord(customer) {
  return {
    id: customer.id,
    name: customer.company,
    industry: customer.industry,
    contactPerson: customer.contact_person,
    phone: customer.phone,
    email: customer.email,
    city: customer.city,
    source: customer.source,
    level: customer.level,
    owner: customer.owner ?? customer.contact_person,
    revenue: customer.annual_revenue,
    status: customer.status,
  }
}

function mapProductRecord(product) {
  return {
    id: product.id,
    name: product.name,
    sku: product.sku,
    category: product.category,
    unitPrice: product.unit_price,
    stock: product.stock,
  }
}

function mapContactRecord(contact) {
  return {
    id: contact.id,
    name: contact.name,
    company: contact.company,
    role: contact.role,
    email: contact.email,
    phone: contact.phone,
    owner: contact.owner,
    status: contact.status,
  }
}

function mapLeadRecord(lead) {
  return {
    id: lead.id,
    name: lead.title,
    company: lead.customer_name,
    owner: lead.owner,
    nextStep: lead.next_action,
    rating: lead.stage === 'lost' ? 'cold' : lead.ai_assisted ? 'hot' : 'warm',
    stage: mapStageLabel(lead.stage),
  }
}

function mapOpportunityRecord(lead) {
  return {
    id: lead.id,
    name: lead.title,
    account: lead.customer_name,
    owner: lead.owner,
    amount: lead.expected_amount,
    closeDate: lead.due_date,
    stage: mapStageLabel(lead.stage),
  }
}

function mapCaseRecord(supportCase) {
  return {
    id: supportCase.id,
    title: supportCase.title,
    account: supportCase.account,
    owner: supportCase.owner,
    priority: supportCase.priority,
    status: supportCase.status,
    statusLabel: supportCase.status_label,
  }
}

function mapTaskRecord(task) {
  return {
    id: task.id,
    title: task.title,
    description: task.description,
    owner: task.owner,
    dueDate: task.due_date,
    priority: task.priority,
    status: task.status,
    statusLabel: task.status_label,
  }
}

function mapGoalRecord(goal) {
  return {
    id: goal.id,
    name: goal.name,
    period: goal.period,
    owner: goal.owner,
    current: goal.current,
    target: goal.target,
    progress: goal.progress,
    note: goal.note,
  }
}

function mapTeamMemberRecord(member) {
  return {
    id: member.id,
    fullName: member.full_name,
    email: member.email,
    phone: member.phone,
    role: member.role,
    status: member.status,
    dataScope: member.data_scope,
    position: member.position,
    department: member.department,
    location: member.location,
    permissions: member.permissions ?? [],
    lastLoginAt: member.last_login_at,
    createdAt: member.created_at,
  }
}

function useRemoteRecords(fetcher, mapper) {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    fetcher()
      .then((payload) => {
        if (mounted) {
          const items = Array.isArray(payload) ? payload : payload?.items ?? []
          setRecords(items.map(mapper))
          setError('')
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || '后端数据同步失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [fetcher, mapper])

  return { records, loading, error }
}

function useResourceUrlState({
  tabKeys = [],
  defaultTab = tabKeys[0] ?? '',
  viewKeys = [],
  defaultView = viewKeys[0] ?? '',
  selectedKey = '',
  preferenceNamespace = '',
} = {}) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [preferenceStatus, setPreferenceStatus] = useState(preferenceNamespace ? '加载偏好' : '')
  const [preferenceValue, setPreferenceValue] = useState({})
  const saveTimerRef = useRef(null)
  const state = parseListSearchState(searchParams, {
    tabKeys,
    defaultTab,
    viewKeys,
    defaultView,
    selectedKey,
  })

  useEffect(() => {
    if (!preferenceNamespace) {
      return undefined
    }
    let mounted = true
    setPreferenceStatus('加载偏好')
    fetchUserPreference(preferenceNamespace)
      .then((preference) => {
        if (!mounted) {
          return
        }
        const value = preference?.value ?? {}
        setPreferenceValue(value)
        const hasSavedState = Boolean(value.query || value.activeTab || value.tab || value.view)
        if (hasSavedState) {
          setSearchParams(
            (currentParams) => {
              const hasExplicitState = currentParams.has('q') || currentParams.has('tab') || currentParams.has('view')
              if (hasExplicitState) {
                return currentParams
              }
              return patchListSearchParams(currentParams, {
                q: value.query ?? '',
                tab: value.activeTab ?? value.tab ?? defaultTab,
                view: value.view ?? defaultView,
              }, {
                q: '',
                tab: defaultTab,
                view: defaultView,
              })
            },
            { replace: true },
          )
        }
        setPreferenceStatus(hasSavedState ? '已恢复偏好' : '偏好已就绪')
      })
      .catch(() => {
        if (mounted) {
          setPreferenceStatus('偏好未同步')
        }
      })

    return () => {
      mounted = false
    }
  }, [defaultTab, defaultView, preferenceNamespace, setSearchParams])

  useEffect(() => () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }
  }, [])

  const schedulePreferenceSave = (updates) => {
    if (!preferenceNamespace) {
      return
    }
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }
    const nextPreference = {
      ...preferenceValue,
      query: updates.q ?? state.query,
      activeTab: updates.tab ?? state.tab,
      view: updates.view ?? state.view,
    }
    setPreferenceValue(nextPreference)
    setPreferenceStatus('保存偏好')
    saveTimerRef.current = setTimeout(() => {
      saveUserPreference(preferenceNamespace, nextPreference)
        .then(() => setPreferenceStatus('偏好已保存'))
        .catch(() => setPreferenceStatus('偏好保存失败'))
    }, 350)
  }

  const updateUrlState = (updates, { persist = true } = {}) => {
    setSearchParams(
      (currentParams) => patchListSearchParams(currentParams, updates, {
        q: '',
        tab: defaultTab,
        view: defaultView,
      }),
      { replace: true },
    )
    if (persist) {
      schedulePreferenceSave(updates)
    }
  }

  const savePreferencePatch = (patch) => {
    if (!preferenceNamespace) {
      return
    }
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }
    const nextPreference = {
      ...preferenceValue,
      query: state.query,
      activeTab: state.tab,
      view: state.view,
      ...patch,
    }
    setPreferenceValue(nextPreference)
    setPreferenceStatus('保存偏好')
    saveTimerRef.current = setTimeout(() => {
      saveUserPreference(preferenceNamespace, nextPreference)
        .then(() => setPreferenceStatus('偏好已保存'))
        .catch(() => setPreferenceStatus('偏好保存失败'))
    }, 350)
  }

  return {
    query: state.query,
    activeTab: state.tab,
    view: state.view,
    selectedId: state.selectedId,
    preferenceStatus,
    preferenceValue,
    savePreferencePatch,
    setQuery: (query) => updateUrlState({ q: query }),
    setActiveTab: (tab) => updateUrlState({ tab }),
    setView: (view) => updateUrlState({ view }),
    setSelectedId: (id) => updateUrlState(selectedKey ? { [selectedKey]: id } : {}, { persist: false }),
  }
}

function RequireAuth({ authSession, children }) {
  if (!authSession?.token) {
    return <Navigate replace to="/login" />
  }
  return children
}

function hasClientPermission(authSession, permission) {
  if (!permission) {
    return true
  }
  const permissions = authSession?.user?.permissions ?? []
  return permissions.includes('*') || permissions.includes(permission)
}

function App() {
  const [authSession, setAuthSession] = useState(loadStoredAuthSession)
  const [authChecked, setAuthChecked] = useState(() => !loadStoredAuthSession()?.token)

  useEffect(() => {
    const storedSession = loadStoredAuthSession()
    if (!storedSession?.token) {
      return
    }
    let mounted = true
    fetchCurrentUser()
      .then((payload) => {
        if (!mounted) {
          return
        }
        const refreshedSession = {
          ...storedSession,
          expires_at: payload.expires_at,
          user: payload.user,
          organizations: payload.organizations,
        }
        persistAuthSession(refreshedSession)
        setAuthSession(refreshedSession)
      })
      .catch(() => {
        if (mounted) {
          clearStoredAuthSession()
          setAuthSession(null)
        }
      })
      .finally(() => {
        if (mounted) {
          setAuthChecked(true)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  const handleAuthSession = (session) => {
    persistAuthSession(session)
    setAuthSession(session)
  }

  const handleSessionRefresh = (payload) => {
    setAuthSession((currentSession) => {
      if (!currentSession) {
        return currentSession
      }
      const refreshedSession = {
        ...currentSession,
        expires_at: payload.expires_at ?? currentSession.expires_at,
        user: payload.user ?? currentSession.user,
        organizations: payload.organizations ?? currentSession.organizations,
      }
      persistAuthSession(refreshedSession)
      return refreshedSession
    })
  }

  const handleLogout = async () => {
    try {
      if (authSession?.token) {
        await logout()
      }
    } catch {
      // The local session should still be cleared if the server token is already expired.
    }
    clearStoredAuthSession()
    setAuthSession(null)
  }

  if (!authChecked) {
    return (
      <div className="crm-auth-page">
        <main className="crm-auth-shell crm-auth-shell--compact">
          <section className="crm-auth-panel">
            <div className="crm-auth-brand crm-auth-brand--panel">
              <BrandMark />
              <div>
                <strong>深大 AI CRM</strong>
                <span>正在校验登录状态</span>
              </div>
            </div>
          </section>
        </main>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage onLogin={handleAuthSession} />} />
      <Route path="/register" element={<RegisterPage onLogin={handleAuthSession} />} />
      <Route
        path="/org"
        element={(
          <RequireAuth authSession={authSession}>
            <OrgSelectionPage authSession={authSession} onLogout={handleLogout} />
          </RequireAuth>
        )}
      />
      <Route path="/" element={<Navigate replace to={authSession?.token ? '/dashboard' : '/login'} />} />
      <Route
        element={(
          <RequireAuth authSession={authSession}>
            <AppShell authSession={authSession} onLogout={handleLogout} onSessionRefresh={handleSessionRefresh} />
          </RequireAuth>
        )}
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/team" element={<TeamMembersPage />} />
        <Route path="/copilot" element={<CopilotPage />} />
        <Route path="/auth-audit" element={<AuthAuditPage />} />
        <Route path="/ai-audit" element={<AiAuditPage />} />
        <Route path="/business-audit" element={<BusinessAuditPage />} />
        <Route path="/permissions" element={<PermissionMatrixPage />} />
        <Route path="/capture" element={<CapturePage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/accounts/:customerId" element={<CustomerWorkspacePage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/opportunities" element={<OpportunitiesPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/goals" element={<GoalsPage />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/login" />} />
    </Routes>
  )
}

function ProductsPage() {
  const { records, loading, error } = useRemoteRecords(fetchProducts, mapProductRecord)

  return (
    <TableResourcePage
      title="商品"
      subtitle="维护 AI 录单、订单明细和库存补货共用的商品目录。"
      icon={Package}
      records={records}
      loading={loading}
      error={error}
      onCreateRecord={(draft) => createProduct(buildProductPayload(draft)).then(mapProductRecord)}
      onUpdateRecord={(id, draft) => updateProduct(id, buildProductPayload(draft)).then(mapProductRecord)}
      onDeleteRecord={deleteProduct}
      createLabel="新建商品"
      columns={[
        { key: 'name', label: '商品名称', defaultValue: '' },
        { key: 'sku', label: 'SKU', defaultValue: '' },
        { key: 'category', label: '分类', inputType: 'select', options: ['硬件', '软件', '服务'], defaultValue: '软件' },
        { key: 'unitPrice', label: '单价', format: 'currency' },
        { key: 'stock', label: '库存', inputType: 'number', defaultValue: 0 },
      ]}
      tabs={[
        { key: 'all', label: '全部' },
        { key: 'hardware', label: '硬件', predicate: (item) => item.category === '硬件' },
        { key: 'software', label: '软件', predicate: (item) => item.category === '软件' },
        { key: 'service', label: '服务', predicate: (item) => item.category === '服务' },
        { key: 'low', label: '低库存', predicate: (item) => Number(item.stock) <= 300 },
      ]}
    />
  )
}

function TeamMembersPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingMember, setEditingMember] = useState(null)
  const [draft, setDraft] = useState(() => createTeamMemberDraft())
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')
  const searchInputRef = useRef(null)

  const loadMembers = async () => {
    setLoading(true)
    try {
      const payload = await fetchTeamMembers()
      const items = Array.isArray(payload) ? payload : payload.items ?? []
      setMembers(items.map(mapTeamMemberRecord))
      setError('')
    } catch (requestError) {
      setError(requestError.message || '团队成员加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMembers()
  }, [])

  const tabs = useMemo(() => [
    { key: 'all', label: '全部', predicate: () => true },
    { key: 'active', label: '启用', predicate: (member) => member.status === 'active' },
    { key: 'manager', label: '管理角色', predicate: (member) => ['管理员', '销售经理'].includes(member.role) },
    { key: 'sales', label: '销售', predicate: (member) => member.role === '销售' },
  ], [])
  const { query, setQuery, activeTab, setActiveTab } = useResourceUrlState({
    tabKeys: tabs.map((tab) => tab.key),
    defaultTab: 'all',
  })

  const visibleMembers = useMemo(() => {
    const tab = tabs.find((item) => item.key === activeTab)
    return members.filter((member) => {
      if (tab?.predicate && !tab.predicate(member)) {
        return false
      }
      if (!query.trim()) {
        return true
      }
      const keyword = query.toLowerCase()
      return [member.fullName, member.email, member.phone, member.role, member.position, member.department, member.location, member.status]
        .some((value) => String(value ?? '').toLowerCase().includes(keyword))
    })
  }, [activeTab, members, query, tabs])

  const handleOpenCreate = () => {
    setEditingMember(null)
    setDraft(createTeamMemberDraft())
    setFormError('')
    setModalOpen(true)
  }

  const handleOpenEdit = (member) => {
    setEditingMember(member)
    setDraft(createTeamMemberDraft(member))
    setFormError('')
    setModalOpen(true)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setFormError('')
    try {
      const payload = buildTeamMemberPayload(draft, Boolean(editingMember))
      const saved = editingMember
        ? await updateTeamMember(editingMember.id, payload)
        : await createTeamMember(payload)
      const mapped = mapTeamMemberRecord(saved)
      setMembers((currentMembers) => (
        editingMember
          ? currentMembers.map((member) => (member.id === mapped.id ? mapped : member))
          : [mapped, ...currentMembers]
      ))
      setModalOpen(false)
      setEditingMember(null)
    } catch (requestError) {
      setFormError(requestError.message || '团队成员保存失败')
    } finally {
      setSaving(false)
    }
  }

  const activeCount = members.filter((member) => member.status === 'active').length
  const managerCount = members.filter((member) => ['管理员', '销售经理'].includes(member.role)).length
  const ownDataCount = members.filter((member) => member.dataScope === 'own').length

  return (
    <div className="crm-page-stack">
      <ResourceHeader
        title="团队成员"
        subtitle="组织成员、角色权限、账号状态和数据范围集中维护。"
        icon={Users}
        createLabel="新增成员"
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onCreate={handleOpenCreate}
        onFocusSearch={() => searchInputRef.current?.focus()}
        onExport={() => downloadResourceCsv('团队成员', visibleMembers, teamMemberExportColumns)}
        exportDisabled={!visibleMembers.length}
      />
      <ResourceSyncState loading={loading || saving} error={error || formError} />

      <section className="crm-metric-grid">
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified"><Users size={18} /></div>
          <div>
            <span>团队人数</span>
            <strong>{members.length}</strong>
            <small>{activeCount} 个账号启用</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-proposal"><KeyRound size={18} /></div>
          <div>
            <span>管理角色</span>
            <strong>{managerCount}</strong>
            <small>管理员与销售经理</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-new"><Shield size={18} /></div>
          <div>
            <span>本人数据范围</span>
            <strong>{ownDataCount}</strong>
            <small>销售角色自动限制 owner 数据</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-won"><Building2 size={18} /></div>
          <div>
            <span>当前操作人</span>
            <strong>{activeProfile.name}</strong>
            <small>{activeProfile.role} / {dataScopeLabelMap[activeProfile.dataScope] ?? activeProfile.dataScope}</small>
          </div>
        </article>
      </section>

      <ResourceToolbar query={query} onQueryChange={setQuery} columnCount={7} inputRef={searchInputRef} />
      <section className="crm-panel">
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>邮箱/手机</th>
                <th>角色</th>
                <th>数据范围</th>
                <th>岗位</th>
                <th>状态</th>
                <th>最近登录</th>
                <th className="crm-table-actions-cell">操作</th>
              </tr>
            </thead>
            <tbody>
              {visibleMembers.map((member) => {
                const canEditMember = activeProfile.role === '管理员' || member.role !== '管理员'
                return (
                  <tr key={member.id}>
                    <td>
                      <strong>{member.fullName}</strong>
                      <span>{member.department}</span>
                    </td>
                    <td>
                      <strong>{member.email}</strong>
                      <span>{member.phone || '未填写手机'}</span>
                    </td>
                    <td><StatusBadge value={member.role} tone={member.role === '管理员' ? 'success' : member.role === '销售经理' ? 'accent' : 'neutral'} /></td>
                    <td><StatusBadge value={dataScopeLabelMap[member.dataScope] ?? member.dataScope} tone={member.dataScope === 'own' ? 'warning' : 'success'} /></td>
                    <td>
                      <strong>{member.position}</strong>
                      <span>{member.location}</span>
                    </td>
                    <td><StatusBadge value={teamStatusLabelMap[member.status] ?? member.status} tone={statusToneMap[member.status] ?? 'neutral'} /></td>
                    <td>{member.lastLoginAt ? formatDateTime(member.lastLoginAt) : '尚未登录'}</td>
                    <td className="crm-table-actions-cell">
                      <button className="crm-icon-button" type="button" aria-label="编辑成员" title={canEditMember ? '编辑' : '仅管理员可编辑管理员账号'} onClick={() => handleOpenEdit(member)} disabled={!canEditMember}>
                        <Pencil size={15} />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
      {!loading && !error && !visibleMembers.length ? <EmptyState icon={Users} title="暂无团队成员" subtitle="新增成员后会在这里维护角色和账号状态。" /> : null}

      <TeamMemberModal
        open={modalOpen}
        editingMember={editingMember}
        draft={draft}
        currentUserId={activeProfile.id}
        currentUserRole={activeProfile.role}
        onDraftChange={setDraft}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
        submitting={saving}
      />
    </div>
  )
}

function AccountsPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const ownerDraftDefaults = useMemo(() => ({ owner: activeProfile.name }), [activeProfile.name])
  const { records, loading, error } = useRemoteRecords(fetchCustomers, mapCustomerRecord)

  return (
    <TableResourcePage
      title="客户"
      subtitle="企业档案、年度收入、客户负责人和状态概览。"
      icon={Building}
      records={records}
      loading={loading}
      error={error}
      defaultDraftValues={ownerDraftDefaults}
      onCreateRecord={(draft) => createCustomer(buildCustomerPayload(draft, activeProfile.name)).then(mapCustomerRecord)}
      onUpdateRecord={(id, draft) => updateCustomer(id, buildCustomerPayload(draft, activeProfile.name)).then(mapCustomerRecord)}
      onDeleteRecord={deleteCustomer}
      getRecordHref={(record) => `/accounts/${record.id}`}
      openRecordLabel="打开客户工作台"
      createLabel="新建客户"
      columns={[
        { key: 'name', label: '客户名称', defaultValue: '' },
        { key: 'industry', label: '行业', defaultValue: '' },
        { key: 'contactPerson', label: '联系人', defaultValue: '' },
        { key: 'phone', label: '电话', inputType: 'tel', defaultValue: '' },
        { key: 'email', label: '邮箱', inputType: 'email', defaultValue: '' },
        { key: 'city', label: '城市', defaultValue: '深圳' },
        { key: 'source', label: '来源', defaultValue: '前端录入' },
        { key: 'level', label: '等级', type: 'badge', inputType: 'select', options: ['S', 'A', 'B', 'C'], defaultValue: 'B' },
        { key: 'owner', label: '负责人' },
        { key: 'revenue', label: '年度收入', format: 'currency' },
        { key: 'status', label: '状态', type: 'badge', inputType: 'select', options: ['active', 'nurturing', 'proposal', 'closed'], optionLabels: { active: '活跃', nurturing: '培育中', proposal: '方案中', closed: '关闭' }, defaultValue: 'active' },
      ]}
      tabs={[
        { key: 'all', label: '全部' },
        { key: 'active', label: '活跃', predicate: (item) => item.status === 'active' },
        { key: 'closed', label: '关闭', predicate: (item) => item.status === 'closed' },
      ]}
    />
  )
}

function formatWorkspaceMetric(metric) {
  const numericValue = Number(metric.value)
  if (Number.isFinite(numericValue) && (metric.label.includes('收入') || metric.label.includes('商机'))) {
    return formatCurrency(numericValue)
  }
  if (metric.label.includes('健康')) {
    return `${metric.value}分`
  }
  return metric.value
}

function getHealthGradeTone(grade) {
  if (grade === 'excellent' || grade === 'healthy') {
    return 'success'
  }
  if (grade === 'watch') {
    return 'warning'
  }
  if (grade === 'risk') {
    return 'danger'
  }
  return 'neutral'
}

function getHealthFactorTone(level) {
  if (level === 'strong') {
    return 'success'
  }
  if (level === 'stable') {
    return 'accent'
  }
  if (level === 'watch') {
    return 'warning'
  }
  if (level === 'risk') {
    return 'danger'
  }
  return 'neutral'
}

function getHealthTrendLabel(trend) {
  return {
    up: '上升',
    stable: '稳定',
    down: '下降',
  }[trend] ?? '稳定'
}

function CustomerWorkspacePage() {
  const { customerId } = useParams()
  const navigate = useNavigate()
  const [workspace, setWorkspace] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activityDraft, setActivityDraft] = useState({
    activity_type: 'call',
    subject: '',
    summary: '',
    outcome: '',
    next_action: '',
    sentiment: 'neutral',
  })
  const [activitySaving, setActivitySaving] = useState(false)
  const [activityError, setActivityError] = useState('')
  const [activityTaskSavingId, setActivityTaskSavingId] = useState(null)
  const [activityTasks, setActivityTasks] = useState({})
  const [orderDraftGoal, setOrderDraftGoal] = useState('')
  const [orderDraft, setOrderDraft] = useState(null)
  const [orderDraftLoading, setOrderDraftLoading] = useState(false)
  const [orderDraftSubmitting, setOrderDraftSubmitting] = useState(false)
  const [orderDraftError, setOrderDraftError] = useState('')
  const [createdDraftOrder, setCreatedDraftOrder] = useState(null)

  useEffect(() => {
    let mounted = true
    fetchCustomerWorkspace(customerId)
      .then((payload) => {
        if (mounted) {
          setWorkspace(payload)
          setError('')
        }
      })
      .catch((requestError) => {
        if (mounted) {
          setError(requestError.message || '客户工作台加载失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [customerId])

  const customer = workspace?.customer
  const accountPlan = workspace?.account_plan
  const healthProfile = workspace?.health_profile
  const defaultOrderDraftGoal = orderDraftGoal || accountPlan?.next_actions?.[0] || healthProfile?.recommended_actions?.[0]?.detail || '围绕客户当前经营计划生成可复核订单草稿'

  const handleActivityDraftChange = (key, value) => {
    setActivityDraft((currentDraft) => ({ ...currentDraft, [key]: value }))
  }

  const handleCreateActivity = async (event) => {
    event.preventDefault()
    setActivitySaving(true)
    setActivityError('')
    try {
      await createCustomerActivity(customerId, {
        ...activityDraft,
        subject: activityDraft.subject || `${customer?.company ?? '客户'}跟进`,
        summary: activityDraft.summary || activityDraft.outcome || '完成一次客户跟进。',
      })
      const nextWorkspace = await fetchCustomerWorkspace(customerId)
      setWorkspace(nextWorkspace)
      setActivityDraft({
        activity_type: 'call',
        subject: '',
        summary: '',
        outcome: '',
        next_action: '',
        sentiment: 'neutral',
      })
    } catch (requestError) {
      setActivityError(requestError.message || '新增互动失败')
    } finally {
      setActivitySaving(false)
    }
  }

  const handleCreateActivityTask = async (activity) => {
    setActivityTaskSavingId(activity.id)
    setActivityError('')
    try {
      const task = await convertCustomerActivityToTask(activity.id)
      setActivityTasks((currentTasks) => ({
        ...currentTasks,
        [activity.id]: task,
      }))
    } catch (requestError) {
      setActivityError(requestError.message || '互动转任务失败')
    } finally {
      setActivityTaskSavingId(null)
    }
  }

  const handleGenerateOrderDraft = async () => {
    if (!customer) {
      return
    }
    setOrderDraftLoading(true)
    setOrderDraftError('')
    setCreatedDraftOrder(null)
    try {
      const draft = await generateOrderDraft({
        customer_id: customer.id,
        business_goal: defaultOrderDraftGoal,
      })
      setOrderDraft(draft)
    } catch (requestError) {
      setOrderDraftError(requestError.message || '订单草稿生成失败')
    } finally {
      setOrderDraftLoading(false)
    }
  }

  const handleSubmitOrderDraft = async () => {
    if (!orderDraft || !customer) {
      return
    }
    setOrderDraftSubmitting(true)
    setOrderDraftError('')
    try {
      const order = await createOrder(buildOrderPayloadFromCopilotDraft(orderDraft, customer))
      setCreatedDraftOrder(order)
      const nextWorkspace = await fetchCustomerWorkspace(customerId)
      setWorkspace(nextWorkspace)
    } catch (requestError) {
      setOrderDraftError(requestError.message || '订单草稿提交失败')
    } finally {
      setOrderDraftSubmitting(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <button className="crm-ghost-button" type="button" onClick={() => navigate('/accounts')}>
            <ArrowRight size={16} className="crm-icon-flip" />
            返回客户列表
          </button>
          <span className="crm-overline">Customer 360</span>
          <h2>{customer?.company ?? '客户工作台'}</h2>
          <p>{customer ? `${customer.industry} / ${customer.city} / ${customer.owner}` : '正在加载客户经营视图'}</p>
        </div>
        <div className="crm-copilot-summary">
          <Building2 size={18} />
          <strong>{customer ? `${customer.level} 级客户 · ${customer.contact_person}` : '读取客户资料中'}</strong>
        </div>
      </section>

      <ResourceSyncState loading={loading} error={error} />

      {workspace ? (
        <>
          <section className="crm-metric-grid">
            {workspace.metrics.map((metric) => (
              <article key={metric.label} className="crm-panel crm-metric-card">
                <div className="crm-metric-icon tone-qualified">
                  <BarChart3 size={18} />
                </div>
                <div>
                  <span>{metric.label}</span>
                  <strong>{formatWorkspaceMetric(metric)}</strong>
                  <small>{metric.hint}</small>
                </div>
              </article>
            ))}
          </section>

          {healthProfile ? (
            <section className="crm-panel">
              <PanelHeader title="客户健康画像" actionLabel={healthProfile.grade_label} />
              <div className="crm-dashboard-grid">
                <article className="crm-list-item">
                  <div>
                    <strong>{healthProfile.score} 分</strong>
                    <span>{healthProfile.evidence_summary}</span>
                  </div>
                  <StatusBadge value={healthProfile.grade_label} tone={getHealthGradeTone(healthProfile.grade)} />
                </article>
                <article className="crm-list-item">
                  <div>
                    <strong>流失概率 {formatPercent(healthProfile.churn_probability)}</strong>
                    <span>趋势 {getHealthTrendLabel(healthProfile.trend)}，由互动、工单、任务、订单和商机变化共同计算。</span>
                  </div>
                  <TrendingUp size={18} />
                </article>
              </div>
              <div className="crm-progress-list">
                {healthProfile.factors.map((factor) => {
                  const tone = getHealthFactorTone(factor.level)
                  return (
                    <div key={factor.key} className="crm-progress-row">
                      <div className="crm-progress-meta">
                        <span>
                          <span className={`crm-dot tone-${tone}`} />
                          {factor.label}
                        </span>
                        <strong>{factor.score} / 100</strong>
                      </div>
                      <div className="crm-progress-track">
                        <div className={`crm-progress-bar tone-${tone}`} style={{ width: `${Math.max(4, factor.score)}%` }} />
                      </div>
                      <small>{factor.detail}</small>
                    </div>
                  )
                })}
              </div>
              <div className="crm-account-plan-grid">
                <CustomerPlanList title="风险旗标" items={healthProfile.risk_flags} tone="warning" />
                <CustomerPlanList title="优势证据" items={healthProfile.strengths} tone="success" />
                <CustomerHealthActionList actions={healthProfile.recommended_actions} />
              </div>
            </section>
          ) : null}

          <section className="crm-dashboard-grid">
            <div className="crm-panel">
              <PanelHeader title="AI 账户计划" actionLabel={accountPlan?.fallback_used ? '规则兜底' : 'LLM 增强'} />
              <div className="crm-script-box">
                <span>{accountPlan?.model ?? 'account-plan'}</span>
                <p>{accountPlan?.summary}</p>
              </div>
              <div className="crm-account-plan-grid">
                <CustomerPlanList title="扩展路径" items={accountPlan?.expansion_paths ?? []} tone="success" />
                <CustomerPlanList title="风险提醒" items={accountPlan?.risks ?? []} tone="warning" />
                <CustomerPlanList title="下一步动作" items={accountPlan?.next_actions ?? []} tone="accent" />
              </div>
            </div>

            <div className="crm-panel">
              <PanelHeader title="AI 订单草稿" actionLabel={orderDraft?.fallback_used ? '规则兜底' : orderDraft ? 'LLM 增强' : '可提交订单'} />
              <div className="crm-activity-form">
                <label className="crm-field">
                  <span>业务目标</span>
                  <input
                    value={orderDraftGoal}
                    onChange={(event) => setOrderDraftGoal(event.target.value)}
                    placeholder={defaultOrderDraftGoal}
                    maxLength={180}
                  />
                </label>
                <button className="crm-primary-button" type="button" onClick={handleGenerateOrderDraft} disabled={orderDraftLoading}>
                  <FileText size={16} />
                  {orderDraftLoading ? '生成中' : orderDraft ? '重新生成草稿' : '生成订单草稿'}
                </button>
              </div>
              {orderDraftError ? <div className="crm-form-error">{orderDraftError}</div> : null}
              {orderDraft ? (
                <div className="crm-list compact">
                  <article className="crm-list-item">
                    <div>
                      <strong>{orderDraft.customer_name}</strong>
                      <span>{orderDraft.llm_summary}</span>
                    </div>
                    <StatusBadge value={orderDraft.fallback_used ? '兜底' : 'LLM'} tone={orderDraft.fallback_used ? 'warning' : 'success'} />
                  </article>
                  {orderDraft.items.map((item) => (
                    <article key={item.product_id} className="crm-list-item">
                      <div>
                        <strong>{item.product_name}</strong>
                        <span>{item.quantity} 件 / {formatCurrency(item.unit_price)} / 小计 {formatCurrency(item.quantity * item.unit_price)}</span>
                      </div>
                    </article>
                  ))}
                  <article className="crm-list-item">
                    <div>
                      <strong>预计总额 {formatCurrency(orderDraft.items.reduce((total, item) => total + item.quantity * item.unit_price, 0))}</strong>
                      <span>{orderDraft.suggested_notes}</span>
                    </div>
                  </article>
                  <div className="crm-form-actions">
                    <button className="crm-primary-button" type="button" onClick={handleSubmitOrderDraft} disabled={orderDraftSubmitting || Boolean(createdDraftOrder)}>
                      <Save size={16} />
                      {orderDraftSubmitting ? '提交中' : createdDraftOrder ? `订单 #${createdDraftOrder.id}` : '提交为订单'}
                    </button>
                    {createdDraftOrder ? (
                      <button className="crm-ghost-button" type="button" onClick={() => navigate('/orders')}>
                        <ArrowRight size={16} />
                        去订单中心
                      </button>
                    ) : null}
                  </div>
                </div>
              ) : (
                <EmptyState icon={FileText} title="暂无订单草稿" subtitle="根据客户经营计划生成可复核订单，并提交到真实订单闭环。" />
              )}
            </div>

            <div className="crm-panel">
              <PanelHeader title="关键联系人" actionLabel={`${workspace.contacts.length} 人`} />
              <div className="crm-list compact">
                {workspace.contacts.map((contact) => (
                  <article key={contact.id} className="crm-list-item">
                    <div>
                      <strong>{contact.name}</strong>
                      <span>{contact.role} / {contact.email}</span>
                    </div>
                    <StatusBadge value={contact.status} tone={contact.status === 'active' ? 'success' : 'neutral'} />
                  </article>
                ))}
                {!workspace.contacts.length ? <EmptyState icon={Users} title="暂无联系人" subtitle="新建联系人后会出现在客户工作台。" /> : null}
              </div>
            </div>
          </section>

          <section className="crm-dashboard-grid">
            <CustomerWorkspaceList
              title="客户商机"
              actionLabel={`${workspace.leads.length} 个`}
              emptyIcon={Target}
              emptyTitle="暂无商机"
              items={workspace.leads}
              renderItem={(lead) => (
                <>
                  <div>
                    <strong>{lead.title}</strong>
                    <span>{lead.stage} / {formatCurrency(lead.expected_amount)} / {lead.next_action}</span>
                  </div>
                  <StatusBadge value={lead.stage} tone={lead.stage === 'won' ? 'success' : lead.stage === 'lost' ? 'danger' : 'accent'} />
                </>
              )}
            />
            <CustomerWorkspaceList
              title="订单闭环"
              actionLabel={`${workspace.orders.length} 单`}
              emptyIcon={Activity}
              emptyTitle="暂无订单"
              items={workspace.orders}
              renderItem={(order) => (
                <>
                  <div>
                    <strong>订单 #{order.id}</strong>
                    <span>{order.status} / {formatCurrency(order.total_amount)} / {order.items.length} 个条目</span>
                  </div>
                  <StatusBadge value={order.created_by_ai ? 'AI' : '人工'} tone={order.created_by_ai ? 'accent' : 'neutral'} />
                </>
              )}
            />
          </section>

          <section className="crm-dashboard-grid">
            <CustomerWorkspaceList
              title="客户互动"
              actionLabel={`${workspace.activities.length} 条`}
              emptyIcon={Phone}
              emptyTitle="暂无互动记录"
              items={workspace.activities}
              renderItem={(activity) => (
                <>
                  <div>
                    <strong>{activity.subject}</strong>
                    <span>{activity.activity_type} / {activity.outcome || activity.summary}</span>
                  </div>
                  <div className="crm-workspace-item-side">
                    <StatusBadge value={activity.sentiment} tone={activity.sentiment === 'positive' ? 'success' : activity.sentiment === 'risk' || activity.sentiment === 'negative' ? 'danger' : 'neutral'} />
                    <button
                      className="crm-ghost-button"
                      type="button"
                      onClick={() => handleCreateActivityTask(activity)}
                      disabled={activityTaskSavingId === activity.id}
                    >
                      <CheckSquare size={15} />
                      {activityTaskSavingId === activity.id ? '生成中' : activityTasks[activity.id] ? `任务 #${activityTasks[activity.id].id}` : '转任务'}
                    </button>
                    {activityTasks[activity.id] ? (
                      <button className="crm-primary-button" type="button" onClick={() => navigate('/tasks')}>
                        <ArrowRight size={15} />
                        查看任务
                      </button>
                    ) : null}
                  </div>
                </>
              )}
            />
            <div className="crm-panel">
              <PanelHeader title="新增互动" actionLabel={activitySaving ? '保存中' : '实时入库'} />
              <form className="crm-activity-form" onSubmit={handleCreateActivity}>
                <div className="crm-workspace-form-grid">
                  <label className="crm-field">
                    <span>类型</span>
                    <select value={activityDraft.activity_type} onChange={(event) => handleActivityDraftChange('activity_type', event.target.value)}>
                      <option value="call">电话</option>
                      <option value="meeting">会议</option>
                      <option value="email">邮件</option>
                      <option value="review">复盘</option>
                    </select>
                  </label>
                  <label className="crm-field">
                    <span>信号</span>
                    <select value={activityDraft.sentiment} onChange={(event) => handleActivityDraftChange('sentiment', event.target.value)}>
                      <option value="positive">正向</option>
                      <option value="neutral">中性</option>
                      <option value="risk">风险</option>
                      <option value="negative">负向</option>
                    </select>
                  </label>
                  <label className="crm-field crm-field-span">
                    <span>主题</span>
                    <input value={activityDraft.subject} onChange={(event) => handleActivityDraftChange('subject', event.target.value)} required />
                  </label>
                  <label className="crm-field crm-field-span">
                    <span>摘要</span>
                    <textarea value={activityDraft.summary} onChange={(event) => handleActivityDraftChange('summary', event.target.value)} required />
                  </label>
                  <label className="crm-field">
                    <span>结果</span>
                    <input value={activityDraft.outcome} onChange={(event) => handleActivityDraftChange('outcome', event.target.value)} />
                  </label>
                  <label className="crm-field">
                    <span>下一步</span>
                    <input value={activityDraft.next_action} onChange={(event) => handleActivityDraftChange('next_action', event.target.value)} />
                  </label>
                </div>
                {activityError ? <div className="crm-form-error">{activityError}</div> : null}
                <div className="crm-form-actions">
                  <button className="crm-primary-button" type="submit" disabled={activitySaving}>
                    {activitySaving ? '保存中' : '保存互动'}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section className="crm-dashboard-grid">
            <CustomerWorkspaceList
              title="服务工单"
              actionLabel={`${workspace.cases.length} 条`}
              emptyIcon={Briefcase}
              emptyTitle="暂无工单"
              items={workspace.cases}
              renderItem={(supportCase) => (
                <>
                  <div>
                    <strong>{supportCase.title}</strong>
                    <span>{supportCase.status_label} / {supportCase.priority} / {supportCase.due_date}</span>
                  </div>
                  <StatusBadge value={supportCase.priority} tone={supportCase.priority === 'hot' ? 'danger' : 'warning'} />
                </>
              )}
            />
            <CustomerWorkspaceList
              title="Copilot 推荐"
              actionLabel={`${workspace.recommendations.length} 条`}
              emptyIcon={Bot}
              emptyTitle="暂无推荐"
              items={workspace.recommendations}
              renderItem={(record) => (
                <>
                  <div>
                    <strong>{record.lead_title || record.customer_name}</strong>
                    <span>{record.next_best_action || record.llm_summary}</span>
                  </div>
                  <div className="crm-score-pill">
                    <span>{record.grade || '-'}</span>
                    <strong>{record.rule_score ?? 0}</strong>
                  </div>
                </>
              )}
            />
          </section>

          <section className="crm-panel">
            <PanelHeader title="客户时间线" actionLabel={`${workspace.timeline.length} 条`} />
            <div className="crm-activity-list">
              {workspace.timeline.map((item) => (
                <article key={item.id} className="crm-activity-item">
                  <div className={`crm-activity-icon tone-${item.severity}`}>
                    <Activity size={16} />
                  </div>
                  <div>
                    <strong>{item.category} · {item.title}</strong>
                    <span>{item.description}</span>
                  </div>
                  <time>{formatDateTime(item.timestamp)}</time>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}

function CustomerHealthActionList({ actions }) {
  return (
    <div className="crm-account-plan-list">
      <strong>建议动作</strong>
      {actions.map((action) => (
        <span key={`${action.source}-${action.title}`}>
          <span className={`crm-dot tone-${statusToneMap[action.priority] ?? 'accent'}`} />
          {action.title}：{action.detail}
        </span>
      ))}
    </div>
  )
}

function CustomerPlanList({ title, items, tone }) {
  return (
    <div className="crm-account-plan-list">
      <strong>{title}</strong>
      {items.map((item) => (
        <span key={item}>
          <span className={`crm-dot tone-${tone}`} />
          {item}
        </span>
      ))}
    </div>
  )
}

function CustomerWorkspaceList({ title, actionLabel, emptyIcon, emptyTitle, items, renderItem }) {
  return (
    <div className="crm-panel">
      <PanelHeader title={title} actionLabel={actionLabel} />
      <div className="crm-list compact">
        {items.map((item) => (
          <article key={item.id} className="crm-list-item">
            {renderItem(item)}
          </article>
        ))}
        {!items.length ? <EmptyState icon={emptyIcon} title={emptyTitle} subtitle="该客户暂未沉淀对应业务数据。" /> : null}
      </div>
    </div>
  )
}

function ContactsPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const ownerDraftDefaults = useMemo(() => ({ owner: activeProfile.name }), [activeProfile.name])
  const { records, loading, error } = useRemoteRecords(fetchContacts, mapContactRecord)

  return (
    <TableResourcePage
      title="联系人"
      subtitle="跟踪关键联系人、角色、所属公司和最近互动。"
      icon={Users}
      records={records}
      loading={loading}
      error={error}
      defaultDraftValues={ownerDraftDefaults}
      onCreateRecord={(draft) => createContact(buildContactPayload(draft, activeProfile.name)).then(mapContactRecord)}
      onUpdateRecord={(id, draft) => updateContact(id, buildContactPayload(draft, activeProfile.name)).then(mapContactRecord)}
      onDeleteRecord={deleteContact}
      createLabel="新建联系人"
      columns={[
        { key: 'name', label: '姓名', defaultValue: '' },
        { key: 'company', label: '所属客户', defaultValue: '' },
        { key: 'role', label: '职位', defaultValue: '' },
        { key: 'email', label: '邮箱', inputType: 'email', defaultValue: '' },
        { key: 'phone', label: '电话', inputType: 'tel', defaultValue: '' },
        { key: 'owner', label: '负责人' },
        { key: 'status', label: '状态', type: 'badge', inputType: 'select', options: ['active', 'nurturing', 'closed'], optionLabels: { active: '活跃', nurturing: '培育中', closed: '关闭' }, defaultValue: 'active' },
      ]}
      tabs={[
        { key: 'all', label: '全部' },
        { key: 'vip', label: '重点', predicate: (item) => item.status === 'active' },
        { key: 'nurturing', label: '培育中', predicate: (item) => item.status === 'nurturing' },
      ]}
    />
  )
}

function LeadsPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const ownerDraftDefaults = useMemo(() => ({ owner: activeProfile.name }), [activeProfile.name])
  const { records, loading, error } = useRemoteRecords(fetchLeads, mapLeadRecord)
  const handleStageChange = (record, nextStage) => updateLeadStage(record.id, normalizeLeadStage(nextStage)).then(mapLeadRecord)

  return (
    <BoardResourcePage
      title="线索"
      subtitle="在列表和看板之间切换，拖动卡片或一键推进线索阶段。"
      icon={Target}
      records={records}
      loading={loading}
      error={error}
      defaultDraftValues={ownerDraftDefaults}
      onCreateRecord={(draft) => createLead(buildLeadPayload(draft, activeProfile.name)).then(mapLeadRecord)}
      onUpdateRecord={(id, draft) => updateLead(id, buildLeadPayload(draft, activeProfile.name)).then(mapLeadRecord)}
      onDeleteRecord={deleteLead}
      onWorkflowChange={handleStageChange}
      createLabel="新建线索"
      boardKey="stage"
      workflowOptions={leadPipelineLabels}
      columns={[
        { key: 'name', label: '线索', defaultValue: '' },
        { key: 'company', label: '公司', defaultValue: '' },
        { key: 'owner', label: '负责人' },
        { key: 'nextStep', label: '下一步', defaultValue: '' },
        { key: 'rating', label: '评级', type: 'badge' },
      ]}
    />
  )
}

function OpportunitiesPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const ownerDraftDefaults = useMemo(() => ({ owner: activeProfile.name }), [activeProfile.name])
  const { records, loading, error } = useRemoteRecords(fetchLeads, mapOpportunityRecord)
  const handleStageChange = (record, nextStage) => updateLeadStage(record.id, normalizeLeadStage(nextStage)).then(mapOpportunityRecord)

  return (
    <BoardResourcePage
      title="商机"
      subtitle="聚焦阶段、金额和预计成交时间，拖动卡片即可推进销售管道。"
      icon={Sparkles}
      records={records}
      loading={loading}
      error={error}
      defaultDraftValues={ownerDraftDefaults}
      onCreateRecord={(draft) => createLead(buildLeadPayload(draft, activeProfile.name)).then(mapOpportunityRecord)}
      onUpdateRecord={(id, draft) => updateLead(id, buildLeadPayload(draft, activeProfile.name)).then(mapOpportunityRecord)}
      onDeleteRecord={deleteLead}
      onWorkflowChange={handleStageChange}
      createLabel="新建商机"
      boardKey="stage"
      workflowOptions={leadPipelineLabels}
      columns={[
        { key: 'name', label: '商机', defaultValue: '' },
        { key: 'account', label: '客户', defaultValue: '' },
        { key: 'owner', label: '负责人' },
        { key: 'amount', label: '金额', format: 'currency' },
        { key: 'closeDate', label: '预计成交', inputType: 'date', defaultValue: '' },
      ]}
    />
  )
}

function CasesPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const ownerDraftDefaults = useMemo(() => ({ owner: activeProfile.name }), [activeProfile.name])
  const { records, loading, error } = useRemoteRecords(fetchCases, mapCaseRecord)

  return (
    <BoardResourcePage
      title="工单"
      subtitle="支持团队当前工作负载、优先级和处理 SLA 一览。"
      icon={Briefcase}
      records={records}
      loading={loading}
      error={error}
      defaultDraftValues={ownerDraftDefaults}
      onCreateRecord={(draft) => createCase(buildCasePayload(draft, activeProfile.name)).then(mapCaseRecord)}
      onUpdateRecord={(id, draft) => updateCase(id, buildCasePayload(draft, activeProfile.name)).then(mapCaseRecord)}
      onDeleteRecord={deleteCase}
      createLabel="新建工单"
      boardKey="statusLabel"
      columns={[
        { key: 'title', label: '工单标题', defaultValue: '' },
        { key: 'account', label: '客户', defaultValue: '' },
        { key: 'owner', label: '负责人' },
        { key: 'priority', label: '优先级', type: 'badge', inputType: 'select', options: ['hot', 'warm', 'cold'], defaultValue: 'warm' },
        { key: 'status', label: '状态', type: 'badge', inputType: 'select', options: ['open', 'working', 'closed'], optionLabels: { open: 'Open', working: 'Pending', closed: 'Resolved' }, defaultValue: 'open' },
      ]}
    />
  )
}

function LoginPage({ onLogin }) {
  const navigate = useNavigate()
  const [account, setAccount] = useState('demo@smart-crm.local')
  const [password, setPassword] = useState('SmartCRM@2026')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    document.title = '登录 | 深大 AI CRM'
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const session = await login({ account, password })
      onLogin(session)
      const nextOrg = session.organizations?.[0]
      if (nextOrg) {
        persistOrg({ id: nextOrg.id, name: nextOrg.name, role: nextOrg.role })
      }
      navigate('/org')
    } catch (nextError) {
      setError(nextError.message || '登录失败，请检查账号和密码')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="crm-auth-page">
      <main className="crm-auth-shell">
        <section className="crm-auth-showcase">
          <div className="crm-auth-brand">
            <BrandMark />
            <div>
              <strong>深大 AI CRM</strong>
              <span>销售、客户与任务协同平台</span>
            </div>
          </div>

          <div className="crm-auth-copy">
            <span className="crm-overline">欢迎回来</span>
            <h1>登录后继续处理你的客户流程</h1>
          </div>
        </section>

        <section className="crm-auth-panel">
          <div className="crm-auth-panel-head">
            <span className="crm-overline">登录</span>
            <h2>进入你的工作台</h2>
          </div>

          <form
            className="crm-auth-form"
            onSubmit={handleSubmit}
          >
            {error ? <div className="crm-auth-alert">{error}</div> : null}
            <label className="crm-auth-field">
              <span>账号</span>
              <input
                type="text"
                value={account}
                onChange={(event) => setAccount(event.target.value)}
                placeholder="请输入邮箱号或手机号"
                autoComplete="username"
                required
              />
            </label>

            <label className="crm-auth-field">
              <span>密码</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="请输入密码"
                autoComplete="current-password"
                required
              />
            </label>

            <button className="crm-primary-button crm-auth-submit" type="submit" disabled={submitting}>
              {submitting ? '登录中...' : '登录'}
              <ArrowRight size={16} />
            </button>
          </form>

          <div className="crm-auth-footer">
            <span>还没有账号？</span>
            <NavLink className="crm-link-button" to="/register">
              去注册
            </NavLink>
          </div>
        </section>
      </main>
    </div>
  )
}

function RegisterPage({ onLogin }) {
  const navigate = useNavigate()
  const [companyName, setCompanyName] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [agreed, setAgreed] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    document.title = '注册 | 深大 AI CRM'
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!agreed) {
      setError('请先阅读并同意服务协议与隐私政策')
      return
    }
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const session = await register({
        organization_name: companyName,
        full_name: fullName,
        email,
        phone,
        password,
        confirm_password: confirmPassword,
      })
      onLogin(session)
      const nextOrg = session.organizations?.[0]
      if (nextOrg) {
        persistOrg({ id: nextOrg.id, name: nextOrg.name, role: nextOrg.role })
      }
      navigate('/org')
    } catch (nextError) {
      setError(nextError.message || '注册失败，请检查输入信息')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="crm-auth-page">
      <main className="crm-auth-shell crm-auth-shell--compact">
        <section className="crm-auth-panel">
          <div className="crm-auth-brand crm-auth-brand--panel">
            <BrandMark />
            <div>
              <strong>深大 AI CRM</strong>
              <span>管理员注册</span>
            </div>
          </div>

          <div className="crm-auth-panel-head">
            <span className="crm-overline">注册</span>
            <h2>创建你的工作空间</h2>
          </div>

          <form
            className="crm-auth-form"
            onSubmit={handleSubmit}
          >
            {error ? <div className="crm-auth-alert">{error}</div> : null}
            <label className="crm-auth-field">
              <span>企业名称</span>
              <input
                type="text"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                placeholder="请输入企业或团队名称"
                autoComplete="organization"
                required
              />
            </label>

            <label className="crm-auth-field">
              <span>联系人姓名</span>
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="请输入管理员姓名"
                autoComplete="name"
                required
              />
            </label>

            <label className="crm-auth-field">
              <span>工作邮箱</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="请输入常用工作邮箱"
                autoComplete="email"
                required
              />
            </label>

            <label className="crm-auth-field">
              <span>手机号</span>
              <input
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="请输入手机号"
                autoComplete="tel"
              />
            </label>

            <label className="crm-auth-field">
              <span>密码</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="设置登录密码"
                autoComplete="new-password"
                required
              />
            </label>

            <label className="crm-auth-field">
              <span>确认密码</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="请再次输入密码"
                autoComplete="new-password"
                required
              />
            </label>

            <label className="crm-auth-check">
              <input type="checkbox" checked={agreed} onChange={(event) => setAgreed(event.target.checked)} />
              <span>我已阅读并同意服务协议与隐私政策</span>
            </label>

            <button className="crm-primary-button crm-auth-submit" type="submit" disabled={submitting}>
              {submitting ? '创建中...' : '创建账号'}
              <ArrowRight size={16} />
            </button>
          </form>

          <div className="crm-auth-footer">
            <span>已经有账号？</span>
            <NavLink className="crm-link-button" to="/login">
              去登录
            </NavLink>
          </div>
        </section>
      </main>
    </div>
  )
}

function AppShell({ authSession, onLogout, onSessionRefresh }) {
  const [collapsed, setCollapsed] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedOrg, setSelectedOrg] = useState(() => loadStoredOrg(authSession))
  const [notifications, setNotifications] = useState([])
  const [notificationOpen, setNotificationOpen] = useState(false)
  const [notificationError, setNotificationError] = useState('')
  const [notificationSavingId, setNotificationSavingId] = useState('')
  const [notificationBulkSaving, setNotificationBulkSaving] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const allowedNavItems = navItems.filter((item) => hasClientPermission(authSession, item.permission))
  const currentPage = pageItems.find((item) => location.pathname.startsWith(item.path)) ?? navItems[0]
  const isProfilePage = location.pathname.startsWith('/profile')
  const activeProfile = buildUserProfile(authSession?.user)
  const activeSelectedOrg = useMemo(() => resolveSelectedOrg(authSession, selectedOrg), [authSession, selectedOrg])
  const urgentNotificationCount = notifications.filter((item) => item.severity !== 'info' && !item.is_read).length

  useEffect(() => {
    document.title = currentPage.title
  }, [currentPage.title])

  useEffect(() => {
    persistOrg(activeSelectedOrg)
  }, [activeSelectedOrg])

  useEffect(() => {
    let mounted = true
    if (!authSession?.token || !hasClientPermission(authSession, 'dashboard:read')) {
      return undefined
    }
    fetchNotifications({ limit: 12 })
      .then((payload) => {
        if (mounted) {
          setNotifications(payload ?? [])
          setNotificationError('')
        }
      })
      .catch((requestError) => {
        if (mounted) {
          setNotificationError(requestError.message || '通知加载失败')
        }
      })

    return () => {
      mounted = false
    }
  }, [authSession, location.pathname])

  const applyNotificationState = (notificationId, state) => {
    setNotifications((currentNotifications) => currentNotifications.map((item) => (
      item.id === notificationId
        ? {
            ...item,
            is_read: state.is_read,
            dismissed: state.dismissed,
            state_updated_at: state.updated_at,
          }
        : item
    )).filter((item) => !item.dismissed))
  }

  const handleNotificationNavigate = async (item) => {
    if (!item.is_read) {
      try {
        const state = await updateNotificationState(item.id, { action: 'read' })
        applyNotificationState(item.id, state)
      } catch (requestError) {
        setNotificationError(requestError.message || '通知状态更新失败')
      }
    }
    setNotificationOpen(false)
    navigate(item.href)
  }

  const handleDismissNotification = async (notificationId) => {
    setNotificationSavingId(notificationId)
    setNotificationError('')
    try {
      const state = await updateNotificationState(notificationId, { action: 'dismiss' })
      applyNotificationState(notificationId, state)
    } catch (requestError) {
      setNotificationError(requestError.message || '通知忽略失败')
    } finally {
      setNotificationSavingId('')
    }
  }

  const handleMarkAllNotificationsRead = async () => {
    setNotificationBulkSaving(true)
    setNotificationError('')
    try {
      await markAllNotificationsRead()
      setNotifications((currentNotifications) => currentNotifications.map((item) => ({ ...item, is_read: true })))
    } catch (requestError) {
      setNotificationError(requestError.message || '通知状态更新失败')
    } finally {
      setNotificationBulkSaving(false)
    }
  }

  return (
    <div className="crm-shell">
      <div className={`crm-sidebar-backdrop ${sidebarOpen ? 'is-visible' : ''}`} onClick={() => setSidebarOpen(false)} />
      <aside className={`crm-sidebar ${collapsed ? 'is-collapsed' : ''} ${sidebarOpen ? 'is-open' : ''}`}>
        <div className="crm-sidebar-inner">
          <div className="crm-sidebar-header">
            <button className="crm-brand" type="button" onClick={() => navigate('/org')}>
              <BrandMark />
              <div className="crm-brand-copy">
                <strong>{activeSelectedOrg.name}</strong>
                <span>CRM 平台</span>
              </div>
            </button>
          </div>

          <div className="crm-sidebar-group">
            <div className="crm-sidebar-label">CRM</div>
            <nav className="crm-nav">
              {allowedNavItems.map(({ path, label, icon: Icon }) => (
                <NavLink
                  key={path}
                  to={path}
                  className={({ isActive }) => `crm-nav-link ${isActive ? 'is-active' : ''}`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="crm-sidebar-footer">
            <button className="crm-nav-link crm-nav-link--ghost" type="button" onClick={() => setCollapsed((value) => !value)}>
              <PanelLeftClose size={18} />
              <span>{collapsed ? '展开侧边栏' : '收起侧边栏'}</span>
            </button>
            <button
              className={`crm-user-card ${isProfilePage ? 'is-active' : ''}`}
              type="button"
              onClick={() => {
                setSidebarOpen(false)
                navigate('/profile')
              }}
            >
              <img className="crm-user-avatar" src={smartCrmLogo} alt="Smart CRM 小猪头像" />
              <div>
                <strong>{activeProfile.name}</strong>
                <span>{activeProfile.email}</span>
              </div>
              <ChevronsUpDown size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="crm-main">
        <header className="crm-topbar">
          <div>
            <button className="crm-icon-button crm-mobile-only" type="button" onClick={() => setSidebarOpen(true)}>
              <Menu size={18} />
            </button>
            <div className="crm-page-heading">
              <span>{activeSelectedOrg.name}</span>
              <h1>{currentPage.label}</h1>
            </div>
          </div>
          <div className="crm-topbar-actions">
            <div className="crm-notification-wrap">
              <button
                className={`crm-icon-button crm-notification-button ${notificationOpen ? 'is-active' : ''}`}
                type="button"
                aria-label="通知"
                onClick={() => setNotificationOpen((value) => !value)}
              >
                <Bell size={18} />
                {urgentNotificationCount ? <span className="crm-notification-badge">{urgentNotificationCount}</span> : null}
              </button>
              {notificationOpen ? (
                <div className="crm-notification-panel">
                  <div className="crm-notification-head">
                    <div className="crm-notification-title">
                      <strong>通知中心</strong>
                      <span>{`${notifications.length} 条业务提醒 · ${urgentNotificationCount} 条未读重点`}</span>
                    </div>
                    <div className="crm-notification-actions">
                      <button className="crm-link-button" type="button" onClick={handleMarkAllNotificationsRead} disabled={notificationBulkSaving || !notifications.some((item) => !item.is_read)}>
                        {notificationBulkSaving ? '处理中' : '全部已读'}
                      </button>
                      <button className="crm-link-button" type="button" onClick={() => handleNotificationNavigate({ href: '/dashboard', id: 'dashboard-link', is_read: true })}>
                        仪表盘
                      </button>
                    </div>
                  </div>
                  {notificationError ? <div className="crm-notification-error">{notificationError}</div> : null}
                  <div className="crm-notification-list">
                    {notifications.map((item) => (
                      <article
                        key={item.id}
                        className={`crm-notification-item tone-${item.severity} ${item.is_read ? 'is-read' : ''}`}
                      >
                        <button className="crm-notification-main" type="button" onClick={() => handleNotificationNavigate(item)}>
                          <span>{item.category}{item.is_read ? ' · 已读' : ' · 未读'}</span>
                          <strong>{item.title}</strong>
                          <small>{item.message}</small>
                          <em>{item.action_label} · {formatDateTime(item.created_at)}</em>
                        </button>
                        <button
                          className="crm-notification-dismiss"
                          type="button"
                          onClick={() => handleDismissNotification(item.id)}
                          disabled={notificationSavingId === item.id}
                        >
                          {notificationSavingId === item.id ? '处理中' : '忽略'}
                        </button>
                      </article>
                    ))}
                  </div>
                  {!notificationError && !notifications.length ? (
                    <div className="crm-notification-empty">暂无新的业务提醒</div>
                  ) : null}
                </div>
              ) : null}
            </div>
            <button className="crm-ghost-button" type="button" onClick={() => navigate('/org')}>
              <LogOut size={16} />
              切换组织
            </button>
          </div>
        </header>

        <section className="crm-content">
          <Outlet context={{ selectedOrg: activeSelectedOrg, setSelectedOrg, userProfile: activeProfile, onLogout, onSessionRefresh }} />
        </section>
      </main>
    </div>
  )
}

function OrgSelectionPage({ authSession, onLogout }) {
  const navigate = useNavigate()
  const availableOrgs = getSessionOrganizations(authSession)

  useEffect(() => {
    document.title = '选择组织 | 深大 AI CRM'
  }, [])

  return (
    <div className="crm-org-page">
      <header className="crm-org-header">
        <div className="crm-org-brand">
          <BrandMark />
          <strong>深大 AI CRM</strong>
        </div>
        <button
          className="crm-ghost-button"
          type="button"
          onClick={async () => {
            await onLogout()
            navigate('/login')
          }}
        >
          <LogOut size={16} />
          退出
        </button>
      </header>

      <main className="crm-org-main">
        <div className="crm-org-copy">
          <h1>选择一个组织</h1>
          <p>组织来自后端认证会话，管理员可在团队成员页维护账号、角色、状态和数据范围。</p>
        </div>

        <div className="crm-org-list">
          {availableOrgs.map((org) => (
            <button
              key={org.id}
              type="button"
              className="crm-org-card"
              onClick={() => {
                persistOrg(org)
                navigate('/dashboard')
              }}
            >
              <div className="crm-org-card-icon">
                <Building2 size={24} />
              </div>
              <div className="crm-org-card-copy">
                <strong>{org.name}</strong>
                <span>{org.role}</span>
              </div>
              <ChevronRight size={18} />
            </button>
          ))}
        </div>

        <button className="crm-dashed-button" type="button" onClick={() => navigate('/register')}>
          <Plus size={16} />
          创建新的组织
        </button>

        <div className="crm-org-note">
          <Shield size={16} />
          <span>你的数据保持私密和安全。</span>
        </div>
      </main>
    </div>
  )
}

function DashboardPage() {
  const [dashboardData, setDashboardData] = useState({
    dashboard: null,
    leads: [],
    tasks: [],
    goals: [],
    loading: true,
    error: '',
  })

  useEffect(() => {
    let mounted = true

    Promise.all([fetchDashboard(), fetchLeads(), fetchTasks(), fetchGoals()])
      .then(([dashboard, leads, tasks, goals]) => {
        if (mounted) {
          setDashboardData({
            dashboard,
            leads,
            tasks,
            goals,
            loading: false,
            error: '',
          })
        }
      })
      .catch((error) => {
        if (mounted) {
          setDashboardData((current) => ({
            ...current,
            loading: false,
            error: error.message || '仪表盘数据同步失败',
          }))
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  const { dashboard, leads, tasks, goals, loading, error } = dashboardData
  const focusItems = useMemo(() => buildDashboardFocus({ dashboard, leads, tasks }), [dashboard, leads, tasks])
  const stageCards = useMemo(() => buildDashboardStages(leads), [leads])
  const dashboardMetrics = useMemo(() => buildDashboardMetrics(dashboard), [dashboard])
  const hotLeads = useMemo(() => buildHotLeads(leads), [leads])
  const topTasks = useMemo(() => tasks.map(mapTaskRecord).slice(0, 4), [tasks])
  const topOpportunities = useMemo(
    () =>
      [...leads]
        .filter((lead) => !['lost'].includes(normalizeStage(lead.stage)))
        .sort((first, second) => Number(second.expected_amount ?? 0) - Number(first.expected_amount ?? 0))
        .slice(0, 4)
        .map(mapOpportunityRecord),
    [leads],
  )
  const goalCards = useMemo(() => goals.map(mapGoalRecord), [goals])
  const activities = useMemo(() => buildRecentActivities(dashboard), [dashboard])

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel">
        <div>
          <span className="crm-overline">下午好</span>
          <h2>仪表盘</h2>
          <p>以下数据来自 FastAPI 后端，聚焦重点任务、跟进和销售管道。</p>
        </div>
      </section>
      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-focus-strip">
        <div className="crm-focus-title">
          <Sparkles size={16} />
          今日焦点
        </div>
        <div className="crm-focus-list">
          {focusItems.map((item) => (
            <a key={item.label} className="crm-focus-chip" href={item.href}>
              <item.icon size={16} />
              <strong>{item.value}</strong>
              <span>{item.label}</span>
            </a>
          ))}
        </div>
      </section>

      <section className="crm-stage-row">
        {stageCards.map((stage) => (
          <article key={stage.label} className={`crm-stage-card tone-${stage.tone}`}>
            <div className="crm-stage-top">
              <span>{stage.label}</span>
              <StatusBadge value={stage.count} tone={stage.tone} isNumeric />
            </div>
            <strong>{formatCurrency(stage.amount)}</strong>
          </article>
        ))}
      </section>

      <section className="crm-metric-grid">
        {dashboardMetrics.map((metric) => (
          <article key={metric.label} className="crm-panel crm-metric-card">
            <div className={`crm-metric-icon tone-${metric.tone}`}>
              <metric.icon size={18} />
            </div>
            <div>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.hint}</small>
            </div>
          </article>
        ))}
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="各阶段流程" actionLabel="全部流水线" actionHref="/opportunities" />
          <div className="crm-progress-list">
            {stageCards.map((stage) => (
              <div key={stage.label} className="crm-progress-row">
                <div className="crm-progress-meta">
                  <div className={`crm-dot tone-${stage.tone}`} />
                  <span>{stage.label}</span>
                  <strong>{formatCurrency(stage.amount)}</strong>
                </div>
                <div className="crm-progress-track">
                  <div className={`crm-progress-bar tone-${stage.tone}`} style={{ width: `${stage.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="热门线索" actionLabel="查看全部" actionHref="/leads" />
          {hotLeads.length ? (
            <div className="crm-list">
              {hotLeads.map((lead) => (
                <article key={lead.id} className="crm-list-item">
                  <div>
                    <strong>{lead.name}</strong>
                    <span>{lead.company}</span>
                  </div>
                  <StatusBadge value={lead.rating} tone={statusToneMap[lead.rating]} />
                </article>
              ))}
            </div>
          ) : (
            <EmptyState icon={Sparkles} title="没有热门线索" subtitle="新的高价值线索会显示在这里。" />
          )}
        </div>
      </section>

      <section className="crm-three-col-grid">
        <div className="crm-panel">
          <PanelHeader title="我的任务" actionLabel="查看全部" actionHref="/tasks" />
          <div className="crm-pill-row">
            {['全部', '逾期', '今天', '本周'].map((label, index) => (
              <button key={label} className={`crm-pill ${index === 0 ? 'is-active' : ''}`} type="button">
                {label}
              </button>
            ))}
          </div>
          <div className="crm-list compact">
            {topTasks.map((task) => (
              <article key={task.id} className="crm-list-item">
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.owner}</span>
                </div>
                <StatusBadge value={task.statusLabel} tone={statusToneMap[task.status]} />
              </article>
            ))}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="我的商机" actionLabel="查看全部" actionHref="/opportunities" />
          <div className="crm-list compact">
            {topOpportunities.map((item) => (
              <article key={item.id} className="crm-list-item">
                <div>
                  <strong>{item.name}</strong>
                  <span>{item.account}</span>
                </div>
                <div className="crm-list-value">{formatCurrency(item.amount)}</div>
              </article>
            ))}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="目标进展" actionLabel="查看全部" actionHref="/goals" />
          <div className="crm-goal-mini-list">
            {goalCards.map((goal) => (
              <div key={goal.id} className="crm-goal-mini-item">
                <div className="crm-goal-mini-head">
                  <strong>{goal.name}</strong>
                  <span>{goal.progress}%</span>
                </div>
                <div className="crm-progress-track">
                  <div className="crm-progress-bar tone-won" style={{ width: `${goal.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="近期活动" actionLabel="查看订单" actionHref="/orders" />
        {activities.length ? (
          <div className="crm-activity-list">
            {activities.map((item) => (
              <article key={item.id} className="crm-activity-item">
                <div className="crm-activity-icon">
                  <item.icon size={16} />
                </div>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.description}</span>
                </div>
                <time>{item.time}</time>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState icon={Activity} title="暂无近期活动" subtitle="后端订单或商机更新后会自动显示。" />
        )}
      </section>
    </div>
  )
}

function ReportsPage() {
  const emptyFilters = { date_from: '', date_to: '', owner: '', region: '' }
  const [draftFilters, setDraftFilters] = useState(emptyFilters)
  const [appliedFilters, setAppliedFilters] = useState(emptyFilters)
  const [reportState, setReportState] = useState({
    report: null,
    approvalReport: null,
    loading: true,
    error: '',
  })
  const [snapshotState, setSnapshotState] = useState({
    items: [],
    loading: true,
    error: '',
    savingType: '',
    deletingId: '',
  })
  const [snapshotVersion, setSnapshotVersion] = useState(0)

  useEffect(() => {
    let mounted = true
    Promise.all([fetchSalesPerformanceReport(appliedFilters), fetchApprovalPerformanceReport(appliedFilters)])
      .then(([report, approvalReport]) => {
        if (mounted) {
          setReportState({ report, approvalReport, loading: false, error: '' })
        }
      })
      .catch((error) => {
        if (mounted) {
          setReportState((current) => ({
            ...current,
            loading: false,
            error: error.message || '销售报表加载失败',
          }))
        }
      })

    return () => {
      mounted = false
    }
  }, [appliedFilters])

  useEffect(() => {
    let mounted = true
    setSnapshotState((current) => ({ ...current, loading: true, error: '' }))
    fetchReportSnapshots({ limit: 6 })
      .then((items) => {
        if (mounted) {
          setSnapshotState((current) => ({ ...current, items: Array.isArray(items) ? items : items.items ?? [], loading: false }))
        }
      })
      .catch((error) => {
        if (mounted) {
          setSnapshotState((current) => ({
            ...current,
            loading: false,
            error: error.message || '报表快照加载失败',
          }))
        }
      })

    return () => {
      mounted = false
    }
  }, [snapshotVersion])

  const { report, approvalReport, loading, error } = reportState
  const metricCards = useMemo(() => buildDashboardMetrics(report), [report])
  const approvalMetricCards = useMemo(() => buildDashboardMetrics(approvalReport), [approvalReport])
  const revenueTrend = report?.revenue_trend ?? []
  const ownerRows = report?.owner_performance ?? []
  const regionRows = report?.region_performance ?? []
  const funnelRows = report?.funnel ?? []
  const approvalRiskRows = approvalReport?.risk_distribution ?? []
  const approvalSlaRows = approvalReport?.sla_distribution ?? []
  const approvalReviewerRows = approvalReport?.reviewer_workload ?? []
  const maxTrendRevenue = Math.max(...revenueTrend.map((item) => item.revenue), 1)
  const maxOwnerValue = Math.max(...ownerRows.map((item) => Math.max(item.revenue, item.pipeline_amount)), 1)

  const handleFilterChange = (key, value) => {
    setDraftFilters((current) => ({ ...current, [key]: value }))
  }

  const handleFilterSubmit = (event) => {
    event.preventDefault()
    setReportState((current) => ({ ...current, loading: true, error: '' }))
    setAppliedFilters({ ...draftFilters })
  }

  const handleFilterReset = () => {
    setDraftFilters({ ...emptyFilters })
    setReportState((current) => ({ ...current, loading: true, error: '' }))
    setAppliedFilters({ ...emptyFilters })
  }

  const handleSaveSnapshot = async (reportType) => {
    const payload = reportType === 'approval_performance' ? approvalReport : report
    if (!payload) {
      return
    }
    const label = reportType === 'approval_performance' ? '审批 SLA' : '销售绩效'
    setSnapshotState((current) => ({ ...current, savingType: reportType, error: '' }))
    try {
      await createReportSnapshot({
        report_type: reportType,
        title: `${label}快照 ${new Date().toLocaleString('zh-CN', { hour12: false })}`,
        filters: payload.applied_filters ?? appliedFilters,
        summary: '',
      })
      setSnapshotVersion((value) => value + 1)
    } catch (saveError) {
      setSnapshotState((current) => ({ ...current, error: saveError.message || '报表快照保存失败' }))
    } finally {
      setSnapshotState((current) => ({ ...current, savingType: '' }))
    }
  }

  const handleDeleteSnapshot = async (snapshotId) => {
    setSnapshotState((current) => ({ ...current, deletingId: snapshotId, error: '' }))
    try {
      await deleteReportSnapshot(snapshotId)
      setSnapshotState((current) => ({
        ...current,
        items: current.items.filter((item) => item.id !== snapshotId),
      }))
    } catch (deleteError) {
      setSnapshotState((current) => ({ ...current, error: deleteError.message || '报表快照删除失败' }))
    } finally {
      setSnapshotState((current) => ({ ...current, deletingId: '' }))
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel">
        <div>
          <span className="crm-overline">Sales Intelligence</span>
          <h2>销售报表</h2>
          <p>从真实订单、商机、AI 参与和库存风险聚合经营报表，用于主管复盘和答辩展示。</p>
        </div>
        {report?.generated_at ? <span className="crm-muted-label">生成时间 {formatDateTime(report.generated_at)}</span> : null}
      </section>

      <form className="crm-panel crm-report-filter-bar" onSubmit={handleFilterSubmit}>
        <label className="crm-field">
          <span>开始日期</span>
          <input type="date" value={draftFilters.date_from} onChange={(event) => handleFilterChange('date_from', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>结束日期</span>
          <input type="date" value={draftFilters.date_to} onChange={(event) => handleFilterChange('date_to', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>负责人</span>
          <input placeholder="如 李伟超" value={draftFilters.owner} onChange={(event) => handleFilterChange('owner', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>区域</span>
          <input placeholder="如 华南" value={draftFilters.region} onChange={(event) => handleFilterChange('region', event.target.value)} />
        </label>
        <div className="crm-report-filter-actions">
          <button className="crm-primary-button" type="submit" disabled={loading}>
            <Filter size={16} />
            应用筛选
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleFilterReset} disabled={loading}>
            重置
          </button>
        </div>
      </form>

      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-panel">
        <PanelHeader title="报表快照历史" subtitle="保存当前经营视图，便于周会复盘和答辩展示" actionLabel={snapshotState.loading ? '同步中' : `${snapshotState.items.length} 条快照`} />
        <div className="crm-report-filter-actions">
          <button className="crm-primary-button" type="button" onClick={() => handleSaveSnapshot('sales_performance')} disabled={loading || !report || snapshotState.savingType === 'sales_performance'}>
            <Save size={16} />
            {snapshotState.savingType === 'sales_performance' ? '保存中' : '保存销售快照'}
          </button>
          <button className="crm-ghost-button" type="button" onClick={() => handleSaveSnapshot('approval_performance')} disabled={loading || !approvalReport || snapshotState.savingType === 'approval_performance'}>
            <FileText size={16} />
            {snapshotState.savingType === 'approval_performance' ? '保存中' : '保存审批快照'}
          </button>
        </div>
        {snapshotState.error ? <div className="crm-form-error">{snapshotState.error}</div> : null}
        <div className="crm-list compact">
          {snapshotState.items.map((snapshot) => (
            <article key={snapshot.id} className="crm-list-item">
              <div>
                <strong>{snapshot.title}</strong>
                <span>{snapshot.report_type_label} / {snapshot.metric_count} 项指标 / {snapshot.summary}</span>
                <small>{snapshot.created_by} 保存于 {formatDateTime(snapshot.created_at)}</small>
              </div>
              <div className="crm-status-cluster">
                <StatusBadge value={snapshot.report_type_label} tone={snapshot.report_type === 'approval_performance' ? 'warning' : 'info'} />
                <button className="crm-ghost-button crm-ghost-button--danger" type="button" onClick={() => handleDeleteSnapshot(snapshot.id)} disabled={snapshotState.deletingId === snapshot.id}>
                  <Trash2 size={15} />
                  {snapshotState.deletingId === snapshot.id ? '删除中' : '删除'}
                </button>
              </div>
            </article>
          ))}
          {!snapshotState.loading && !snapshotState.items.length ? <EmptyState icon={FileText} title="暂无报表快照" subtitle="保存一次销售或审批报表后会出现在这里。" /> : null}
        </div>
      </section>

      <section className="crm-metric-grid crm-report-metric-grid">
        {metricCards.map((metric) => (
          <article key={metric.label} className="crm-panel crm-metric-card">
            <div className={`crm-metric-icon tone-${metric.tone}`}>
              <metric.icon size={18} />
            </div>
            <div>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.hint}</small>
            </div>
          </article>
        ))}
      </section>

      <section className="crm-panel">
        <PanelHeader title="审批 SLA 分析" subtitle={approvalReport?.generated_at ? `生成时间 ${formatDateTime(approvalReport.generated_at)}` : '按真实订单审批记录聚合'} />
        <div className="crm-metric-grid crm-report-metric-grid">
          {approvalMetricCards.map((metric) => (
            <article key={metric.label} className="crm-metric-card compact">
              <div className={`crm-metric-icon tone-${metric.tone}`}>
                <metric.icon size={18} />
              </div>
              <div>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <small>{metric.hint}</small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="crm-dashboard-grid">
        <ApprovalDistributionPanel title="风险等级分布" rows={approvalRiskRows} toneMap={approvalRiskToneMap} emptyTitle="暂无审批风险数据" />
        <ApprovalDistributionPanel title="SLA 状态分布" rows={approvalSlaRows} toneMap={approvalSlaToneMap} emptyTitle="暂无审批 SLA 数据" />
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="审批人工作量" actionLabel="待审 / 已决策 / 逾期" />
          <div className="crm-report-breakdown-list">
            {approvalReviewerRows.map((row) => (
              <article key={row.name} className="crm-report-breakdown-item">
                <div className="crm-report-breakdown-head">
                  <div>
                    <strong>{row.name}</strong>
                    <span>待审 {row.pending_count} / 通过 {row.approved_count} / 驳回 {row.rejected_count}</span>
                  </div>
                  <StatusBadge value={`${row.overdue_count} 逾期`} tone={row.overdue_count ? 'danger' : 'success'} />
                </div>
                <div className="crm-report-breakdown-foot">
                  <span>平均处理 {row.average_resolution_hours}h</span>
                  <span>合计 {row.pending_count + row.approved_count + row.rejected_count} 条</span>
                </div>
              </article>
            ))}
            {!loading && !error && !approvalReviewerRows.length ? <EmptyState icon={ClipboardList} title="暂无审批人工作量" subtitle="提交订单审批后会在这里聚合。" /> : null}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="最近审批记录" actionLabel="订单审批真实流转" />
          <div className="crm-list compact">
            {(approvalReport?.recent_approvals ?? []).map((approval) => (
              <article key={approval.id} className="crm-list-item">
                <div>
                  <strong>订单 #{approval.order_id} · {approval.customer_name}</strong>
                  <span>{approval.owner} 提交给 {approval.reviewer || '销售经理'} / {formatApprovalSla(approval)}</span>
                </div>
                <div className="crm-status-cluster">
                  <StatusBadge value={approvalRiskLabelMap[approval.risk_level] ?? '中风险'} tone={approvalRiskToneMap[approval.risk_level] ?? 'info'} />
                  <StatusBadge value={approvalStatusLabelMap[approval.status] ?? approval.status} tone={approval.status === 'pending' ? 'warning' : approval.status === 'approved' ? 'success' : 'danger'} />
                </div>
              </article>
            ))}
            {!loading && !error && !(approvalReport?.recent_approvals ?? []).length ? <EmptyState icon={ClipboardList} title="暂无最近审批记录" subtitle="订单提交经理复核后会显示在这里。" /> : null}
          </div>
        </div>
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="收入趋势" actionLabel="按订单日期聚合" />
          <div className="crm-report-bars">
            {revenueTrend.map((item) => (
              <div key={item.month} className="crm-report-bar-row">
                <span>{item.month}</span>
                <div className="crm-progress-track">
                  <div className="crm-progress-bar tone-accent" style={{ width: `${Math.max(6, (item.revenue / maxTrendRevenue) * 100)}%` }} />
                </div>
                <strong>{formatCurrency(item.revenue)}</strong>
              </div>
            ))}
            {!loading && !error && !revenueTrend.length ? <EmptyState icon={BarChart3} title="暂无趋势数据" subtitle="当前筛选范围内没有订单收入。" /> : null}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="AI 收入影响" actionLabel="按真实订单计算" />
          {report?.ai_impact ? (
            <div className="crm-ai-impact">
              <div>
                <span>AI 收入</span>
                <strong>{formatCurrency(report.ai_impact.ai_revenue)}</strong>
              </div>
              <div>
                <span>人工收入</span>
                <strong>{formatCurrency(report.ai_impact.manual_revenue)}</strong>
              </div>
              <div className="crm-progress-track">
                <div className="crm-progress-bar tone-proposal" style={{ width: `${Math.max(4, report.ai_impact.ai_revenue_ratio * 100)}%` }} />
              </div>
              <small>
                AI 订单 {report.ai_impact.ai_order_count} 张，平均置信度 {formatPercent(report.ai_impact.average_ai_confidence)}
              </small>
            </div>
          ) : null}
        </div>
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="销售漏斗" actionLabel="按商机阶段聚合" />
          <div className="crm-progress-list">
            {funnelRows.map((stage) => (
              <div key={stage.stage} className="crm-progress-row">
                <div className="crm-progress-meta">
                  <div className={`crm-dot tone-${dashboardStageMeta[stage.stage]?.tone ?? 'neutral'}`} />
                  <span>{stage.label}</span>
                  <strong>{stage.lead_count} 个 / {formatCurrency(stage.expected_amount)}</strong>
                </div>
                <div className="crm-progress-track">
                  <div className={`crm-progress-bar tone-${dashboardStageMeta[stage.stage]?.tone ?? 'neutral'}`} style={{ width: `${Math.max(4, stage.share * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="库存风险联动" actionLabel="订单消耗 + 安全线" />
          <div className="crm-list compact">
            {(report?.inventory_risks ?? []).map((risk) => (
              <article key={risk.product_id} className="crm-list-item">
                <div>
                  <strong>{risk.name}</strong>
                  <span>{risk.sku} / 建议补货 {risk.recommended_restock} 件</span>
                </div>
                <StatusBadge value={`${risk.current_stock} 件`} tone={risk.priority === 'critical' ? 'danger' : 'warning'} />
              </article>
            ))}
            {!loading && !error && !(report?.inventory_risks ?? []).length ? <EmptyState icon={Package} title="暂无库存风险" subtitle="商品库存高于安全线时会显示为空。" /> : null}
          </div>
        </div>
      </section>

      <section className="crm-dashboard-grid">
        <ReportBreakdownPanel title="负责人绩效" rows={ownerRows} maxValue={maxOwnerValue} />
        <ReportBreakdownPanel title="区域绩效" rows={regionRows} maxValue={Math.max(...regionRows.map((item) => Math.max(item.revenue, item.pipeline_amount)), 1)} />
      </section>
    </div>
  )
}

function ApprovalDistributionPanel({ title, rows, toneMap, emptyTitle }) {
  return (
    <div className="crm-panel">
      <PanelHeader title={title} actionLabel="按真实审批记录聚合" />
      <div className="crm-progress-list">
        {rows.map((row) => {
          const tone = toneMap[row.key] ?? 'neutral'
          return (
            <div key={row.key} className="crm-progress-row">
              <div className="crm-progress-meta">
                <div className={`crm-dot tone-${tone}`} />
                <span>{row.label}</span>
                <strong>{row.count} 条 / {formatPercent(row.share)}</strong>
              </div>
              <div className="crm-progress-track">
                <div className={`crm-progress-bar tone-${tone}`} style={{ width: `${Math.max(4, row.share * 100)}%` }} />
              </div>
            </div>
          )
        })}
        {!rows.some((row) => row.count > 0) ? <EmptyState icon={ClipboardList} title={emptyTitle} subtitle="提交订单审批后会在这里形成分析。" /> : null}
      </div>
    </div>
  )
}

function ReportBreakdownPanel({ title, rows, maxValue }) {
  return (
    <div className="crm-panel">
      <PanelHeader title={title} actionLabel="收入 / 在管商机" />
      <div className="crm-report-breakdown-list">
        {rows.map((row) => (
          <article key={row.name} className="crm-report-breakdown-item">
            <div className="crm-report-breakdown-head">
              <div>
                <strong>{row.name}</strong>
                <span>{row.order_count} 单 / AI {row.ai_order_count} 单 / {row.open_leads} 个在管商机</span>
              </div>
              <div className="crm-list-value">{formatCurrency(row.revenue)}</div>
            </div>
            <div className="crm-progress-track">
              <div className="crm-progress-bar tone-accent" style={{ width: `${Math.max(4, (row.revenue / maxValue) * 100)}%` }} />
            </div>
            <div className="crm-report-breakdown-foot">
              <span>客单价 {formatCurrency(row.average_order_value)}</span>
              <span>在管商机 {formatCurrency(row.pipeline_amount)}</span>
            </div>
          </article>
        ))}
        {!rows.length ? <EmptyState icon={BarChart3} title="暂无绩效数据" subtitle="当前筛选范围内没有订单或商机。" /> : null}
      </div>
    </div>
  )
}

function cleanAiMarkdownLine(line) {
  return line
    .replace(/^#{1,6}\s*/, '')
    .replace(/^\s*[-*]\s+/, '')
    .replace(/^\s*\d+[.)、]\s*/, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .trim()
}

function parseAiText(value) {
  const text = String(value ?? '').trim()
  if (!text) {
    return []
  }
  return text
    .replace(/\r/g, '')
    .replace(/\s+(?=#{1,6}\s+)/g, '\n')
    .replace(/\s+(?=\d+[.)、]\s+)/g, '\n')
    .replace(/\s+(?=[-*]\s+)/g, '\n')
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const heading = line.match(/^#{1,6}\s*(.+)$/)
      const listItem = line.match(/^(\d+[.)、]|[-*])\s*(.+)$/)
      if (heading) {
        return { type: 'heading', text: cleanAiMarkdownLine(heading[1]) }
      }
      if (listItem) {
        return { type: 'item', text: cleanAiMarkdownLine(listItem[2]) }
      }
      return { type: 'paragraph', text: cleanAiMarkdownLine(line) }
    })
    .filter((item) => item.text)
}

function AiText({ value, fallback = '', compact = false }) {
  const segments = parseAiText(value || fallback)
  if (!segments.length) {
    return null
  }
  return (
    <div className={`crm-ai-text ${compact ? 'is-compact' : ''}`}>
      {segments.map((segment, index) => {
        if (segment.type === 'heading') {
          return <strong key={`${segment.type}-${index}`}>{segment.text}</strong>
        }
        return (
          <p key={`${segment.type}-${index}`} className={segment.type === 'item' ? 'is-item' : ''}>
            {segment.text}
          </p>
        )
      })}
    </div>
  )
}

function CopilotPage() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [historyRecords, setHistoryRecords] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [followUp, setFollowUp] = useState(null)
  const [loading, setLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [generating, setGenerating] = useState(false)
  const [convertingId, setConvertingId] = useState(null)
  const [feedbackSavingId, setFeedbackSavingId] = useState(null)
  const [createdTasks, setCreatedTasks] = useState({})
  const [scoreRulesOpen, setScoreRulesOpen] = useState(false)
  const [askQuestion, setAskQuestion] = useState('本周最需要优先跟进哪些客户？')
  const [askResult, setAskResult] = useState(null)
  const [askLoading, setAskLoading] = useState(false)
  const [askError, setAskError] = useState('')

  const loadSummary = async ({ force = false } = {}) => {
    setLoading(true)
    setError('')
    try {
      const payload = await fetchCopilotSummary({ force })
      setSummary(payload)
      setSelectedId(String(payload.top_opportunity?.id ?? payload.insights?.[0]?.id ?? ''))
      setFollowUp(null)
      refreshHistory()
    } catch (requestError) {
      setError(requestError.message || 'AI 副驾接口请求失败')
      refreshHistory()
    } finally {
      setLoading(false)
    }
  }

  const refreshHistory = async () => {
    setHistoryLoading(true)
    try {
      const payload = await fetchCopilotRecommendations({ limit: 8 })
      setHistoryRecords(Array.isArray(payload) ? payload : payload.items ?? [])
      setHistoryError('')
    } catch (requestError) {
      setHistoryError(requestError.message || 'Copilot 推荐历史加载失败')
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true
    setLoading(true)
    fetchCopilotSummary()
      .then((payload) => {
        if (!mounted) {
          return
        }
        setSummary(payload)
        setSelectedId(String(payload.top_opportunity?.id ?? payload.insights?.[0]?.id ?? ''))
        setFollowUp(null)
        setError('')
        refreshHistory()
      })
      .catch((requestError) => {
        if (mounted) {
          setError(requestError.message || 'AI 副驾接口请求失败')
          refreshHistory()
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  const insights = summary?.insights ?? []
  const selectedInsight = insights.find((item) => String(item.id) === selectedId) ?? insights[0]

  const handleGenerateFollowUp = async () => {
    if (!selectedInsight) {
      return
    }
    setGenerating(true)
    setError('')
    try {
      const payload = await generateFollowUp(selectedInsight.id)
      setFollowUp(payload)
      refreshHistory()
    } catch (requestError) {
      setError(requestError.message || '生成跟进话术失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleCreateTask = async (record) => {
    setConvertingId(record.id)
    setHistoryError('')
    try {
      const task = await convertCopilotRecommendationToTask(record.id)
      setCreatedTasks((currentTasks) => ({
        ...currentTasks,
        [record.id]: task,
      }))
      refreshHistory()
    } catch (requestError) {
      setHistoryError(requestError.message || '推荐转任务失败')
    } finally {
      setConvertingId(null)
    }
  }

  const handleRecommendationFeedback = async (record, feedbackStatus, feedbackRating) => {
    setFeedbackSavingId(`${record.id}:${feedbackStatus}`)
    setHistoryError('')
    try {
      const updatedRecord = await submitCopilotRecommendationFeedback(record.id, {
        feedback_status: feedbackStatus,
        feedback_rating: feedbackRating,
      })
      setHistoryRecords((records) => records.map((item) => (item.id === record.id ? updatedRecord : item)))
    } catch (requestError) {
      setHistoryError(requestError.message || '推荐反馈提交失败')
    } finally {
      setFeedbackSavingId(null)
    }
  }

  const handleAskCopilot = async (event) => {
    event.preventDefault()
    const question = askQuestion.trim()
    if (!question) {
      return
    }
    setAskLoading(true)
    setAskError('')
    try {
      const payload = await askCopilot({ question })
      setAskResult(payload)
      refreshHistory()
    } catch (requestError) {
      setAskError(requestError.message || '经营问答生成失败')
    } finally {
      setAskLoading(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <span className="crm-overline">AI Sales Copilot</span>
          <h2>智能销售副驾</h2>
          <p>基于商机阶段、金额、预计成交日期和客户上下文进行可解释评分，辅助销售人员判断优先级、风险和下一步动作。</p>
        </div>
        <div className="crm-copilot-summary">
          <Sparkles size={18} />
          <div className="crm-copilot-summary-copy">
            <AiText
              compact
              value={loading ? '正在从后端加载 AI 副驾建议...' : summary?.llm_summary ?? summary?.recommendation}
              fallback="后端 Copilot 暂无建议。"
            />
            <button className="crm-ghost-button" type="button" onClick={() => loadSummary({ force: true })} disabled={loading}>
              <RefreshCw size={15} />
              {loading ? '同步中' : '刷新副驾'}
            </button>
          </div>
        </div>
      </section>

      {error ? (
        <section className="crm-ai-alert">
          <Shield size={16} />
          <span>{error}</span>
        </section>
      ) : null}

      <section className="crm-metric-grid">
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-won">
            <Trophy size={18} />
          </div>
          <div>
            <span>最高优先级商机</span>
            <strong>{summary?.top_opportunity?.title ?? '暂无商机'}</strong>
            <small>{summary?.top_opportunity ? `${summary.top_opportunity.grade} 级 / ${summary.top_opportunity.rule_score} 分` : '等待后端数据'}</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-proposal">
            <TrendingUp size={18} />
          </div>
          <div>
            <span>AI 预测金额</span>
            <strong>{formatCurrency(summary?.forecast_amount ?? 0)}</strong>
            <small>A/B 级商机预估可转化金额</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-new">
            <Shield size={18} />
          </div>
          <div>
            <span>风险商机</span>
            <strong>{summary?.at_risk_count ?? 0}</strong>
            <small>低分或信息缺口明显的商机</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified">
            <Bot size={18} />
          </div>
          <div>
            <span>Copilot 模式</span>
            <strong>{summary?.fallback_used ? '规则兜底已启用' : 'LLM 增强已启用'}</strong>
            <small>后端 OpenAI 兼容接口 + 可解释评分</small>
          </div>
        </article>
      </section>

      <section className="crm-panel crm-ask-panel">
        <PanelHeader title="CRM Skill 经营问答" actionLabel={askResult?.fallback_used ? '规则兜底' : askResult ? 'LLM 增强' : '实时上下文'} />
        <form className="crm-ask-form" onSubmit={handleAskCopilot}>
          <label className="crm-field">
            <span>问题</span>
            <input value={askQuestion} onChange={(event) => setAskQuestion(event.target.value)} maxLength={500} />
          </label>
          <button className="crm-primary-button" type="submit" disabled={askLoading}>
            <Sparkles size={16} />
            {askLoading ? '分析中' : '询问 Copilot'}
          </button>
        </form>
        {askError ? (
          <div className="crm-ai-alert">
            <Shield size={16} />
            <span>{askError}</span>
          </div>
        ) : null}
        {askResult ? (
          <div className="crm-ask-result">
            <div className="crm-script-box">
              <span>{askResult.recommendation_id ? `${askResult.model} · 推荐历史 #${askResult.recommendation_id}` : askResult.model}</span>
              <AiText value={askResult.answer} />
            </div>
            <div className="crm-ask-columns">
              <CustomerPlanList title="证据片段" items={askResult.evidence ?? []} tone="accent" />
              <CustomerPlanList title="下一步动作" items={askResult.next_actions ?? []} tone="success" />
            </div>
          </div>
        ) : null}
      </section>

      <section className="crm-copilot-grid">
        <div className="crm-panel">
          <PanelHeader
            title="商机智能评分"
            actionLabel={scoreRulesOpen ? '收起评分规则' : '查看评分规则'}
            actionOnClick={() => setScoreRulesOpen((value) => !value)}
          />
          {scoreRulesOpen ? (
            <div className="crm-score-rules">
              <div>
                <strong>阶段权重</strong>
                <span>越接近 proposal / negotiation / won，基础分越高。</span>
              </div>
              <div>
                <strong>金额权重</strong>
                <span>高金额商机提升优先级，避免大单沉没在普通列表里。</span>
              </div>
              <div>
                <strong>紧急度</strong>
                <span>临近预计成交日期的商机会被优先提醒。</span>
              </div>
              <div>
                <strong>AI 辅助信号</strong>
                <span>AI 辅助录入或 Copilot 推荐会作为可解释加分项。</span>
              </div>
            </div>
          ) : null}
          <div className="crm-copilot-list">
            {loading ? <EmptyState icon={Bot} title="正在加载后端数据" subtitle="Copilot 将从 FastAPI 获取真实商机评分。" /> : null}
            {!loading && !insights.length ? <EmptyState icon={Bot} title="暂无商机评分" subtitle="请先初始化演示数据库。" /> : null}
            {insights.map((item) => (
              <button
                key={item.id}
                className={`crm-copilot-item ${selectedInsight?.id === item.id ? 'is-active' : ''}`}
                type="button"
                onClick={() => {
                  setSelectedId(String(item.id))
                  setFollowUp(null)
                }}
              >
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.customer_name} · {item.stage} · {item.due_date}</span>
                </div>
                <div className="crm-score-pill">
                  <span>{item.grade}</span>
                  <strong>{item.rule_score}</strong>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="crm-panel crm-copilot-detail">
          <PanelHeader title="下一步最佳动作" />
          {selectedInsight ? (
            <>
              <div className="crm-copilot-selected">
                <StatusBadge value={`${selectedInsight.grade} 级`} tone={selectedInsight.grade === 'A' ? 'success' : 'accent'} />
                <h3>{selectedInsight.title}</h3>
                <p>{selectedInsight.customer_name} 预计成交 {formatCurrency(selectedInsight.expected_amount)}，当前赢单概率 {formatPercent(selectedInsight.win_rate)}。</p>
              </div>
              <div className="crm-ai-note">
                <Sparkles size={18} />
                <span>{selectedInsight.next_best_action}</span>
              </div>
              <div className="crm-script-box">
                <span>AI 跟进话术草稿</span>
                <AiText
                  value={followUp?.message_draft}
                  fallback="点击下方按钮，后端将根据真实商机上下文调用 OpenAI 兼容接口生成话术；未配置密钥时返回规则兜底文案。"
                />
                <button className="crm-primary-button" type="button" onClick={handleGenerateFollowUp} disabled={generating}>
                  <Bot size={16} />
                  {generating ? '生成中...' : followUp ? '重新生成话术' : '生成跟进话术'}
                </button>
                {followUp ? (
                  <div className="crm-ai-text-note">
                    <AiText
                      compact
                      value={followUp.fallback_used ? '当前使用规则兜底，配置 SMART_CRM_LLM_API_KEY 后可启用真实 LLM。' : followUp.llm_summary}
                    />
                  </div>
                ) : null}
              </div>
            </>
          ) : (
            <EmptyState icon={Bot} title="暂无 Copilot 建议" subtitle="接入真实商机数据后将自动生成。" />
          )}
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="Copilot 推荐历史" actionLabel={historyLoading ? '同步中' : `${historyRecords.length} 条记录`} />
        {historyError ? (
          <div className="crm-ai-alert">
            <Shield size={16} />
            <span>{historyError}</span>
          </div>
        ) : null}
        <div className="crm-copilot-history">
          {historyRecords.map((record) => (
            <article key={record.id} className="crm-copilot-history-card">
              <div className="crm-copilot-history-head">
                <div>
                  <span>{record.source === 'follow_up' ? '跟进话术' : record.source === 'ask' ? '经营问答' : '摘要建议'} · {formatDateTime(record.created_at)}</span>
                  <strong>{record.lead_title || record.customer_name || '未命名推荐'}</strong>
                </div>
                <div className="crm-score-pill">
                  <span>{record.grade || '-'}</span>
                  <strong>{record.rule_score ?? 0}</strong>
                </div>
              </div>
              <AiText compact value={record.next_best_action || record.llm_summary} fallback="暂无建议内容" />
              {record.message_draft ? (
                <div className="crm-ai-text-note">
                  <AiText compact value={record.message_draft} />
                </div>
              ) : null}
              <div className="crm-copilot-history-meta">
                <span>{record.customer_name || '未知客户'}</span>
                <span>{record.stage || '未标记阶段'}</span>
                <span>{record.fallback_used ? '规则兜底' : 'LLM 增强'}</span>
                <span>{record.feedback_status ? `${copilotFeedbackLabelMap[record.feedback_status] ?? record.feedback_status} · ${record.feedback_rating || 0} 星` : '未评价'}</span>
              </div>
              <div className="crm-copilot-history-actions">
                <button
                  className="crm-ghost-button"
                  type="button"
                  onClick={() => handleCreateTask(record)}
                  disabled={convertingId === record.id}
                >
                  <CheckSquare size={15} />
                  {convertingId === record.id ? '生成中' : createdTasks[record.id] ? `任务 #${createdTasks[record.id].id}` : '转为任务'}
                </button>
                <button
                  className="crm-ghost-button"
                  type="button"
                  onClick={() => handleRecommendationFeedback(record, 'accepted', 5)}
                  disabled={feedbackSavingId === `${record.id}:accepted`}
                >
                  <CheckSquare size={15} />
                  {feedbackSavingId === `${record.id}:accepted` ? '保存中' : '已采纳'}
                </button>
                <button
                  className="crm-ghost-button"
                  type="button"
                  onClick={() => handleRecommendationFeedback(record, 'helpful', 4)}
                  disabled={feedbackSavingId === `${record.id}:helpful`}
                >
                  <Sparkles size={15} />
                  有帮助
                </button>
                <button
                  className="crm-ghost-button"
                  type="button"
                  onClick={() => handleRecommendationFeedback(record, 'not_helpful', 2)}
                  disabled={feedbackSavingId === `${record.id}:not_helpful`}
                >
                  <Shield size={15} />
                  不匹配
                </button>
                {createdTasks[record.id] ? (
                  <button className="crm-primary-button" type="button" onClick={() => navigate('/tasks')}>
                    <ArrowRight size={15} />
                    查看任务
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
        {!historyLoading && !historyError && !historyRecords.length ? (
          <EmptyState icon={Bot} title="暂无推荐历史" subtitle="打开副驾摘要、经营问答或生成跟进话术后会自动落库。" />
        ) : null}
      </section>
    </div>
  )
}

function AuthAuditPage() {
  const initialDraftFilters = { q: '', event: '', status: '' }
  const [draftFilters, setDraftFilters] = useState(initialDraftFilters)
  const [filters, setFilters] = useState({ ...initialDraftFilters, page: 1, per_page: 20 })
  const [pageState, setPageState] = useState({
    items: [],
    total: 0,
    page: 1,
    per_page: 20,
    pages: 1,
    has_next: false,
    has_previous: false,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exportSaving, setExportSaving] = useState(false)

  useEffect(() => {
    let mounted = true
    fetchAuthAuditLogs(filters)
      .then((payload) => {
        if (!mounted) {
          return
        }
        setPageState(normalizePaginatedPayload(payload, filters.page, filters.per_page))
        setError('')
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || '认证审计日志加载失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [filters])

  const logs = pageState.items
  const latestLog = logs[0]
  const pageSummary = useMemo(() => {
    const successCount = logs.filter((log) => log.status === 'success').length
    const failedCount = logs.filter((log) => log.status === 'failed').length
    const accountGovernanceCount = logs.filter((log) => ['profile_update', 'password_change', 'team_create', 'team_update'].includes(log.event)).length
    return { successCount, failedCount, accountGovernanceCount }
  }, [logs])

  const handleFilterChange = (name, value) => {
    setDraftFilters((current) => ({ ...current, [name]: value }))
  }

  const handleFilterSubmit = (event) => {
    event.preventDefault()
    setLoading(true)
    setFilters((current) => ({ ...current, ...draftFilters, page: 1 }))
  }

  const handleFilterReset = () => {
    setDraftFilters(initialDraftFilters)
    setLoading(true)
    setFilters({ ...initialDraftFilters, page: 1, per_page: 20 })
  }

  const handlePageChange = (nextPage) => {
    setLoading(true)
    setFilters((current) => ({ ...current, page: Math.max(1, nextPage) }))
  }

  const handleExportAuditLogs = async () => {
    setExportSaving(true)
    setError('')
    try {
      const { q, event, status } = filters
      const blob = await exportAuthAuditLogsCsv({ q, event, status })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `smart-crm-auth-audit-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.append(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (nextError) {
      setError(nextError.message || '认证审计导出失败')
    } finally {
      setExportSaving(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <span className="crm-overline">Auth Audit</span>
          <h2>认证审计</h2>
          <p>从后端认证审计表读取登录、注册、个人资料、密码和团队成员变更记录，验证账号治理、RBAC 和安全留痕。</p>
        </div>
        <div className="crm-copilot-summary">
          <KeyRound size={18} />
          <strong>{latestLog ? `最近一次为 ${authAuditEventLabelMap[latestLog.event] ?? latestLog.event}，账号 ${latestLog.account}，结果 ${authAuditStatusLabelMap[latestLog.status] ?? latestLog.status}。` : '登录、注册、改密码或维护团队账号后会自动写入认证审计。'}</strong>
        </div>
      </section>

      <form className="crm-panel crm-report-filter-bar" onSubmit={handleFilterSubmit}>
        <label className="crm-field">
          <span>关键词</span>
          <input placeholder="账号、事件、详情" value={draftFilters.q} onChange={(event) => handleFilterChange('q', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>事件</span>
          <select value={draftFilters.event} onChange={(event) => handleFilterChange('event', event.target.value)}>
            <option value="">全部事件</option>
            {Object.entries(authAuditEventLabelMap).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="crm-field">
          <span>状态</span>
          <select value={draftFilters.status} onChange={(event) => handleFilterChange('status', event.target.value)}>
            <option value="">全部状态</option>
            {Object.entries(authAuditStatusLabelMap).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <div className="crm-report-filter-actions">
          <button className="crm-primary-button" type="submit" disabled={loading}>
            <Filter size={16} />
            应用筛选
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleFilterReset} disabled={loading}>
            <RefreshCw size={16} />
            重置
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleExportAuditLogs} disabled={loading || exportSaving}>
            <Download size={16} />
            {exportSaving ? '导出中' : '导出 CSV'}
          </button>
        </div>
      </form>

      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-metric-grid crm-report-metric-grid">
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-accent">
            <KeyRound size={18} />
          </div>
          <div>
            <span>审计总数</span>
            <strong>{pageState.total}</strong>
            <small>后端分页查询的认证日志</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-won">
            <Shield size={18} />
          </div>
          <div>
            <span>本页成功</span>
            <strong>{pageSummary.successCount}</strong>
            <small>登录、资料或团队操作成功记录</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-danger">
            <Activity size={18} />
          </div>
          <div>
            <span>本页失败</span>
            <strong>{pageSummary.failedCount}</strong>
            <small>可用于演示账号风控与错误留痕</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified">
            <Users size={18} />
          </div>
          <div>
            <span>账号治理</span>
            <strong>{pageSummary.accountGovernanceCount}</strong>
            <small>资料、密码和团队成员维护记录</small>
          </div>
        </article>
      </section>

      <section className="crm-panel">
        <PanelHeader title="认证安全留痕" subtitle="由 FastAPI 认证、个人资料和团队管理接口自动写入" actionLabel={`第 ${pageState.page} / ${Math.max(1, pageState.pages)} 页`} />
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>事件</th>
                <th>状态</th>
                <th>账号</th>
                <th>用户</th>
                <th>组织</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatDateTime(log.created_at)}</td>
                  <td>{authAuditEventLabelMap[log.event] ?? log.event}</td>
                  <td>
                    <StatusBadge
                      value={authAuditStatusLabelMap[log.status] ?? log.status}
                      tone={log.status === 'success' ? 'success' : log.status === 'failed' ? 'danger' : 'neutral'}
                    />
                  </td>
                  <td>{log.account}</td>
                  <td>{log.user_id ? `#${log.user_id}` : '未绑定'}</td>
                  <td>{log.organization_id ? `#${log.organization_id}` : '未绑定'}</td>
                  <td>{log.detail || '无补充说明'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && !error && !logs.length ? <EmptyState icon={KeyRound} title="暂无认证审计记录" subtitle="尝试登录、修改资料、修改密码或创建团队成员后会出现在这里。" /> : null}
        <div className="crm-report-filter-actions crm-audit-pagination">
          <button className="crm-ghost-button" type="button" onClick={() => handlePageChange(pageState.page - 1)} disabled={loading || !pageState.has_previous}>
            <ChevronLeft size={16} />
            上一页
          </button>
          <span className="crm-muted-label">共 {pageState.total} 条，每页 {pageState.per_page} 条</span>
          <button className="crm-ghost-button" type="button" onClick={() => handlePageChange(pageState.page + 1)} disabled={loading || !pageState.has_next}>
            下一页
            <ChevronRight size={16} />
          </button>
        </div>
      </section>
    </div>
  )
}

function AiAuditPage() {
  const initialDraftFilters = { q: '', operation: '', entity_type: '', fallback_used: '' }
  const [draftFilters, setDraftFilters] = useState(initialDraftFilters)
  const [filters, setFilters] = useState({ ...initialDraftFilters, page: 1, per_page: 20 })
  const [pageState, setPageState] = useState({
    items: [],
    total: 0,
    page: 1,
    per_page: 20,
    pages: 1,
    has_next: false,
    has_previous: false,
  })
  const [qualityReport, setQualityReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exportSaving, setExportSaving] = useState(false)

  useEffect(() => {
    let mounted = true
    Promise.all([fetchAiAuditLogs(filters), fetchAiQualityReport()])
      .then(([payload, report]) => {
        if (mounted) {
          setPageState(normalizePaginatedPayload(payload, filters.page, filters.per_page))
          setQualityReport(report)
          setError('')
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || 'AI 审计日志加载失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [filters])

  const logs = pageState.items
  const qualityMetrics = useMemo(() => buildDashboardMetrics(qualityReport), [qualityReport])
  const operationBreakdown = qualityReport?.operation_breakdown ?? []
  const modelBreakdown = qualityReport?.model_breakdown ?? []
  const recommendationSignal = qualityReport?.recommendation_signal
  const handleFilterChange = (name, value) => {
    setDraftFilters((current) => ({ ...current, [name]: value }))
  }

  const handleFilterSubmit = (event) => {
    event.preventDefault()
    setLoading(true)
    setFilters((current) => ({ ...current, ...draftFilters, page: 1 }))
  }

  const handleFilterReset = () => {
    setDraftFilters(initialDraftFilters)
    setLoading(true)
    setFilters({ ...initialDraftFilters, page: 1, per_page: 20 })
  }

  const handlePageChange = (nextPage) => {
    setLoading(true)
    setFilters((current) => ({ ...current, page: Math.max(1, nextPage) }))
  }

  const handleExportAuditLogs = async () => {
    setExportSaving(true)
    setError('')
    try {
      const { q, operation, entity_type, fallback_used } = filters
      const blob = await exportAiAuditLogsCsv({ q, operation, entity_type, fallback_used })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `smart-crm-ai-audit-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.append(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (nextError) {
      setError(nextError.message || 'AI 审计导出失败')
    } finally {
      setExportSaving(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <span className="crm-overline">AI Audit</span>
          <h2>AI 调用审计</h2>
          <p>记录 Copilot、智能录单和订单草稿生成的运行状态、模型、耗时、兜底情况和关联对象，并用真实日志计算模型质量指标。</p>
        </div>
        <div className="crm-copilot-summary">
          <Shield size={18} />
          <strong>{qualityReport ? `已评估 ${qualityReport.metrics[0]?.value ?? 0} 次 AI 行为，最近一次为 ${logs[0] ? aiOperationLabelMap[logs[0].operation] ?? logs[0].operation : '暂无调用'}。` : '调用 AI 副驾或智能录单后会自动写入审计记录。'}</strong>
        </div>
      </section>

      <form className="crm-panel crm-report-filter-bar" onSubmit={handleFilterSubmit}>
        <label className="crm-field">
          <span>关键词</span>
          <input placeholder="操作、模型、摘要" value={draftFilters.q} onChange={(event) => handleFilterChange('q', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>操作</span>
          <select value={draftFilters.operation} onChange={(event) => handleFilterChange('operation', event.target.value)}>
            <option value="">全部操作</option>
            {Object.entries(aiOperationLabelMap).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="crm-field">
          <span>关联对象</span>
          <select value={draftFilters.entity_type} onChange={(event) => handleFilterChange('entity_type', event.target.value)}>
            <option value="">全部对象</option>
            <option value="customer">客户</option>
            <option value="lead">线索/商机</option>
            <option value="crm">CRM 上下文</option>
          </select>
        </label>
        <label className="crm-field">
          <span>运行模式</span>
          <select value={draftFilters.fallback_used} onChange={(event) => handleFilterChange('fallback_used', event.target.value)}>
            <option value="">全部模式</option>
            <option value="false">LLM 增强</option>
            <option value="true">规则兜底</option>
          </select>
        </label>
        <div className="crm-report-filter-actions">
          <button className="crm-primary-button" type="submit" disabled={loading}>
            <Filter size={16} />
            应用筛选
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleFilterReset} disabled={loading}>
            <RefreshCw size={16} />
            重置
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleExportAuditLogs} disabled={loading || exportSaving}>
            <Download size={16} />
            {exportSaving ? '导出中' : '导出 CSV'}
          </button>
        </div>
      </form>

      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-metric-grid">
        {qualityMetrics.map((metric) => (
          <article key={metric.label} className="crm-panel crm-metric-card">
            <div className={`crm-metric-icon tone-${metric.tone}`}>
              <metric.icon size={18} />
            </div>
            <div>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.hint}</small>
            </div>
          </article>
        ))}
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="AI 场景质量" subtitle={qualityReport?.generated_at ? `生成时间 ${formatDateTime(qualityReport.generated_at)}` : '按真实 AI 审计日志聚合'} />
          <div className="crm-progress-list">
            {operationBreakdown.map((item) => (
              <div key={item.operation} className="crm-progress-row">
                <div className="crm-progress-meta">
                  <div className={`crm-dot tone-${item.fallback_rate >= 0.5 ? 'danger' : item.fallback_rate > 0 ? 'warning' : 'success'}`} />
                  <span>{item.label}</span>
                  <strong>{item.total_count} 次 / 兜底 {formatPercent(item.fallback_rate)}</strong>
                </div>
                <div className="crm-progress-track">
                  <div className={`crm-progress-bar tone-${item.fallback_rate >= 0.5 ? 'danger' : item.fallback_rate > 0 ? 'warning' : 'success'}`} style={{ width: `${Math.max(4, (1 - item.fallback_rate) * 100)}%` }} />
                </div>
                <small>LLM {item.llm_count} 次，平均耗时 {item.average_latency_ms}ms</small>
              </div>
            ))}
            {!loading && !error && !operationBreakdown.length ? <EmptyState icon={Bot} title="暂无场景质量数据" subtitle="触发 AI 副驾、智能录单或客户经营计划后会显示。" /> : null}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="模型与推荐质量" actionLabel="日志 + 推荐历史" />
          <div className="crm-ai-impact">
            <div>
              <span>平均评分</span>
              <strong>{recommendationSignal?.average_rule_score ?? 0}</strong>
            </div>
            <div>
              <span>平均赢单率</span>
              <strong>{formatPercent(recommendationSignal?.average_win_rate ?? 0)}</strong>
            </div>
            <div>
              <span>推荐总数</span>
              <strong>{recommendationSignal?.total_recommendations ?? 0}</strong>
            </div>
            <div>
              <span>已转任务</span>
              <strong>{recommendationSignal?.converted_task_count ?? 0}</strong>
            </div>
            <div>
              <span>人工反馈</span>
              <strong>{recommendationSignal?.feedback_count ?? 0}</strong>
            </div>
            <div>
              <span>平均人工评分</span>
              <strong>{recommendationSignal?.average_feedback_rating ?? 0}</strong>
            </div>
            <div>
              <span>人工好评率</span>
              <strong>{formatPercent(recommendationSignal?.positive_feedback_rate ?? 0)}</strong>
            </div>
            <div className="crm-progress-track">
              <div className="crm-progress-bar tone-won" style={{ width: `${Math.max(4, Math.max(recommendationSignal?.conversion_rate ?? 0, recommendationSignal?.positive_feedback_rate ?? 0) * 100)}%` }} />
            </div>
            <small>
              推荐转任务率 {formatPercent(recommendationSignal?.conversion_rate ?? 0)}，人工好评率 {formatPercent(recommendationSignal?.positive_feedback_rate ?? 0)}，
              推荐兜底率 {formatPercent(recommendationSignal?.fallback_rate ?? 0)}
            </small>
          </div>
          <div className="crm-list compact">
            {modelBreakdown.map((item) => (
              <article key={item.model} className="crm-list-item">
                <div>
                  <strong>{item.model}</strong>
                  <span>{item.total_count} 次调用 / 平均 {item.average_latency_ms}ms</span>
                </div>
                <StatusBadge value={`兜底 ${formatPercent(item.fallback_rate)}`} tone={item.fallback_rate > 0 ? 'warning' : 'success'} />
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="最近兜底记录" subtitle="用于定位模型不可用、超时或配置缺失场景" />
        <div className="crm-list compact">
          {(qualityReport?.recent_fallbacks ?? []).map((log) => (
            <article key={log.id} className="crm-list-item">
              <div>
                <strong>{aiOperationLabelMap[log.operation] ?? log.operation}</strong>
                <span>{log.model || '未配置'} / {log.request_summary}</span>
              </div>
              <StatusBadge value={`${log.latency_ms}ms`} tone="warning" />
            </article>
          ))}
          {!loading && !error && !(qualityReport?.recent_fallbacks ?? []).length ? <EmptyState icon={Shield} title="暂无兜底记录" subtitle="当前 AI 调用均未触发规则兜底。" /> : null}
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="最近 AI 行为" actionLabel={`第 ${pageState.page} / ${Math.max(1, pageState.pages)} 页`} />
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>操作</th>
                <th>状态</th>
                <th>模型</th>
                <th>耗时</th>
                <th>请求摘要</th>
                <th>响应摘要</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatDateTime(log.created_at)}</td>
                  <td>{aiOperationLabelMap[log.operation] ?? log.operation}</td>
                  <td><StatusBadge value={log.fallback_used ? '兜底' : 'LLM'} tone={log.fallback_used ? 'warning' : 'success'} /></td>
                  <td>{log.model || '未配置'}</td>
                  <td>{log.latency_ms}ms</td>
                  <td>{log.request_summary}</td>
                  <td>{log.response_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && !error && !logs.length ? <EmptyState icon={Shield} title="暂无 AI 审计记录" subtitle="打开 AI 副驾、生成话术或上传智能录单材料后会自动出现记录。" /> : null}
        <div className="crm-report-filter-actions crm-audit-pagination">
          <button className="crm-ghost-button" type="button" onClick={() => handlePageChange(pageState.page - 1)} disabled={loading || !pageState.has_previous}>
            <ChevronLeft size={16} />
            上一页
          </button>
          <span className="crm-muted-label">共 {pageState.total} 条，每页 {pageState.per_page} 条</span>
          <button className="crm-ghost-button" type="button" onClick={() => handlePageChange(pageState.page + 1)} disabled={loading || !pageState.has_next}>
            下一页
            <ChevronRight size={16} />
          </button>
        </div>
      </section>
    </div>
  )
}

function BusinessAuditPage() {
  const initialDraftFilters = { q: '', action: '', entity_type: '', operator: '', status: '' }
  const [draftFilters, setDraftFilters] = useState(initialDraftFilters)
  const [filters, setFilters] = useState({ ...initialDraftFilters, page: 1, per_page: 20 })
  const [pageState, setPageState] = useState({
    items: [],
    total: 0,
    page: 1,
    per_page: 20,
    pages: 1,
    has_next: false,
    has_previous: false,
  })
  const [consistency, setConsistency] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exportSaving, setExportSaving] = useState(false)

  useEffect(() => {
    let mounted = true
    Promise.all([fetchBusinessAuditLogs(filters), fetchConsistencyChecks()])
      .then(([payload, consistencyPayload]) => {
        if (mounted) {
          setPageState(normalizePaginatedPayload(payload, filters.page, filters.per_page))
          setConsistency(consistencyPayload)
          setError('')
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || '操作审计日志加载失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [filters])

  const logs = pageState.items
  const latestLog = logs[0]
  const summary = useMemo(() => {
    const orderCount = logs.filter((log) => log.entity_type === 'order').length
    const stockCount = logs.filter((log) => log.action === 'restock' || log.summary.includes('库存')).length
    return {
      orderCount,
      stockCount,
      issueCount: consistency?.issue_count ?? 0,
      criticalCount: consistency?.critical_count ?? 0,
    }
  }, [consistency, logs])

  const handleFilterChange = (name, value) => {
    setDraftFilters((current) => ({ ...current, [name]: value }))
  }

  const handleFilterSubmit = (event) => {
    event.preventDefault()
    setLoading(true)
    setFilters((current) => ({ ...current, ...draftFilters, page: 1 }))
  }

  const handleFilterReset = () => {
    setDraftFilters(initialDraftFilters)
    setLoading(true)
    setFilters({ ...initialDraftFilters, page: 1, per_page: 20 })
  }

  const handlePageChange = (nextPage) => {
    setLoading(true)
    setFilters((current) => ({ ...current, page: Math.max(1, nextPage) }))
  }

  const handleExportAuditLogs = async () => {
    setExportSaving(true)
    setError('')
    try {
      const { q, action, entity_type, operator, status } = filters
      const blob = await exportBusinessAuditLogsCsv({ q, action, entity_type, operator, status })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `smart-crm-business-audit-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.append(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (nextError) {
      setError(nextError.message || '业务审计导出失败')
    } finally {
      setExportSaving(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <span className="crm-overline">Business Audit</span>
          <h2>业务操作审计</h2>
          <p>记录客户、商品、订单和补货等真实写库动作，展示操作人、对象、摘要和细节，证明系统具备可追踪的业务治理能力。</p>
        </div>
        <div className="crm-copilot-summary">
          <ClipboardList size={18} />
          <strong>{latestLog ? `当前筛选命中 ${pageState.total} 次业务操作，最近一次为 ${businessActionLabelMap[latestLog.action] ?? latestLog.action} ${businessEntityLabelMap[latestLog.entity_type] ?? latestLog.entity_type}。` : '创建客户、商品、订单或补货后会自动写入业务审计。'}</strong>
        </div>
      </section>

      <form className="crm-panel crm-report-filter-bar" onSubmit={handleFilterSubmit}>
        <label className="crm-field">
          <span>关键词</span>
          <input placeholder="摘要、细节、操作人" value={draftFilters.q} onChange={(event) => handleFilterChange('q', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>动作</span>
          <select value={draftFilters.action} onChange={(event) => handleFilterChange('action', event.target.value)}>
            <option value="">全部动作</option>
            {Object.entries(businessActionLabelMap).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="crm-field">
          <span>对象</span>
          <select value={draftFilters.entity_type} onChange={(event) => handleFilterChange('entity_type', event.target.value)}>
            <option value="">全部对象</option>
            {Object.entries(businessEntityLabelMap).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="crm-field">
          <span>操作人</span>
          <input placeholder="如 李伟超" value={draftFilters.operator} onChange={(event) => handleFilterChange('operator', event.target.value)} />
        </label>
        <label className="crm-field">
          <span>状态</span>
          <select value={draftFilters.status} onChange={(event) => handleFilterChange('status', event.target.value)}>
            <option value="">全部状态</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
          </select>
        </label>
        <div className="crm-report-filter-actions">
          <button className="crm-primary-button" type="submit" disabled={loading}>
            <Filter size={16} />
            应用筛选
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleFilterReset} disabled={loading}>
            <RefreshCw size={16} />
            重置
          </button>
          <button className="crm-ghost-button" type="button" onClick={handleExportAuditLogs} disabled={loading || exportSaving}>
            <Download size={16} />
            {exportSaving ? '导出中' : '导出 CSV'}
          </button>
        </div>
      </form>

      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-metric-grid">
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-accent">
            <ClipboardList size={18} />
          </div>
          <div>
            <span>审计记录</span>
            <strong>{pageState.total}</strong>
            <small>当前筛选命中的真实业务日志</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified">
            <Activity size={18} />
          </div>
          <div>
            <span>订单动作</span>
            <strong>{summary.orderCount}</strong>
            <small>订单创建、编辑和明细调整</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-proposal">
            <Package size={18} />
          </div>
          <div>
            <span>库存相关</span>
            <strong>{summary.stockCount}</strong>
            <small>补货或库存调整行为</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-won">
            <Shield size={18} />
          </div>
          <div>
            <span>一致性巡检</span>
            <strong>{summary.issueCount}</strong>
            <small>{summary.criticalCount ? `${summary.criticalCount} 个严重问题` : '跨表关系实时校验'}</small>
          </div>
        </article>
      </section>

      <section className="crm-panel">
        <PanelHeader title="跨表一致性巡检" subtitle={consistency ? `生成时间 ${formatDateTime(consistency.generated_at)} / ${consistency.total_checks} 项检查` : '正在检查订单、库存、审批和客户关系'} />
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th>类别</th>
                <th>状态</th>
                <th>检查项</th>
                <th>详情</th>
                <th>建议</th>
              </tr>
            </thead>
            <tbody>
              {(consistency?.checks ?? []).map((check) => (
                <tr key={check.id}>
                  <td>{check.category}</td>
                  <td>
                    <StatusBadge
                      value={check.status === 'ok' ? '正常' : check.severity === 'critical' ? '严重' : '提醒'}
                      tone={check.status === 'ok' ? 'success' : check.severity === 'critical' ? 'danger' : 'warning'}
                    />
                  </td>
                  <td>{check.title}</td>
                  <td>{check.detail}</td>
                  <td>{check.suggestion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && !error && consistency && !consistency.checks.length ? <EmptyState icon={Shield} title="暂无巡检项" subtitle="数据库初始化后会自动展示跨表一致性检查。" /> : null}
      </section>

      <section className="crm-panel">
        <PanelHeader title="最近业务操作" actionLabel={`第 ${pageState.page} / ${Math.max(1, pageState.pages)} 页`} />
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>动作</th>
                <th>对象</th>
                <th>操作人</th>
                <th>状态</th>
                <th>摘要</th>
                <th>细节</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatDateTime(log.created_at)}</td>
                  <td>{businessActionLabelMap[log.action] ?? log.action}</td>
                  <td>{businessEntityLabelMap[log.entity_type] ?? log.entity_type} #{log.entity_id ?? '-'}</td>
                  <td>{log.operator || '系统'}</td>
                  <td><StatusBadge value={log.status === 'success' ? '成功' : log.status} tone={log.status === 'success' ? 'success' : 'warning'} /></td>
                  <td>{log.summary}</td>
                  <td>{log.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && !error && !logs.length ? <EmptyState icon={ClipboardList} title="暂无业务审计记录" subtitle="创建客户、商品、订单或执行补货后会自动出现记录。" /> : null}
        <div className="crm-report-filter-actions crm-audit-pagination">
          <button className="crm-ghost-button" type="button" onClick={() => handlePageChange(pageState.page - 1)} disabled={loading || !pageState.has_previous}>
            <ChevronLeft size={16} />
            上一页
          </button>
          <span className="crm-muted-label">共 {pageState.total} 条，每页 {pageState.per_page} 条</span>
          <button className="crm-ghost-button" type="button" onClick={() => handlePageChange(pageState.page + 1)} disabled={loading || !pageState.has_next}>
            下一页
            <ChevronRight size={16} />
          </button>
        </div>
      </section>
    </div>
  )
}

function PermissionMatrixPage() {
  const [matrix, setMatrix] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    fetchPermissionMatrix()
      .then((payload) => {
        if (mounted) {
          setMatrix(payload)
          setError('')
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || '权限矩阵加载失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  const roles = useMemo(() => matrix?.roles ?? [], [matrix])
  const permissions = useMemo(() => matrix?.permission_catalog ?? [], [matrix])
  const modules = useMemo(() => matrix?.modules ?? [], [matrix])
  const permissionMap = useMemo(() => new Map(permissions.map((permission) => [permission.key, permission])), [permissions])
  const roleHasPermission = (role, permissionKey) => role.all_permissions || role.permissions.includes(permissionKey)

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <span className="crm-overline">Access Governance</span>
          <h2>权限矩阵</h2>
          <p>从 FastAPI 后端 RBAC 策略读取角色、权限和模块访问关系，验证菜单隐藏和接口 403 的规则来源。</p>
        </div>
        <div className="crm-copilot-summary">
          <KeyRound size={18} />
          <strong>{matrix ? `当前角色 ${matrix.current_role}，共 ${roles.length} 个角色、${permissions.length} 项权限、${modules.length} 个模块。` : '正在读取后端权限策略。'}</strong>
        </div>
      </section>

      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-metric-grid">
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-accent">
            <Users size={18} />
          </div>
          <div>
            <span>角色数量</span>
            <strong>{roles.length}</strong>
            <small>来自后端 ROLE_PERMISSIONS</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified">
            <KeyRound size={18} />
          </div>
          <div>
            <span>权限项</span>
            <strong>{permissions.length}</strong>
            <small>接口级权限目录</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-proposal">
            <LayoutGrid size={18} />
          </div>
          <div>
            <span>前端模块</span>
            <strong>{modules.length}</strong>
            <small>与侧栏模块权限一致</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-won">
            <Shield size={18} />
          </div>
          <div>
            <span>当前角色</span>
            <strong>{matrix?.current_role ?? '-'}</strong>
            <small>由 Bearer token 解析</small>
          </div>
        </article>
      </section>

      <section className="crm-three-col-grid">
        {roles.map((role) => (
          <article key={role.role} className="crm-panel crm-permission-role-card">
            <div className="crm-permission-role-head">
              <div>
                <span className="crm-overline">Role</span>
                <h3>{role.role}</h3>
              </div>
              <div className="crm-stack-inline">
                <StatusBadge value={dataScopeLabelMap[role.data_scope] ?? role.data_scope ?? '全量数据'} tone={role.data_scope === 'own' ? 'warning' : 'success'} />
                <StatusBadge value={role.all_permissions ? '全部权限' : `${role.granted_count} 项`} tone={role.all_permissions ? 'success' : 'accent'} />
              </div>
            </div>
            <p>{role.description}</p>
            <div className="crm-permission-chip-list">
              {role.permissions.slice(0, 8).map((permissionKey) => (
                <span key={permissionKey}>{permissionMap.get(permissionKey)?.label ?? permissionKey}</span>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="crm-panel">
        <PanelHeader title="权限项矩阵" actionLabel="角色 x 接口能力" />
        <div className="crm-table-wrap">
          <table className="crm-table crm-permission-table">
            <thead>
              <tr>
                <th>权限</th>
                <th>分类</th>
                {roles.map((role) => (
                  <th key={role.role}>{role.role}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {permissions.map((permission) => (
                <tr key={permission.key}>
                  <td>
                    <strong>{permission.label}</strong>
                    <span>{permission.key}</span>
                    <small>{permission.description}</small>
                  </td>
                  <td>{permission.category}</td>
                  {roles.map((role) => (
                    <td key={`${role.role}-${permission.key}`}>
                      <span className={`crm-check-cell ${roleHasPermission(role, permission.key) ? 'is-allowed' : ''}`}>
                        {roleHasPermission(role, permission.key) ? '允许' : '拒绝'}
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="模块访问矩阵" actionLabel="侧栏模块 x 角色" />
        <div className="crm-table-wrap">
          <table className="crm-table crm-permission-table">
            <thead>
              <tr>
                <th>模块</th>
                <th>路由</th>
                <th>所需权限</th>
                <th>可访问角色</th>
              </tr>
            </thead>
            <tbody>
              {modules.map((module) => (
                <tr key={module.path}>
                  <td>{module.label}</td>
                  <td>{module.path}</td>
                  <td>{permissionMap.get(module.permission)?.label ?? module.permission}</td>
                  <td>
                    <div className="crm-permission-chip-list">
                      {module.roles.map((role) => (
                        <span key={`${module.path}-${role}`}>{role}</span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && !error && !modules.length ? <EmptyState icon={KeyRound} title="暂无权限矩阵" subtitle="后端权限策略为空时会显示在这里。" /> : null}
      </section>
    </div>
  )
}

function CapturePage() {
  const { userProfile: activeProfile } = useOutletContext()
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [catalog, setCatalog] = useState({ customers: [], products: [] })
  const [captureDrafts, setCaptureDrafts] = useState([])
  const [draftStatusFilter, setDraftStatusFilter] = useState('draft')
  const [submittedOrder, setSubmittedOrder] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [draftsLoading, setDraftsLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [draftUpdatingId, setDraftUpdatingId] = useState(null)
  const [reviewSaving, setReviewSaving] = useState(false)
  const [error, setError] = useState('')

  const loadCaptureDrafts = useCallback(() => {
    setDraftsLoading(true)
    const params = { page: 1, per_page: 6 }
    if (draftStatusFilter !== 'all') {
      params.status = draftStatusFilter
    }
    return fetchCaptureDrafts(params)
      .then((payload) => {
        const items = Array.isArray(payload) ? payload : payload.items ?? []
        setCaptureDrafts(items)
      })
      .catch((nextError) => {
        setError(nextError.message || '智能录单草稿加载失败')
      })
      .finally(() => {
        setDraftsLoading(false)
      })
  }, [draftStatusFilter])

  useEffect(() => {
    let mounted = true
    Promise.all([fetchCustomers(), fetchProducts()])
      .then(([customers, products]) => {
        if (mounted) {
          setCatalog({ customers, products })
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || '客户/商品目录加载失败')
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    loadCaptureDrafts()
  }, [loadCaptureDrafts])

  const totalAmount = useMemo(() => {
    if (!result?.items?.length) {
      return 0
    }
    return result.items.reduce((total, item) => total + Number(item.quantity) * Number(item.unit_price), 0)
  }, [result])

  const normalizeCaptureResult = (draft) => ({
    ...draft,
    capture_draft_id: draft?.capture_draft_id ?? draft?.id ?? null,
    items: draft?.items ?? [],
    status: draft?.status ?? 'draft',
  })

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!file) {
      setError('请选择订单图片或文本文件')
      return
    }

    setExtracting(true)
    setError('')
    extractOrderFromFile(file)
      .then((payload) => {
        setResult(normalizeCaptureResult({ ...payload, status: 'draft' }))
        setSubmittedOrder(null)
        if (draftStatusFilter === 'draft') {
          loadCaptureDrafts()
        } else {
          setDraftStatusFilter('draft')
        }
      })
      .catch((nextError) => {
        setError(nextError.message || '智能录单失败')
      })
      .finally(() => {
        setExtracting(false)
      })
  }

  const handleCreateOrder = async () => {
    if (!result) {
      return
    }
    if (result.status && result.status !== 'draft') {
      setError(result.status === 'submitted' ? '该草稿已经提交为订单，不能重复提交' : '已作废草稿不能提交订单')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const payload = buildOrderPayloadFromCapture({
        captureResult: result,
        customers: catalog.customers,
        products: catalog.products,
        owner: activeProfile.name,
        region: '华南',
      })
      const order = await createOrder(payload)
      setSubmittedOrder(order)
      if (result.capture_draft_id) {
        const updatedDraft = await updateCaptureDraft(result.capture_draft_id, {
          status: 'submitted',
          submitted_order_id: order.id,
        })
        setResult((current) => current?.capture_draft_id === updatedDraft.id ? { ...current, status: updatedDraft.status, submitted_order_id: updatedDraft.submitted_order_id } : current)
        setCaptureDrafts((current) => {
          const withoutUpdated = current.filter((draft) => draft.id !== updatedDraft.id)
          if (draftStatusFilter === 'draft' || draftStatusFilter === 'discarded') {
            return withoutUpdated
          }
          return [updatedDraft, ...withoutUpdated]
        })
      }
    } catch (nextError) {
      setError(nextError.message || '订单提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCaptureFieldChange = (field, value) => {
    setResult((current) => current ? { ...current, [field]: value } : current)
  }

  const handleCaptureCustomerSelect = (value) => {
    const customerId = Number(value)
    const customer = Number.isFinite(customerId) ? catalog.customers.find((item) => Number(item.id) === customerId) : null
    setResult((current) => {
      if (!current) {
        return current
      }
      if (!customer) {
        return { ...current, customer_id: null }
      }
      return {
        ...current,
        customer_id: customer.id,
        company: customer.company,
        customer_name: customer.contact_person,
      }
    })
  }

  const handleCaptureItemChange = (index, field, value) => {
    setResult((current) => {
      if (!current) {
        return current
      }
      const items = [...(current.items ?? [])]
      const existing = items[index] ?? { product_id: null, product_name: '', quantity: 1, unit_price: 1 }
      if (field === 'product_id') {
        const productId = Number(value)
        const product = Number.isFinite(productId) ? catalog.products.find((item) => Number(item.id) === productId) : null
        items[index] = product
          ? { ...existing, product_id: product.id, product_name: product.name, unit_price: product.unit_price }
          : { ...existing, product_id: null }
      } else {
        items[index] = { ...existing, [field]: value }
      }
      return { ...current, items }
    })
  }

  const handleAddCaptureItem = () => {
    const product = catalog.products[0]
    setResult((current) => {
      if (!current) {
        return current
      }
      const nextItem = product
        ? { product_id: product.id, product_name: product.name, quantity: 1, unit_price: product.unit_price }
        : { product_id: null, product_name: '', quantity: 1, unit_price: 1 }
      return { ...current, items: [...(current.items ?? []), nextItem] }
    })
  }

  const handleRemoveCaptureItem = (index) => {
    setResult((current) => {
      if (!current) {
        return current
      }
      const items = (current.items ?? []).filter((_, itemIndex) => itemIndex !== index)
      return { ...current, items }
    })
  }

  const handleSaveCaptureReview = async () => {
    if (!result?.capture_draft_id) {
      setError('当前草稿尚未保存到后端，无法保存修正')
      return
    }
    setReviewSaving(true)
    setError('')
    try {
      const updatedDraft = await updateCaptureDraft(result.capture_draft_id, {
        customer_id: result.customer_id ? Number(result.customer_id) : null,
        company: result.company,
        customer_name: result.customer_name,
        confidence: Number(result.confidence ?? 0),
        summary: result.summary,
        suggested_notes: result.suggested_notes,
        items: (result.items ?? []).map((item) => ({
          product_id: item.product_id ? Number(item.product_id) : null,
          product_name: item.product_name,
          quantity: Math.max(Number(item.quantity) || 1, 1),
          unit_price: Math.max(Number(item.unit_price) || 0, 0.01),
        })),
      })
      const normalizedDraft = normalizeCaptureResult(updatedDraft)
      setResult(normalizedDraft)
      setCaptureDrafts((current) => [updatedDraft, ...current.filter((draft) => draft.id !== updatedDraft.id)])
    } catch (nextError) {
      setError(nextError.message || '草稿修正保存失败')
    } finally {
      setReviewSaving(false)
    }
  }

  const handleDiscardDraft = async (draft) => {
    if (!draft?.id || draft.status !== 'draft') {
      return
    }
    setDraftUpdatingId(draft.id)
    setError('')
    try {
      const updatedDraft = await updateCaptureDraft(draft.id, { status: 'discarded' })
      setCaptureDrafts((current) => {
        if (draftStatusFilter === 'draft') {
          return current.filter((item) => item.id !== updatedDraft.id)
        }
        return [updatedDraft, ...current.filter((item) => item.id !== updatedDraft.id)]
      })
      setResult((current) => current?.capture_draft_id === updatedDraft.id ? { ...current, status: updatedDraft.status } : current)
    } catch (nextError) {
      setError(nextError.message || '草稿作废失败')
    } finally {
      setDraftUpdatingId(null)
    }
  }

  const selectedResultStatus = result?.status ?? 'draft'
  const selectedResultLocked = selectedResultStatus !== 'draft'
  const selectedResultOrderId = submittedOrder?.id ?? result?.submitted_order_id
  const canEditCaptureDraft = Boolean(result?.capture_draft_id) && !selectedResultLocked
  const captureDraftStatusOptions = [
    { value: 'draft', label: '草稿' },
    { value: 'submitted', label: '已提交' },
    { value: 'discarded', label: '已作废' },
    { value: 'all', label: '全部' },
  ]

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-copilot-hero">
        <div>
          <span className="crm-overline">AI Capture</span>
          <h2>智能录单</h2>
          <p>上传订单图片、报价单截图或文本文件，生成可复核的订单草稿。</p>
        </div>
        <div className="crm-score-pill">
          <UploadCloud size={18} />
          <span>{result?.fallback_used ? '兜底解析' : result ? '模型抽取' : '等待上传'}</span>
        </div>
      </section>

      <ResourceSyncState loading={extracting || submitting} error={error} />

      <section className="crm-dashboard-grid">
        <form className="crm-panel" onSubmit={handleSubmit}>
          <PanelHeader title="上传材料" />
          <label className="crm-field">
            <span>订单文件</span>
            <input
              type="file"
              accept="image/*,.txt,.csv,.md,.json"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null)
              }}
            />
          </label>
          <button className="crm-primary-button" type="submit" disabled={extracting}>
            <UploadCloud size={16} />
            {extracting ? '生成中' : '生成草稿'}
          </button>
          <small>已加载 {catalog.customers.length} 个客户、{catalog.products.length} 个商品用于自动匹配。</small>
        </form>

        <div className="crm-panel">
          <PanelHeader title="抽取结果" />
          {result ? (
            <div className="crm-progress-list">
              <div className="crm-list-item">
                <div>
                  <strong>{result.company}</strong>
                  <span>{result.customer_name} · {result.customer_id ? `已匹配客户 #${result.customer_id}` : '待人工匹配客户'}</span>
                </div>
                <StatusBadge value={formatPercent(result.confidence)} tone={result.confidence >= 0.8 ? 'success' : 'warning'} />
              </div>
              <div className="crm-form-grid">
                <label className="crm-field">
                  <span>匹配客户</span>
                  <select value={result.customer_id ?? ''} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureCustomerSelect(event.target.value)}>
                    <option value="">待人工匹配</option>
                    {catalog.customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>{customer.company} / {customer.contact_person}</option>
                    ))}
                  </select>
                </label>
                <label className="crm-field">
                  <span>客户公司</span>
                  <input value={result.company ?? ''} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureFieldChange('company', event.target.value)} />
                </label>
                <label className="crm-field">
                  <span>联系人</span>
                  <input value={result.customer_name ?? ''} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureFieldChange('customer_name', event.target.value)} />
                </label>
                <label className="crm-field">
                  <span>置信度</span>
                  <input type="number" min="0" max="1" step="0.01" value={result.confidence ?? 0} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureFieldChange('confidence', event.target.value)} />
                </label>
              </div>
              <div className="crm-list-item">
                <div>
                  <strong>{result.source}</strong>
                  <span>{result.fallback_used ? '已使用兜底解析' : '模型抽取成功'}</span>
                </div>
                <div className="crm-list-value">{formatCurrency(totalAmount)}</div>
              </div>
              {submittedOrder ? (
                <div className="crm-list-item">
                  <div>
                    <strong>订单 #{submittedOrder.id}</strong>
                    <span>{submittedOrder.customer_name} · {submittedOrder.items.length} 个条目</span>
                  </div>
                  <StatusBadge value={submittedOrder.status} tone="success" />
                </div>
              ) : null}
              <label className="crm-field">
                <span>抽取摘要</span>
                <textarea rows={3} value={result.summary ?? ''} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureFieldChange('summary', event.target.value)} />
              </label>
            </div>
          ) : (
            <EmptyState icon={UploadCloud} title="暂无草稿" subtitle="上传材料后会显示结构化订单草稿。" />
          )}
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="最近草稿" subtitle={draftsLoading ? '同步中' : `${captureDrafts.length} 条`} actionLabel="后端持久化" />
        <div className="crm-tabs" role="tablist" aria-label="智能录单草稿状态">
          {captureDraftStatusOptions.map((option) => (
            <button
              key={option.value}
              className={draftStatusFilter === option.value ? 'is-active' : ''}
              type="button"
              onClick={() => setDraftStatusFilter(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="crm-progress-list">
          {captureDrafts.map((draft) => (
            <div className="crm-list-item" key={draft.id}>
              <div>
                <strong>{draft.company || '待复核客户'} · #{draft.id}</strong>
                <span>{draft.customer_name || '待复核联系人'} · {draft.items?.length ?? 0} 个条目 · {draft.submitted_order_id ? `订单 #${draft.submitted_order_id}` : draft.source}</span>
              </div>
              <div className="crm-toolbar-actions">
                <StatusBadge value={draft.status === 'submitted' ? '已提交' : draft.status === 'discarded' ? '已作废' : '草稿'} tone={draft.status === 'submitted' ? 'success' : draft.status === 'discarded' ? 'danger' : 'warning'} />
                <button
                  className="crm-ghost-button"
                  type="button"
                  onClick={() => {
                    setResult(normalizeCaptureResult(draft))
                    setSubmittedOrder(draft.submitted_order_id ? { id: draft.submitted_order_id, customer_name: draft.company, items: draft.items ?? [], status: 'submitted' } : null)
                  }}
                >
                  载入草稿
                </button>
                {draft.status === 'draft' ? (
                  <button
                    className="crm-ghost-button crm-ghost-button--danger"
                    type="button"
                    disabled={draftUpdatingId === draft.id}
                    onClick={() => handleDiscardDraft(draft)}
                  >
                    <Trash2 size={14} />
                    {draftUpdatingId === draft.id ? '作废中' : '作废'}
                  </button>
                ) : null}
              </div>
            </div>
          ))}
          {!draftsLoading && !captureDrafts.length ? <EmptyState icon={ClipboardList} title="暂无智能录单草稿" subtitle="上传材料后，后端会保存一条可复核草稿。" /> : null}
        </div>
      </section>

      {result?.items?.length ? (
        <section className="crm-panel">
          <PanelHeader title="订单条目" />
          <div className="crm-table-wrap">
            <table className="crm-table">
              <thead>
                <tr>
                  <th>商品</th>
                  <th>匹配</th>
                  <th>数量</th>
                  <th>单价</th>
                  <th>小计</th>
                  <th className="crm-table-actions-cell">操作</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((item, index) => (
                  <tr key={`${item.product_name}-${item.quantity}-${item.unit_price}`}>
                    <td>
                      <div className="crm-table-stack">
                        <select value={item.product_id ?? ''} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureItemChange(index, 'product_id', event.target.value)}>
                          <option value="">待匹配商品</option>
                          {catalog.products.map((product) => (
                            <option key={product.id} value={product.id}>{product.name} / {product.sku}</option>
                          ))}
                        </select>
                        <input value={item.product_name ?? ''} disabled={!canEditCaptureDraft || Boolean(item.product_id)} onChange={(event) => handleCaptureItemChange(index, 'product_name', event.target.value)} />
                      </div>
                    </td>
                    <td>{item.product_id ? `#${item.product_id}` : '待匹配'}</td>
                    <td>
                      <input type="number" min="1" step="1" value={item.quantity} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureItemChange(index, 'quantity', event.target.value)} />
                    </td>
                    <td>
                      <input type="number" min="0.01" step="0.01" value={item.unit_price} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureItemChange(index, 'unit_price', event.target.value)} />
                    </td>
                    <td>{formatCurrency(item.quantity * item.unit_price)}</td>
                    <td className="crm-table-actions-cell">
                      {canEditCaptureDraft ? (
                        <button className="crm-icon-button" type="button" title="移除条目" onClick={() => handleRemoveCaptureItem(index)} disabled={result.items.length <= 1}>
                          <Trash2 size={15} />
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <label className="crm-field">
            <span>复核备注</span>
            <textarea rows={3} value={result.suggested_notes ?? ''} disabled={!canEditCaptureDraft} onChange={(event) => handleCaptureFieldChange('suggested_notes', event.target.value)} />
          </label>
          {selectedResultLocked ? (
            <div className="crm-form-warning">
              {selectedResultStatus === 'submitted'
                ? `该草稿已提交为订单${selectedResultOrderId ? ` #${selectedResultOrderId}` : ''}，不能重复提交。`
                : '该草稿已作废，仅保留为审计记录，不能提交订单。'}
            </div>
          ) : null}
          <div className="crm-toolbar-actions">
            {canEditCaptureDraft ? (
              <>
                <button className="crm-ghost-button" type="button" onClick={handleAddCaptureItem}>
                  <Plus size={16} />
                  添加条目
                </button>
                <button className="crm-ghost-button" type="button" onClick={handleSaveCaptureReview} disabled={reviewSaving}>
                  <Save size={16} />
                  {reviewSaving ? '保存中' : '保存草稿修正'}
                </button>
              </>
            ) : null}
            <button className="crm-primary-button" type="button" onClick={handleCreateOrder} disabled={submitting || selectedResultLocked || Boolean(submittedOrder)}>
              <CheckSquare size={16} />
              {selectedResultLocked ? (selectedResultStatus === 'submitted' ? '已提交订单' : '已作废') : submittedOrder ? '已提交订单' : submitting ? '提交中' : '复核并提交订单'}
            </button>
            {submittedOrder && Number.isFinite(Number(submittedOrder.total_amount)) ? <span className="crm-list-value">{formatCurrency(submittedOrder.total_amount)}</span> : null}
          </div>
          {result.raw_text_excerpt ? <small>{result.raw_text_excerpt}</small> : null}
        </section>
      ) : null}
    </div>
  )
}

function OrdersPage() {
  const navigate = useNavigate()
  const { userProfile: activeProfile } = useOutletContext()
  const [orders, setOrders] = useState([])
  const [orderApprovals, setOrderApprovals] = useState([])
  const [products, setProducts] = useState([])
  const [restockAlerts, setRestockAlerts] = useState([])
  const [inventoryMovements, setInventoryMovements] = useState([])
  const [selectedOrderMovements, setSelectedOrderMovements] = useState([])
  const [loading, setLoading] = useState(true)
  const [restockSavingId, setRestockSavingId] = useState(null)
  const [exportSaving, setExportSaving] = useState(false)
  const [orderEditOpen, setOrderEditOpen] = useState(false)
  const [orderSaving, setOrderSaving] = useState(false)
  const [approvalSavingId, setApprovalSavingId] = useState(null)
  const [approvalDecisionId, setApprovalDecisionId] = useState(null)
  const [approvalActionId, setApprovalActionId] = useState(null)
  const [approvalAssignmentDrafts, setApprovalAssignmentDrafts] = useState({})
  const [orderDraft, setOrderDraft] = useState(() => buildOrderDraft(null, activeProfile.name))
  const [error, setError] = useState('')
  const { activeTab, setActiveTab, selectedId: selectedOrderId, setSelectedId: setSelectedOrderId } = useResourceUrlState({
    tabKeys: ORDER_FILTERS.map((filter) => filter.key),
    defaultTab: 'all',
    selectedKey: 'order',
  })

  useEffect(() => {
    let mounted = true
    Promise.all([fetchOrders(), fetchProducts(), fetchRestockAlerts(), fetchInventoryMovements(), fetchOrderApprovals()])
      .then(([nextOrders, nextProducts, nextRestockAlerts, nextInventoryMovements, nextOrderApprovals]) => {
        if (mounted) {
          setOrders(nextOrders)
          setOrderApprovals(nextOrderApprovals)
          setProducts(nextProducts)
          setRestockAlerts(nextRestockAlerts)
          setInventoryMovements(nextInventoryMovements)
          setError('')
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setError(nextError.message || '订单和库存数据加载失败')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  const refreshInventoryState = async () => {
    const [nextProducts, nextRestockAlerts, nextInventoryMovements] = await Promise.all([
      fetchProducts(),
      fetchRestockAlerts(),
      fetchInventoryMovements(),
    ])
    setProducts(nextProducts)
    setRestockAlerts(nextRestockAlerts)
    setInventoryMovements(nextInventoryMovements)
  }

  const refreshOrderApprovals = async () => {
    const nextOrderApprovals = await fetchOrderApprovals()
    setOrderApprovals(nextOrderApprovals)
  }

  const refreshSelectedOrderMovements = async (orderId) => {
    if (!orderId) {
      setSelectedOrderMovements([])
      return
    }
    try {
      const movements = await fetchOrderInventoryMovements(orderId)
      setSelectedOrderMovements(movements)
    } catch (nextError) {
      setSelectedOrderMovements([])
      setError(nextError.message || '订单库存审计加载失败')
    }
  }

  const handleRestockProduct = async (product, alert) => {
    const quantity = alert?.recommended_restock ?? Math.max(120, 300 - Number(product.stock ?? 0))
    setRestockSavingId(product.id)
    setError('')
    try {
      await restockProduct(product.id, {
        quantity,
        reason: '订单中心低库存建议补货',
        operator: activeProfile.name,
      })
      await refreshInventoryState()
    } catch (nextError) {
      setError(nextError.message || '补货失败')
    } finally {
      setRestockSavingId(null)
    }
  }

  const handleExportOrders = async () => {
    setExportSaving(true)
    setError('')
    try {
      const blob = await exportOrdersCsv()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `smart-crm-orders-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.append(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (nextError) {
      setError(nextError.message || '订单导出失败')
    } finally {
      setExportSaving(false)
    }
  }

  const handleOpenOrderEdit = () => {
    if (!selectedOrder) {
      return
    }
    const nextDraft = buildOrderDraft(selectedOrder, activeProfile.name)
    if (!nextDraft.items.length && products[0]) {
      nextDraft.items = [buildOrderLineDraft(products[0])]
    }
    setOrderDraft(nextDraft)
    setError('')
    setOrderEditOpen(true)
  }

  const handleSubmitOrderEdit = async (event) => {
    event.preventDefault()
    if (!selectedOrder) {
      return
    }
    setOrderSaving(true)
    setError('')
    try {
      const updatedOrder = await updateOrder(selectedOrder.id, buildOrderUpdatePayload(orderDraft, activeProfile.name))
      setOrders((currentOrders) => currentOrders.map((order) => (order.id === updatedOrder.id ? updatedOrder : order)))
      setSelectedOrderId(updatedOrder.id)
      await refreshInventoryState()
      await refreshSelectedOrderMovements(updatedOrder.id)
      setOrderEditOpen(false)
    } catch (nextError) {
      setError(nextError.message || '订单更新失败')
    } finally {
      setOrderSaving(false)
    }
  }

  const handleSubmitOrderApproval = async () => {
    if (!selectedOrder) {
      return
    }
    setApprovalSavingId(selectedOrder.id)
    setError('')
    try {
      await submitOrderApproval(selectedOrder.id, {
        reviewer: '销售经理',
        target_order_status: 'confirmed',
        reason: selectedOrder.created_by_ai
          ? 'AI 智能录单生成的订单，确认前需要经理复核客户、商品、数量和交付风险。'
          : '订单确认前需要经理复核商务条款、库存和交付风险。',
      })
      await refreshOrderApprovals()
    } catch (nextError) {
      setError(nextError.message || '提交审批失败')
    } finally {
      setApprovalSavingId(null)
    }
  }

  const handleDecisionOrderApproval = async (approval, decision) => {
    setApprovalDecisionId(`${approval.id}-${decision}`)
    setError('')
    try {
      await decideOrderApproval(approval.id, {
        decision,
        comment: decision === 'approved' ? '审批通过，订单可进入确认状态。' : '审批驳回，请销售补充客户确认或交付材料。',
      })
      const [nextOrders] = await Promise.all([fetchOrders(), refreshOrderApprovals()])
      setOrders(nextOrders)
    } catch (nextError) {
      setError(nextError.message || '审批处理失败')
    } finally {
      setApprovalDecisionId(null)
    }
  }

  const handleRemindOrderApproval = async (approval) => {
    setApprovalActionId(`${approval.id}-remind`)
    setError('')
    try {
      await remindOrderApproval(approval.id, {
        message: `${activeProfile.name} 催办订单 #${approval.order_id} 审批，请在 ${approval.sla_due_at ? formatDateTime(approval.sla_due_at) : 'SLA 截止前'} 处理。`,
      })
      await refreshOrderApprovals()
    } catch (nextError) {
      setError(nextError.message || '审批催办失败')
    } finally {
      setApprovalActionId(null)
    }
  }

  const handleAssignOrderApproval = async (approval) => {
    const reviewer = String(approvalAssignmentDrafts[approval.id] ?? approval.reviewer ?? '').trim()
    if (!reviewer) {
      setError('请输入转派对象')
      return
    }
    setApprovalActionId(`${approval.id}-assign`)
    setError('')
    try {
      await assignOrderApproval(approval.id, {
        reviewer,
        comment: `${activeProfile.name} 将审批转派给 ${reviewer} 处理。`,
      })
      setApprovalAssignmentDrafts((currentDrafts) => {
        const nextDrafts = { ...currentDrafts }
        delete nextDrafts[approval.id]
        return nextDrafts
      })
      await refreshOrderApprovals()
    } catch (nextError) {
      setError(nextError.message || '审批转派失败')
    } finally {
      setApprovalActionId(null)
    }
  }

  const summary = useMemo(() => summarizeOrders(orders), [orders])
  const visibleOrders = useMemo(() => filterOrders(orders, activeTab), [activeTab, orders])
  const selectedOrder = useMemo(() => {
    return visibleOrders.find((order) => String(order.id) === String(selectedOrderId)) ?? visibleOrders[0] ?? orders[0] ?? null
  }, [orders, selectedOrderId, visibleOrders])

  useEffect(() => {
    let mounted = true
    if (!selectedOrder?.id) {
      setSelectedOrderMovements([])
      return () => {
        mounted = false
      }
    }

    fetchOrderInventoryMovements(selectedOrder.id)
      .then((movements) => {
        if (mounted) {
          setSelectedOrderMovements(movements)
        }
      })
      .catch((nextError) => {
        if (mounted) {
          setSelectedOrderMovements([])
          setError(nextError.message || '订单库存审计加载失败')
        }
      })

    return () => {
      mounted = false
    }
  }, [selectedOrder?.id])
  const lowStockProducts = useMemo(() => pickLowStockProducts(products), [products])
  const restockAlertMap = useMemo(() => new Map(restockAlerts.map((alert) => [alert.product_id, alert])), [restockAlerts])
  const criticalAlertCount = useMemo(() => restockAlerts.filter((alert) => alert.priority === 'critical').length, [restockAlerts])
  const pendingApprovalCount = useMemo(() => orderApprovals.filter((approval) => approval.status === 'pending').length, [orderApprovals])
  const canApproveOrders = useMemo(() => {
    const permissions = activeProfile.permissions ?? []
    return permissions.includes('*') || permissions.includes('approval:manage')
  }, [activeProfile.permissions])
  const selectedOrderApprovals = useMemo(() => {
    if (!selectedOrder) {
      return []
    }
    return orderApprovals.filter((approval) => approval.order_id === selectedOrder.id)
  }, [orderApprovals, selectedOrder])
  const selectedPendingApproval = useMemo(() => {
    return selectedOrderApprovals.find((approval) => approval.status === 'pending') ?? null
  }, [selectedOrderApprovals])
  const canSubmitSelectedOrderApproval = Boolean(selectedOrder && selectedOrder.status === 'draft' && !selectedPendingApproval)
  const maxStock = useMemo(() => Math.max(1, ...products.map((product) => Number(product.stock ?? 0))), [products])
  const orderEditColumns = useMemo(() => [
    { key: 'owner', label: '负责人' },
    { key: 'region', label: '区域' },
    { key: 'dueDate', label: '交付日期', inputType: 'date', defaultValue: '' },
    { key: 'notes', label: '备注', defaultValue: '', required: false },
  ], [])
  const orderStatusField = useMemo(() => ({
    key: 'status',
    label: '订单状态',
    value: 'draft',
    options: ['draft', 'confirmed', 'fulfilled'],
    optionLabels: orderStatusLabelMap,
  }), [])
  const productOptionMap = useMemo(() => new Map(products.map((product) => [String(product.id), product])), [products])
  const orderDraftItems = useMemo(() => orderDraft.items ?? [], [orderDraft.items])
  const orderDraftTotal = useMemo(() => {
    return orderDraftItems.reduce((total, item) => total + calculateOrderLineTotal(item), 0)
  }, [orderDraftItems])

  const handleAddOrderItem = () => {
    if (!products.length) {
      return
    }
    setOrderDraft((currentDraft) => ({
      ...currentDraft,
      items: [...(currentDraft.items ?? []), buildOrderLineDraft(products[0])],
    }))
  }

  const handleRemoveOrderItem = (draftId) => {
    setOrderDraft((currentDraft) => {
      const remainingItems = (currentDraft.items ?? []).filter((item) => item.draftId !== draftId)
      return {
        ...currentDraft,
        items: remainingItems.length ? remainingItems : currentDraft.items,
      }
    })
  }

  const handleOrderItemChange = (draftId, key, value) => {
    setOrderDraft((currentDraft) => ({
      ...currentDraft,
      items: (currentDraft.items ?? []).map((item) => {
        if (item.draftId !== draftId) {
          return item
        }
        const nextItem = { ...item, [key]: value }
        if (key === 'productId') {
          const product = productOptionMap.get(String(value))
          if (product) {
            nextItem.unitPrice = String(product.unit_price)
          }
        }
        return nextItem
      }),
    }))
  }

  return (
    <div className="crm-page-stack">
      <ResourceHeader
        title="订单中心"
        subtitle="查看智能录单提交后的真实订单、订单明细和库存扣减结果。"
        icon={Activity}
        createLabel="去智能录单"
        tabs={ORDER_FILTERS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onCreate={() => navigate('/capture')}
      />
      <ResourceSyncState loading={loading || Boolean(restockSavingId) || exportSaving || orderSaving || Boolean(approvalSavingId) || Boolean(approvalDecisionId) || Boolean(approvalActionId)} error={error} />

      <section className="crm-metric-grid">
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-won">
            <TrendingUp size={18} />
          </div>
          <div>
            <span>订单总额</span>
            <strong>{formatCurrency(summary.totalRevenue)}</strong>
            <small>{summary.orderCount} 张订单 / {summary.totalItems} 个明细条目</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-proposal">
            <Sparkles size={18} />
          </div>
          <div>
            <span>AI 创建订单</span>
            <strong>{summary.aiOrderCount}</strong>
            <small>平均置信度 {formatPercent(summary.avgConfidence)}</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-new">
            <FileText size={18} />
          </div>
          <div>
            <span>草稿待确认</span>
            <strong>{summary.draftCount}</strong>
            <small>{pendingApprovalCount} 个审批中 / 可从智能录单继续提交</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified">
            <Shield size={18} />
          </div>
          <div>
            <span>补货建议</span>
            <strong>{restockAlerts.length}</strong>
            <small>{criticalAlertCount} 个危险库存 / 支持一键补货</small>
          </div>
        </article>
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <div className="crm-panel-header">
            <div>
              <strong>订单列表</strong>
              <small>{visibleOrders.length} 条订单，点击任意行查看明细。</small>
            </div>
            <button className="crm-ghost-button" type="button" onClick={handleExportOrders} disabled={exportSaving || loading}>
              <Download size={16} />
              {exportSaving ? '导出中' : '导出 CSV'}
            </button>
          </div>
          <div className="crm-table-wrap">
            <table className="crm-table">
              <thead>
                <tr>
                  <th>订单</th>
                  <th>客户</th>
                  <th>状态</th>
                  <th>来源</th>
                  <th>金额</th>
                  <th>交付日期</th>
                </tr>
              </thead>
              <tbody>
                {visibleOrders.map((order) => (
                  <tr
                    key={order.id}
                    className={selectedOrder?.id === order.id ? 'is-selected' : ''}
                    onClick={() => setSelectedOrderId(order.id)}
                  >
                    <td>
                      <div className="crm-table-stack">
                        <strong>#{order.id}</strong>
                        <span>{order.owner}</span>
                      </div>
                    </td>
                    <td>{order.customer_name}</td>
                    <td><StatusBadge value={orderStatusLabelMap[order.status] ?? order.status} tone={statusToneMap[order.status] ?? 'neutral'} /></td>
                    <td><StatusBadge value={order.created_by_ai ? 'AI' : '人工'} tone={order.created_by_ai ? 'accent' : 'neutral'} /></td>
                    <td>{formatCurrency(order.total_amount)}</td>
                    <td>{order.due_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!loading && !error && !visibleOrders.length ? <EmptyState icon={Activity} title="暂无匹配订单" subtitle="切换筛选条件或从智能录单创建新订单。" /> : null}
        </div>

        <div className="crm-panel">
          <div className="crm-panel-header">
            <strong>订单明细</strong>
            {selectedOrder ? (
              <button className="crm-ghost-button" type="button" onClick={handleOpenOrderEdit}>
                <Pencil size={16} />
                编辑订单
              </button>
            ) : null}
          </div>
          {selectedOrder ? (
            <div className="crm-progress-list">
              <div className="crm-list-item">
                <div>
                  <strong>{selectedOrder.customer_name}</strong>
                  <span>{selectedOrder.order_date} 创建 / {selectedOrder.due_date} 交付</span>
                </div>
                <div className="crm-list-value">{formatCurrency(selectedOrder.total_amount)}</div>
              </div>
              <div className="crm-list-item">
                <div>
                  <strong>{selectedOrder.created_by_ai ? 'AI Capture 录入' : '人工录入'}</strong>
                  <span>{selectedOrder.notes || '暂无备注'}</span>
                </div>
                <StatusBadge value={formatPercent(selectedOrder.ai_confidence_score ?? 0)} tone={selectedOrder.created_by_ai ? 'accent' : 'neutral'} />
              </div>
              <div className="crm-order-audit-block">
                <div className="crm-order-audit-head">
                  <strong>订单审批流</strong>
                  <small>{selectedOrderApprovals.length ? `${selectedOrderApprovals.length} 条记录` : '可提交经理复核'}</small>
                </div>
                <div className="crm-toolbar-actions">
                  <button
                    className="crm-primary-button"
                    type="button"
                    onClick={handleSubmitOrderApproval}
                    disabled={!canSubmitSelectedOrderApproval || approvalSavingId === selectedOrder.id}
                  >
                    <CheckSquare size={16} />
                    {approvalSavingId === selectedOrder.id ? '提交中' : selectedPendingApproval ? '审批中' : selectedOrder.status === 'draft' ? '提交审批' : '无需审批'}
                  </button>
                  {selectedPendingApproval ? <StatusBadge value="待经理处理" tone="warning" /> : null}
                </div>
                {selectedOrderApprovals.length ? selectedOrderApprovals.map((approval) => (
                  <div key={approval.id} className="crm-list-item">
                    <div>
                      <strong>{approvalStatusLabelMap[approval.status] ?? approval.status}</strong>
                      <span>{approval.reason}</span>
                      <small>{approval.risk_summary}</small>
                      <small>{formatApprovalSla(approval)}</small>
                      {approval.decision_comment ? <small>{approval.reviewer}：{approval.decision_comment}</small> : null}
                    </div>
                    <div className="crm-approval-actions">
                      <StatusBadge value={approvalRiskLabelMap[approval.risk_level] ?? '中风险'} tone={approvalRiskToneMap[approval.risk_level] ?? 'info'} />
                      <StatusBadge value={approvalSlaLabelMap[approval.sla_status] ?? 'SLA 未设置'} tone={approvalSlaToneMap[approval.sla_status] ?? 'neutral'} />
                      <StatusBadge value={formatCurrency(approval.requested_total)} tone={approval.requested_total >= 100000 ? 'warning' : 'neutral'} />
                      {approval.status === 'pending' ? (
                        <button
                          className="crm-ghost-button"
                          type="button"
                          onClick={() => handleRemindOrderApproval(approval)}
                          disabled={approvalActionId === `${approval.id}-remind`}
                        >
                          催办
                        </button>
                      ) : null}
                      {approval.status === 'pending' && canApproveOrders ? (
                        <div className="crm-approval-assign">
                          <input
                            aria-label="审批转派对象"
                            value={approvalAssignmentDrafts[approval.id] ?? approval.reviewer ?? ''}
                            onChange={(event) => setApprovalAssignmentDrafts((currentDrafts) => ({
                              ...currentDrafts,
                              [approval.id]: event.target.value,
                            }))}
                            placeholder="审批人或角色"
                          />
                          <button
                            className="crm-ghost-button"
                            type="button"
                            onClick={() => handleAssignOrderApproval(approval)}
                            disabled={approvalActionId === `${approval.id}-assign`}
                          >
                            转派
                          </button>
                        </div>
                      ) : null}
                      {approval.status === 'pending' && canApproveOrders ? (
                        <div className="crm-stack-inline">
                          <button
                            className="crm-ghost-button"
                            type="button"
                            onClick={() => handleDecisionOrderApproval(approval, 'rejected')}
                            disabled={approvalDecisionId === `${approval.id}-rejected`}
                          >
                            驳回
                          </button>
                          <button
                            className="crm-primary-button"
                            type="button"
                            onClick={() => handleDecisionOrderApproval(approval, 'approved')}
                            disabled={approvalDecisionId === `${approval.id}-approved`}
                          >
                            通过
                          </button>
                        </div>
                      ) : null}
                    </div>
                  </div>
                )) : (
                  <EmptyState icon={CheckSquare} title="暂无审批记录" subtitle="草稿订单可提交经理复核，审批结果会写入操作审计。" />
                )}
              </div>
              {selectedOrder.items.map((item) => (
                <div key={item.id} className="crm-list-item">
                  <div>
                    <strong>{item.product_name}</strong>
                    <span>{item.quantity} 件 x {formatCurrency(item.unit_price)}</span>
                  </div>
                  <div className="crm-list-value">{formatCurrency(item.line_total)}</div>
                </div>
              ))}
              <div className="crm-order-audit-block">
                <div className="crm-order-audit-head">
                  <strong>本订单库存审计</strong>
                  <small>{selectedOrderMovements.length} 条流水</small>
                </div>
                {selectedOrderMovements.length ? selectedOrderMovements.slice(0, 6).map((movement) => (
                  <div key={movement.id} className="crm-list-item">
                    <div>
                      <strong>{movement.product_name}</strong>
                      <span>{inventorySourceLabelMap[movement.source] ?? movement.source} · {movement.before_stock} → {movement.after_stock}</span>
                      <small>{movement.reason}</small>
                    </div>
                    <div className="crm-list-value">
                      {movement.change_quantity > 0 ? '+' : ''}{movement.change_quantity}
                    </div>
                  </div>
                )) : (
                  <EmptyState icon={Shield} title="暂无库存审计" subtitle="订单创建或明细调整后会显示库存变化。" />
                )}
              </div>
            </div>
          ) : (
            <EmptyState icon={Activity} title="暂无订单明细" subtitle="后端订单数据同步后会显示在这里。" />
          )}
        </div>
      </section>

      <CreateRecordModal
        open={orderEditOpen}
        title="编辑订单"
        columns={orderEditColumns}
        workflowField={orderStatusField}
        draft={orderDraft}
        onDraftChange={setOrderDraft}
        onClose={() => setOrderEditOpen(false)}
        onSubmit={handleSubmitOrderEdit}
        submitting={orderSaving}
      >
        <OrderItemsEditor
          products={products}
          items={orderDraftItems}
          totalAmount={orderDraftTotal}
          onAddItem={handleAddOrderItem}
          onRemoveItem={handleRemoveOrderItem}
          onItemChange={handleOrderItemChange}
        />
      </CreateRecordModal>

      <section className="crm-panel">
        <PanelHeader title="库存补货建议" />
        <div className="crm-dashboard-grid">
          <div className="crm-stock-grid">
            {lowStockProducts.map((product) => {
              const alert = restockAlertMap.get(product.id)
              const tone = alert?.priority === 'critical' ? 'danger' : getStockTone(product)
              const stockWidth = Math.max(8, Math.round((Number(product.stock ?? 0) / maxStock) * 100))
              return (
                <article key={product.id} className="crm-stock-card">
                  <div className="crm-stock-card-head">
                    <div>
                      <strong>{product.name}</strong>
                      <span>{product.sku} · {product.category} · {formatCurrency(product.unit_price)}</span>
                    </div>
                    <StatusBadge value={`${product.stock} 件`} tone={tone} />
                  </div>
                  <div className="crm-progress-track">
                    <div className={`crm-progress-bar tone-${tone}`} style={{ width: `${stockWidth}%` }} />
                  </div>
                  {alert ? (
                    <div className="crm-stock-action">
                      <span>{alert.reason}</span>
                      <button
                        className="crm-primary-button"
                        type="button"
                        onClick={() => handleRestockProduct(product, alert)}
                        disabled={restockSavingId === product.id}
                      >
                        {restockSavingId === product.id ? '补货中' : `补货 ${alert.recommended_restock} 件`}
                      </button>
                    </div>
                  ) : (
                    <small>库存高于预警线，继续观察订单消耗。</small>
                  )}
                </article>
              )
            })}
          </div>

          <div className="crm-progress-list">
            {inventoryMovements.slice(0, 6).map((movement) => (
              <div key={movement.id} className="crm-list-item">
                <div>
                  <strong>{movement.product_name}</strong>
                  <span>{inventorySourceLabelMap[movement.source] ?? movement.source} · {movement.reason}</span>
                </div>
                <div className="crm-list-value">
                  {movement.change_quantity > 0 ? '+' : ''}{movement.change_quantity}
                </div>
              </div>
            ))}
            {!inventoryMovements.length ? <EmptyState icon={Shield} title="暂无库存流水" subtitle="创建订单或补货后会显示库存变化记录。" /> : null}
          </div>
        </div>
      </section>
    </div>
  )
}

function TableResourcePage({
  title,
  subtitle,
  icon: Icon,
  records,
  columns,
  tabs,
  createLabel,
  loading = false,
  error = '',
  defaultDraftValues = {},
  onCreateRecord,
  onUpdateRecord,
  onDeleteRecord,
  getRecordHref,
  openRecordLabel = '打开详情',
  preferenceNamespace = `resource:${title}`,
}) {
  const [rows, setRows] = useState(records)
  const [createOpen, setCreateOpen] = useState(false)
  const [bulkEditOpen, setBulkEditOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)
  const [bulkEditSaving, setBulkEditSaving] = useState(false)
  const [deleteSaving, setDeleteSaving] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [createError, setCreateError] = useState('')
  const [selectedRowIds, setSelectedRowIds] = useState([])
  const [confirmRequest, setConfirmRequest] = useState(null)
  const createInitialDraft = () => ({
    ...createDraftFromColumns(columns),
    ...defaultDraftValues,
  })
  const [draft, setDraft] = useState(createInitialDraft)
  const [bulkEditDraft, setBulkEditDraft] = useState(() => createBulkEditDraft(columns))
  const searchInputRef = useRef(null)
  const hasActions = Boolean(getRecordHref || onUpdateRecord || onDeleteRecord)
  const { query, setQuery, activeTab, setActiveTab, preferenceStatus, preferenceValue, savePreferencePatch } = useResourceUrlState({
    tabKeys: tabs.map((tab) => tab.key),
    defaultTab: tabs[0].key,
    preferenceNamespace,
  })
  const visibleColumnKeys = useMemo(
    () => normalizeVisibleColumnKeys(columns, preferenceValue.visibleColumnKeys),
    [columns, preferenceValue.visibleColumnKeys],
  )
  const visibleColumns = useMemo(
    () => columns.filter((column) => visibleColumnKeys.includes(column.key)),
    [columns, visibleColumnKeys],
  )
  const sortState = useMemo(
    () => normalizeSortState(columns, preferenceValue.sort),
    [columns, preferenceValue.sort],
  )

  useEffect(() => {
    setRows(records)
  }, [records])

  useEffect(() => {
    const rowIds = new Set(rows.map((record) => String(record.id)))
    setSelectedRowIds((currentIds) => currentIds.filter((id) => rowIds.has(id)))
  }, [rows])

  const filteredRecords = useMemo(() => {
    const tab = tabs.find((item) => item.key === activeTab)
    return rows.filter((record) => {
      const matchesTab = tab?.predicate ? tab.predicate(record) : true
      if (!matchesTab) {
        return false
      }
      if (!query.trim()) {
        return true
      }
      return Object.values(record).some((value) => String(value).toLowerCase().includes(query.toLowerCase()))
    })
  }, [activeTab, query, rows, tabs])
  const visibleRecords = useMemo(
    () => sortRecordsByColumn(filteredRecords, sortState.key, sortState.direction),
    [filteredRecords, sortState.direction, sortState.key],
  )
  const visibleRecordIds = useMemo(() => visibleRecords.map((record) => String(record.id)), [visibleRecords])
  const selectedRecords = useMemo(
    () => rows.filter((record) => selectedRowIds.includes(String(record.id))),
    [rows, selectedRowIds],
  )
  const allVisibleSelected = visibleRecordIds.length > 0 && visibleRecordIds.every((id) => selectedRowIds.includes(id))

  const handleOpenCreate = () => {
    setEditingRecord(null)
    setDraft(createInitialDraft())
    setCreateError('')
    setCreateOpen(true)
  }

  const handleOpenEdit = (record) => {
    setEditingRecord(record)
    setDraft(buildDraftFromRecord(columns, record))
    setCreateError('')
    setCreateOpen(true)
  }

  const handleOpenBulkEdit = () => {
    setBulkEditDraft(createBulkEditDraft(columns))
    setCreateError('')
    setBulkEditOpen(true)
  }

  const handleSubmitCreate = async (event) => {
    event.preventDefault()
    setCreateSaving(true)
    setCreateError('')
    try {
      if (editingRecord && onUpdateRecord) {
        const record = await onUpdateRecord(editingRecord.id, draft)
        setRows((currentRows) => currentRows.map((item) => (item.id === editingRecord.id ? record : item)))
      } else {
        const record = onCreateRecord
          ? await onCreateRecord(draft)
          : await Promise.reject(new Error(`${title} 未接入后端创建接口`))
        setRows((currentRows) => [record, ...currentRows])
      }
      setCreateOpen(false)
      setEditingRecord(null)
    } catch (nextError) {
      setCreateError(nextError.message || (editingRecord ? '更新记录失败' : '新建记录失败'))
    } finally {
      setCreateSaving(false)
    }
  }

  const handleDeleteRecord = async (record) => {
    if (!onDeleteRecord) {
      return
    }
    const recordName = record.name ?? record.title ?? '这条记录'
    setConfirmRequest({
      title: `删除${title}`,
      message: `确认删除 ${recordName}？系统会调用后端 DELETE 接口，若存在订单、库存或权限关联，后端会拒绝删除并保留记录。`,
      confirmLabel: '确认删除',
      onConfirm: async () => {
        setDeleteSaving(true)
        setCreateError('')
        try {
          await onDeleteRecord(record.id)
          setRows((currentRows) => currentRows.filter((item) => item.id !== record.id))
          setConfirmRequest(null)
        } catch (nextError) {
          setCreateError(nextError.message || '删除记录失败')
        } finally {
          setDeleteSaving(false)
        }
      },
    })
  }

  const handleFocusSearch = () => {
    searchInputRef.current?.focus()
  }

  const handleExportCsv = () => {
    downloadResourceCsv(title, visibleRecords, visibleColumns)
  }

  const handleExportSelectedCsv = () => {
    downloadResourceCsv(`${title}-selected`, selectedRecords, visibleColumns)
  }

  const handleToggleColumn = (columnKey) => {
    const nextKeys = visibleColumnKeys.includes(columnKey)
      ? visibleColumnKeys.filter((key) => key !== columnKey)
      : columns.map((column) => column.key).filter((key) => key === columnKey || visibleColumnKeys.includes(key))
    if (!nextKeys.length) {
      return
    }
    savePreferencePatch({ visibleColumnKeys: nextKeys })
  }

  const handleSortColumn = (columnKey) => {
    const nextSort = sortState.key !== columnKey
      ? { key: columnKey, direction: 'asc' }
      : sortState.direction === 'asc'
        ? { key: columnKey, direction: 'desc' }
        : { key: '', direction: 'asc' }
    savePreferencePatch({ sort: nextSort })
  }

  const handleToggleRowSelection = (recordId) => {
    setSelectedRowIds((currentIds) => toggleSelectedKey(currentIds, String(recordId)))
  }

  const handleToggleVisibleSelection = () => {
    setSelectedRowIds((currentIds) => toggleVisibleSelection(currentIds, visibleRecordIds))
  }

  const handleBulkDelete = async () => {
    if (!onDeleteRecord || !selectedRecords.length) {
      return
    }
    const targetRecords = [...selectedRecords]
    setConfirmRequest({
      title: `批量删除${title}`,
      message: `确认删除选中的 ${targetRecords.length} 条记录？系统会逐条调用真实后端 DELETE 接口，成功项会从列表移除，失败项会保留并提示原因。`,
      confirmLabel: `删除 ${targetRecords.length} 条`,
      onConfirm: async () => {
        setDeleteSaving(true)
        setCreateError('')
        try {
          const results = await Promise.allSettled(targetRecords.map((record) => onDeleteRecord(record.id)))
          const summary = summarizeBulkSettledResults(results)
          const deletedIds = new Set(targetRecords.filter((_, index) => results[index].status === 'fulfilled').map((record) => String(record.id)))
          setRows((currentRows) => currentRows.filter((record) => !deletedIds.has(String(record.id))))
          setSelectedRowIds((currentIds) => currentIds.filter((id) => !deletedIds.has(id)))
          if (summary.failed) {
            setCreateError(`已删除 ${summary.succeeded} 条，${summary.failed} 条失败，请检查关联数据或权限。`)
          }
          setConfirmRequest(null)
        } catch (nextError) {
          setCreateError(nextError.message || '批量删除失败')
        } finally {
          setDeleteSaving(false)
        }
      },
    })
  }

  const handleSubmitBulkEdit = async (event) => {
    event.preventDefault()
    if (!onUpdateRecord || !selectedRecords.length) {
      return
    }
    const patch = buildBulkEditPatch(bulkEditDraft, columns)
    if (!Object.keys(patch).length) {
      setCreateError('请至少选择一个要批量更新的字段。')
      return
    }

    setBulkEditSaving(true)
    setCreateError('')
    const targetRecords = [...selectedRecords]
    try {
      const results = await Promise.allSettled(targetRecords.map((record) => {
        const nextDraft = {
          ...buildDraftFromRecord(columns, record),
          ...patch,
        }
        return onUpdateRecord(record.id, nextDraft)
      }))
      const summary = summarizeBulkSettledResults(results)
      const updatedById = new Map()
      targetRecords.forEach((record, index) => {
        if (results[index].status === 'fulfilled') {
          updatedById.set(String(record.id), results[index].value)
        }
      })

      setRows((currentRows) => currentRows.map((record) => updatedById.get(String(record.id)) ?? record))
      setSelectedRowIds((currentIds) => currentIds.filter((id) => !updatedById.has(id)))
      if (summary.failed) {
        setCreateError(`已更新 ${summary.succeeded} 条，${summary.failed} 条失败，请检查字段唯一性、权限或后端校验。`)
      } else {
        setBulkEditOpen(false)
      }
    } catch (nextError) {
      setCreateError(nextError.message || '批量编辑失败')
    } finally {
      setBulkEditSaving(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <ResourceHeader
        title={title}
        subtitle={subtitle}
        icon={Icon}
        createLabel={createLabel}
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onCreate={handleOpenCreate}
        onFocusSearch={handleFocusSearch}
        onExport={handleExportCsv}
        exportDisabled={!visibleRecords.length}
      />
      <ResourceSyncState loading={loading || createSaving || deleteSaving || bulkEditSaving} error={error || createError} />
      {selectedRecords.length ? (
        <section className="crm-bulk-action-bar">
          <strong>已选 {selectedRecords.length} 条</strong>
          <button className="crm-ghost-button" type="button" onClick={handleExportSelectedCsv}>
            <Download size={15} />
            导出选中
          </button>
          {onUpdateRecord ? (
            <button className="crm-ghost-button" type="button" onClick={handleOpenBulkEdit} disabled={bulkEditSaving}>
              <Pencil size={15} />
              {bulkEditSaving ? '保存中' : '批量编辑'}
            </button>
          ) : null}
          {onDeleteRecord ? (
            <button className="crm-ghost-button crm-ghost-button--danger" type="button" onClick={handleBulkDelete} disabled={deleteSaving}>
              <Trash2 size={15} />
              {deleteSaving ? '删除中' : '批量删除'}
            </button>
          ) : null}
          <button className="crm-link-button" type="button" onClick={() => setSelectedRowIds([])}>
            清除选择
          </button>
        </section>
      ) : null}
      <ResourceToolbar query={query} onQueryChange={setQuery} columnCount={visibleColumns.length} inputRef={searchInputRef} preferenceStatus={preferenceStatus}>
        <div className="crm-column-picker" aria-label="列显示">
          {columns.map((column) => (
            <label key={column.key} className="crm-column-choice">
              <input
                type="checkbox"
                checked={visibleColumnKeys.includes(column.key)}
                disabled={visibleColumnKeys.length === 1 && visibleColumnKeys.includes(column.key)}
                onChange={() => handleToggleColumn(column.key)}
              />
              <span>{column.label}</span>
            </label>
          ))}
        </div>
      </ResourceToolbar>
      <div className="crm-panel">
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th className="crm-table-select-cell">
                  <input
                    type="checkbox"
                    aria-label="选择当前可见记录"
                    checked={allVisibleSelected}
                    disabled={!visibleRecordIds.length}
                    onChange={handleToggleVisibleSelection}
                  />
                </th>
                {visibleColumns.map((column) => (
                  <th key={column.key}>
                    <button className="crm-table-sort-button" type="button" onClick={() => handleSortColumn(column.key)}>
                      <span>{column.label}</span>
                      {sortState.key === column.key ? <small>{sortState.direction === 'asc' ? '升序' : '降序'}</small> : null}
                    </button>
                  </th>
                ))}
                {hasActions ? <th className="crm-table-actions-cell">操作</th> : null}
              </tr>
            </thead>
            <tbody>
              {visibleRecords.map((record) => (
                <tr key={record.id}>
                  <td className="crm-table-select-cell">
                    <input
                      type="checkbox"
                      aria-label={`选择 ${record.name ?? record.title ?? record.company ?? record.id}`}
                      checked={selectedRowIds.includes(String(record.id))}
                      onChange={() => handleToggleRowSelection(record.id)}
                    />
                  </td>
                  {visibleColumns.map((column) => (
                    <td key={column.key}>{renderCell(record[column.key], column)}</td>
                  ))}
                  {hasActions ? (
                    <td className="crm-table-actions-cell">
                      <div className="crm-row-actions">
                        {getRecordHref ? (
                          <NavLink className="crm-icon-button" aria-label={openRecordLabel} title={openRecordLabel} to={getRecordHref(record)}>
                            <ArrowRight size={15} />
                          </NavLink>
                        ) : null}
                        {onUpdateRecord ? (
                          <button className="crm-icon-button" type="button" aria-label="编辑记录" title="编辑" onClick={() => handleOpenEdit(record)}>
                            <Pencil size={15} />
                          </button>
                        ) : null}
                        {onDeleteRecord ? (
                          <button
                            className="crm-icon-button crm-icon-button--danger"
                            type="button"
                            aria-label="删除记录"
                            title="删除"
                            onClick={() => handleDeleteRecord(record)}
                          >
                            <Trash2 size={15} />
                          </button>
                        ) : null}
                      </div>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {!loading && !error && !visibleRecords.length ? <EmptyState icon={Icon} title={`暂无${title}数据`} subtitle="后端演示数据同步后会显示在这里。" /> : null}
      <CreateRecordModal
        open={createOpen}
        title={editingRecord ? `编辑${title}` : createLabel}
        columns={columns}
        draft={draft}
        onDraftChange={setDraft}
        onClose={() => {
          setCreateOpen(false)
          setEditingRecord(null)
        }}
        onSubmit={handleSubmitCreate}
        submitting={createSaving}
      />
      <BulkEditModal
        open={bulkEditOpen}
        title={`批量编辑${title}`}
        columns={columns}
        draft={bulkEditDraft}
        selectedCount={selectedRecords.length}
        onDraftChange={setBulkEditDraft}
        onClose={() => setBulkEditOpen(false)}
        onSubmit={handleSubmitBulkEdit}
        submitting={bulkEditSaving}
      />
      <ConfirmDialog
        open={Boolean(confirmRequest)}
        title={confirmRequest?.title ?? ''}
        message={confirmRequest?.message ?? ''}
        confirmLabel={confirmRequest?.confirmLabel ?? '确认'}
        submitting={deleteSaving}
        onCancel={() => setConfirmRequest(null)}
        onConfirm={confirmRequest?.onConfirm}
      />
    </div>
  )
}

function BoardResourcePage({
  title,
  subtitle,
  icon: Icon,
  records,
  columns,
  createLabel,
  boardKey,
  workflowOptions,
  loading = false,
  error = '',
  defaultDraftValues = {},
  onCreateRecord,
  onUpdateRecord,
  onDeleteRecord,
  onWorkflowChange,
  preferenceNamespace = `resource:${title}`,
}) {
  const [rows, setRows] = useState(records)
  const [createOpen, setCreateOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)
  const [deleteSaving, setDeleteSaving] = useState(false)
  const [workflowSavingId, setWorkflowSavingId] = useState('')
  const [dragOverGroup, setDragOverGroup] = useState('')
  const [editingRecord, setEditingRecord] = useState(null)
  const [createError, setCreateError] = useState('')
  const [confirmRequest, setConfirmRequest] = useState(null)
  const searchInputRef = useRef(null)
  const hasActions = Boolean(onUpdateRecord || onDeleteRecord)
  const { query, setQuery, view, setView, preferenceStatus } = useResourceUrlState({
    viewKeys: ['list', 'board'],
    defaultView: 'list',
    preferenceNamespace,
  })
  const boardValues = useMemo(() => {
    const configuredValues = workflowOptions?.length ? workflowOptions : []
    const rowValues = rows.map((record) => record[boardKey]).filter(Boolean)
    return [...new Set([...configuredValues, ...rowValues])]
  }, [boardKey, rows, workflowOptions])
  const workflowField = useMemo(
    () => ({ key: boardKey, label: '阶段', value: boardValues[0] ?? 'New', options: boardValues.length ? boardValues : ['New'] }),
    [boardKey, boardValues],
  )
  const createInitialDraft = () => ({
    ...createDraftFromColumns(columns, workflowField),
    ...defaultDraftValues,
  })
  const [draft, setDraft] = useState(createInitialDraft)

  useEffect(() => {
    setRows(records)
  }, [records])

  const visibleRecords = useMemo(() => {
    if (!query.trim()) {
      return rows
    }
    return rows.filter((record) => Object.values(record).some((value) => String(value).toLowerCase().includes(query.toLowerCase())))
  }, [query, rows])

  const groups = useMemo(() => {
    return visibleRecords.reduce((accumulator, record) => {
      const key = record[boardKey]
      accumulator[key] = accumulator[key] ? [...accumulator[key], record] : [record]
      return accumulator
    }, Object.fromEntries(boardValues.map((value) => [value, []])))
  }, [boardKey, boardValues, visibleRecords])

  const handleWorkflowMove = async (record, nextValue) => {
    if (!onWorkflowChange || !nextValue || record[boardKey] === nextValue || workflowSavingId) {
      return
    }
    const previousValue = record[boardKey]
    const recordId = String(record.id)
    setWorkflowSavingId(recordId)
    setCreateError('')
    setRows((currentRows) => currentRows.map((item) => (item.id === record.id ? { ...item, [boardKey]: nextValue } : item)))
    try {
      const updatedRecord = await onWorkflowChange(record, nextValue)
      setRows((currentRows) => currentRows.map((item) => (item.id === record.id ? updatedRecord : item)))
    } catch (nextError) {
      setRows((currentRows) => currentRows.map((item) => (item.id === record.id ? { ...item, [boardKey]: previousValue } : item)))
      setCreateError(nextError.message || '阶段流转失败')
    } finally {
      setWorkflowSavingId('')
      setDragOverGroup('')
    }
  }

  const handleCardDragStart = (event, record) => {
    if (!onWorkflowChange) {
      return
    }
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(record.id))
  }

  const handleColumnDragOver = (event, group) => {
    if (!onWorkflowChange) {
      return
    }
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    setDragOverGroup(group)
  }

  const handleColumnDrop = (event, group) => {
    if (!onWorkflowChange) {
      return
    }
    event.preventDefault()
    const recordId = event.dataTransfer.getData('text/plain')
    const record = rows.find((item) => String(item.id) === recordId)
    if (record) {
      handleWorkflowMove(record, group)
    }
  }

  const handleOpenCreate = () => {
    setEditingRecord(null)
    setDraft(createInitialDraft())
    setCreateError('')
    setCreateOpen(true)
  }

  const handleOpenEdit = (record) => {
    setEditingRecord(record)
    setDraft(buildDraftFromRecord(columns, record, workflowField))
    setCreateError('')
    setCreateOpen(true)
  }

  const handleSubmitCreate = async (event) => {
    event.preventDefault()
    setCreateSaving(true)
    setCreateError('')
    try {
      if (editingRecord && onUpdateRecord) {
        const record = await onUpdateRecord(editingRecord.id, draft)
        setRows((currentRows) => currentRows.map((item) => (item.id === editingRecord.id ? record : item)))
      } else {
        const record = onCreateRecord
          ? await onCreateRecord(draft)
          : await Promise.reject(new Error(`${title} 未接入后端创建接口`))
        setRows((currentRows) => [record, ...currentRows])
      }
      setCreateOpen(false)
      setEditingRecord(null)
      setView('list')
    } catch (nextError) {
      setCreateError(nextError.message || (editingRecord ? '更新记录失败' : '新建记录失败'))
    } finally {
      setCreateSaving(false)
    }
  }

  const handleDeleteRecord = async (record) => {
    if (!onDeleteRecord) {
      return
    }
    const recordName = record.name ?? record.title ?? '这条记录'
    setConfirmRequest({
      title: `删除${title}`,
      message: `确认删除 ${recordName}？系统会调用后端 DELETE 接口，后端权限和关联数据规则仍会进行最终校验。`,
      confirmLabel: '确认删除',
      onConfirm: async () => {
        setDeleteSaving(true)
        setCreateError('')
        try {
          await onDeleteRecord(record.id)
          setRows((currentRows) => currentRows.filter((item) => item.id !== record.id))
          setConfirmRequest(null)
        } catch (nextError) {
          setCreateError(nextError.message || '删除记录失败')
        } finally {
          setDeleteSaving(false)
        }
      },
    })
  }

  const handleFocusSearch = () => {
    searchInputRef.current?.focus()
  }

  const handleExportCsv = () => {
    downloadResourceCsv(title, visibleRecords, columns)
  }

  return (
    <div className="crm-page-stack">
      <ResourceHeader
        title={title}
        subtitle={subtitle}
        icon={Icon}
        createLabel={createLabel}
        onCreate={handleOpenCreate}
        onFocusSearch={handleFocusSearch}
        onExport={handleExportCsv}
        exportDisabled={!visibleRecords.length}
      />
      <ResourceSyncState loading={loading || createSaving || deleteSaving || Boolean(workflowSavingId)} error={error || createError} />
      <ResourceToolbar query={query} onQueryChange={setQuery} columnCount={columns.length} inputRef={searchInputRef} preferenceStatus={preferenceStatus}>
        <div className="crm-view-toggle">
          <button className={view === 'list' ? 'is-active' : ''} type="button" onClick={() => setView('list')}>
            <LayoutList size={16} />
            列表
          </button>
          <button className={view === 'board' ? 'is-active' : ''} type="button" onClick={() => setView('board')}>
            <LayoutGrid size={16} />
            看板
          </button>
        </div>
      </ResourceToolbar>

      {view === 'list' ? (
        <div className="crm-panel">
          <div className="crm-table-wrap">
            <table className="crm-table">
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.key}>{column.label}</th>
                  ))}
                  {hasActions ? <th className="crm-table-actions-cell">操作</th> : null}
                </tr>
              </thead>
              <tbody>
                {visibleRecords.map((record) => (
                  <tr key={record.id}>
                    {columns.map((column) => (
                      <td key={column.key}>{renderCell(record[column.key], column)}</td>
                    ))}
                    {hasActions ? (
                      <td className="crm-table-actions-cell">
                        <div className="crm-row-actions">
                          {onUpdateRecord ? (
                            <button className="crm-icon-button" type="button" aria-label="编辑记录" title="编辑" onClick={() => handleOpenEdit(record)}>
                              <Pencil size={15} />
                            </button>
                          ) : null}
                          {onDeleteRecord ? (
                            <button
                              className="crm-icon-button crm-icon-button--danger"
                              type="button"
                              aria-label="删除记录"
                              title="删除"
                              onClick={() => handleDeleteRecord(record)}
                            >
                              <Trash2 size={15} />
                            </button>
                          ) : null}
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="crm-board-grid">
          {Object.entries(groups).map(([group, items]) => (
            <section
              key={group}
              className={`crm-board-column${dragOverGroup === group ? ' is-drag-over' : ''}`}
              onDragOver={(event) => handleColumnDragOver(event, group)}
              onDragLeave={() => setDragOverGroup((currentGroup) => (currentGroup === group ? '' : currentGroup))}
              onDrop={(event) => handleColumnDrop(event, group)}
            >
              <div className="crm-board-head">
                <div>
                  <strong>{group}</strong>
                  <span>{items.length} 条</span>
                </div>
                <StatusBadge value={items.length} tone={boardToneMap[group] ?? 'neutral'} isNumeric />
              </div>
              <div className="crm-board-list">
                {items.map((item) => {
                  const groupIndex = boardValues.indexOf(item[boardKey])
                  const previousGroup = boardValues[groupIndex - 1]
                  const nextGroup = boardValues[groupIndex + 1]
                  const isWorkflowSaving = workflowSavingId === String(item.id)
                  return (
                    <article
                      key={item.id}
                      className={`crm-board-card${onWorkflowChange ? ' is-draggable' : ''}${isWorkflowSaving ? ' is-saving' : ''}`}
                      draggable={Boolean(onWorkflowChange) && !isWorkflowSaving}
                      onDragStart={(event) => handleCardDragStart(event, item)}
                    >
                      <strong>{item.name ?? item.title}</strong>
                      <p>{item.company ?? item.account ?? item.owner}</p>
                      {'amount' in item ? <span>{formatCurrency(item.amount)}</span> : null}
                      {'nextStep' in item ? <span>{item.nextStep}</span> : null}
                      {'priority' in item ? <StatusBadge value={item.priority} tone={statusToneMap[item.priority] ?? 'neutral'} /> : null}
                      {onWorkflowChange ? (
                        <div className="crm-board-flow-actions" aria-label="阶段流转">
                          <button
                            className="crm-icon-button"
                            type="button"
                            aria-label={`退回到${previousGroup ?? '上一阶段'}`}
                            title={previousGroup ? `退回到${previousGroup}` : '已在第一阶段'}
                            disabled={!previousGroup || isWorkflowSaving}
                            onClick={() => handleWorkflowMove(item, previousGroup)}
                          >
                            <ChevronLeft size={15} />
                          </button>
                          <button
                            className="crm-icon-button"
                            type="button"
                            aria-label={`推进到${nextGroup ?? '下一阶段'}`}
                            title={nextGroup ? `推进到${nextGroup}` : '已在最后阶段'}
                            disabled={!nextGroup || isWorkflowSaving}
                            onClick={() => handleWorkflowMove(item, nextGroup)}
                          >
                            <ChevronRight size={15} />
                          </button>
                        </div>
                      ) : null}
                      {hasActions ? (
                        <div className="crm-board-card-actions">
                          {onUpdateRecord ? (
                            <button className="crm-icon-button" type="button" aria-label="编辑记录" title="编辑" onClick={() => handleOpenEdit(item)}>
                              <Pencil size={15} />
                            </button>
                          ) : null}
                          {onDeleteRecord ? (
                            <button
                              className="crm-icon-button crm-icon-button--danger"
                              type="button"
                              aria-label="删除记录"
                              title="删除"
                              onClick={() => handleDeleteRecord(item)}
                            >
                              <Trash2 size={15} />
                            </button>
                          ) : null}
                        </div>
                      ) : null}
                    </article>
                  )
                })}
                {!items.length ? <div className="crm-board-empty">拖入卡片或新建记录后进入该阶段。</div> : null}
              </div>
            </section>
          ))}
        </div>
      )}
      {!loading && !error && !visibleRecords.length ? <EmptyState icon={Icon} title={`暂无${title}数据`} subtitle="后端演示数据同步后会显示在这里。" /> : null}
      <CreateRecordModal
        open={createOpen}
        title={editingRecord ? `编辑${title}` : createLabel}
        columns={columns}
        workflowField={workflowField}
        draft={draft}
        onDraftChange={setDraft}
        onClose={() => {
          setCreateOpen(false)
          setEditingRecord(null)
        }}
        onSubmit={handleSubmitCreate}
        submitting={createSaving}
      />
      <ConfirmDialog
        open={Boolean(confirmRequest)}
        title={confirmRequest?.title ?? ''}
        message={confirmRequest?.message ?? ''}
        confirmLabel={confirmRequest?.confirmLabel ?? '确认'}
        submitting={deleteSaving}
        onCancel={() => setConfirmRequest(null)}
        onConfirm={confirmRequest?.onConfirm}
      />
    </div>
  )
}

function TasksPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const { records: fetchedTasks, loading, error } = useRemoteRecords(fetchTasks, mapTaskRecord)
  const taskCreateColumns = useMemo(
    () => [
      { key: 'title', label: '任务标题' },
      { key: 'description', label: '任务说明', defaultValue: '', required: false },
      { key: 'owner', label: '负责人' },
      { key: 'dueDate', label: '到期时间', defaultValue: '' },
      { key: 'priority', label: '优先级', inputType: 'select', options: ['hot', 'warm', 'cold'], defaultValue: 'warm' },
      { key: 'statusLabel', label: '状态', inputType: 'select', options: ['今天', '本周', '逾期'], defaultValue: '本周' },
    ],
    [],
  )
  const createTaskDraft = () => ({
    ...createDraftFromColumns(taskCreateColumns),
    owner: activeProfile.name,
  })
  const [tasks, setTasks] = useState(fetchedTasks)
  const [createOpen, setCreateOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)
  const [deleteSaving, setDeleteSaving] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [createError, setCreateError] = useState('')
  const [confirmRequest, setConfirmRequest] = useState(null)
  const [draft, setDraft] = useState(createTaskDraft)
  const tabs = [
    { key: 'all', label: '全部' },
    { key: 'overdue', label: '逾期', predicate: (item) => item.status === 'overdue' },
    { key: 'today', label: '今天', predicate: (item) => item.status === 'today' },
    { key: 'week', label: '本周', predicate: (item) => item.status === 'week' },
  ]

  const { activeTab, setActiveTab } = useResourceUrlState({
    tabKeys: tabs.map((tab) => tab.key),
    defaultTab: 'all',
  })
  const visibleTasks = tabs.find((tab) => tab.key === activeTab)?.predicate
    ? tasks.filter(tabs.find((tab) => tab.key === activeTab).predicate)
    : tasks

  useEffect(() => {
    setTasks(fetchedTasks)
  }, [fetchedTasks])

  const handleOpenCreate = () => {
    setEditingTask(null)
    setDraft(createTaskDraft())
    setCreateError('')
    setCreateOpen(true)
  }

  const handleOpenEdit = (task) => {
    setEditingTask(task)
    setDraft(buildDraftFromRecord(taskCreateColumns, task))
    setCreateError('')
    setCreateOpen(true)
  }

  const handleSubmitCreate = async (event) => {
    event.preventDefault()
    setCreateSaving(true)
    setCreateError('')
    try {
      if (editingTask) {
        const task = await updateTask(editingTask.id, buildTaskPayload(draft, activeProfile.name))
        const mappedTask = mapTaskRecord(task)
        setTasks((currentTasks) => currentTasks.map((item) => (item.id === editingTask.id ? mappedTask : item)))
      } else {
        const task = await createTask(buildTaskPayload(draft, activeProfile.name))
        setTasks((currentTasks) => [mapTaskRecord(task), ...currentTasks])
      }
      setCreateOpen(false)
      setEditingTask(null)
    } catch (nextError) {
      setCreateError(nextError.message || (editingTask ? '更新任务失败' : '新建任务失败'))
    } finally {
      setCreateSaving(false)
    }
  }

  const handleDeleteTask = async (task) => {
    setConfirmRequest({
      title: '删除任务',
      message: `确认删除 ${task.title}？系统会调用后端任务 DELETE 接口，跨负责人或无权限删除会被后端拒绝。`,
      confirmLabel: '确认删除',
      onConfirm: async () => {
        setDeleteSaving(true)
        setCreateError('')
        try {
          await deleteTask(task.id)
          setTasks((currentTasks) => currentTasks.filter((item) => item.id !== task.id))
          setConfirmRequest(null)
        } catch (nextError) {
          setCreateError(nextError.message || '删除任务失败')
        } finally {
          setDeleteSaving(false)
        }
      },
    })
  }

  return (
    <div className="crm-page-stack">
      <ResourceHeader
        title="任务"
        subtitle="按优先级和到期时间管理个人与团队任务。"
        icon={CheckSquare}
        createLabel="新建任务"
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onCreate={handleOpenCreate}
      />
      <ResourceSyncState loading={loading || createSaving || deleteSaving} error={error || createError} />

      <section className="crm-task-grid">
        {visibleTasks.map((task) => (
          <article key={task.id} className="crm-panel crm-task-card">
            <div className="crm-task-card-head">
              <StatusBadge value={task.priority} tone={statusToneMap[task.priority] ?? 'neutral'} />
              <StatusBadge value={task.statusLabel} tone={statusToneMap[task.status] ?? 'neutral'} />
            </div>
            <strong>{task.title}</strong>
            <p>{task.description}</p>
            <div className="crm-task-card-foot">
              <span>{task.owner}</span>
              <time>{task.dueDate}</time>
            </div>
            <div className="crm-row-actions">
              <button className="crm-icon-button" type="button" aria-label="编辑任务" title="编辑" onClick={() => handleOpenEdit(task)}>
                <Pencil size={15} />
              </button>
              <button
                className="crm-icon-button crm-icon-button--danger"
                type="button"
                aria-label="删除任务"
                title="删除"
                onClick={() => handleDeleteTask(task)}
              >
                <Trash2 size={15} />
              </button>
            </div>
          </article>
        ))}
      </section>
      {!loading && !error && !visibleTasks.length ? <EmptyState icon={CheckSquare} title="暂无任务" subtitle="后端任务数据同步后会显示在这里。" /> : null}
      <CreateRecordModal
        open={createOpen}
        title={editingTask ? '编辑任务' : '新建任务'}
        columns={taskCreateColumns}
        draft={draft}
        onDraftChange={setDraft}
        onClose={() => {
          setCreateOpen(false)
          setEditingTask(null)
        }}
        onSubmit={handleSubmitCreate}
        submitting={createSaving}
      />
      <ConfirmDialog
        open={Boolean(confirmRequest)}
        title={confirmRequest?.title ?? ''}
        message={confirmRequest?.message ?? ''}
        confirmLabel={confirmRequest?.confirmLabel ?? '确认'}
        submitting={deleteSaving}
        onCancel={() => setConfirmRequest(null)}
        onConfirm={confirmRequest?.onConfirm}
      />
    </div>
  )
}

function GoalsPage() {
  const { userProfile: activeProfile } = useOutletContext()
  const { records: fetchedGoals, loading, error } = useRemoteRecords(fetchGoals, mapGoalRecord)
  const ownerDraftDefault = useMemo(() => ({ key: 'owner', value: activeProfile.name }), [activeProfile.name])
  const goalCreateColumns = useMemo(
    () => [
      { key: 'name', label: '目标名称', defaultValue: '' },
      { key: 'period', label: '周期', defaultValue: '' },
      { key: 'owner', label: '负责人' },
      { key: 'current', label: '当前值', format: 'currency' },
      { key: 'target', label: '目标值', format: 'currency', defaultValue: '' },
      { key: 'note', label: '说明', defaultValue: '', required: false },
    ],
    [],
  )
  const [goals, setGoals] = useState(fetchedGoals)
  const [createOpen, setCreateOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)
  const [deleteSaving, setDeleteSaving] = useState(false)
  const [editingGoal, setEditingGoal] = useState(null)
  const [createError, setCreateError] = useState('')
  const [confirmRequest, setConfirmRequest] = useState(null)
  const [draft, setDraft] = useState(() => createDraftFromColumns(goalCreateColumns, ownerDraftDefault))

  useEffect(() => {
    setGoals(fetchedGoals)
  }, [fetchedGoals])

  const handleOpenCreate = () => {
    setEditingGoal(null)
    setDraft(createDraftFromColumns(goalCreateColumns, ownerDraftDefault))
    setCreateError('')
    setCreateOpen(true)
  }

  const handleOpenEdit = (goal) => {
    setEditingGoal(goal)
    setDraft(buildDraftFromRecord(goalCreateColumns, goal))
    setCreateError('')
    setCreateOpen(true)
  }

  const handleSubmitCreate = async (event) => {
    event.preventDefault()
    setCreateSaving(true)
    setCreateError('')
    try {
      if (editingGoal) {
        const goal = await updateGoal(editingGoal.id, buildGoalPayload(draft, activeProfile.name))
        const mappedGoal = mapGoalRecord(goal)
        setGoals((currentGoals) => currentGoals.map((item) => (item.id === editingGoal.id ? mappedGoal : item)))
      } else {
        const goal = await createGoal(buildGoalPayload(draft, activeProfile.name))
        setGoals((currentGoals) => [mapGoalRecord(goal), ...currentGoals])
      }
      setCreateOpen(false)
      setEditingGoal(null)
    } catch (nextError) {
      setCreateError(nextError.message || (editingGoal ? '更新目标失败' : '新建目标失败'))
    } finally {
      setCreateSaving(false)
    }
  }

  const handleDeleteGoal = async (goal) => {
    setConfirmRequest({
      title: '删除销售目标',
      message: `确认删除 ${goal.name}？系统会调用后端销售目标 DELETE 接口，销售 owner 数据范围和权限规则仍会生效。`,
      confirmLabel: '确认删除',
      onConfirm: async () => {
        setDeleteSaving(true)
        setCreateError('')
        try {
          await deleteGoal(goal.id)
          setGoals((currentGoals) => currentGoals.filter((item) => item.id !== goal.id))
          setConfirmRequest(null)
        } catch (nextError) {
          setCreateError(nextError.message || '删除目标失败')
        } finally {
          setDeleteSaving(false)
        }
      },
    })
  }

  return (
    <div className="crm-page-stack">
      <ResourceHeader title="销售目标" subtitle="季度目标、完成进度和预测结果一屏查看。" icon={Trophy} createLabel="新建目标" onCreate={handleOpenCreate} />
      <ResourceSyncState loading={loading || createSaving || deleteSaving} error={error || createError} />

      <section className="crm-goal-grid">
        {goals.map((goal) => (
          <article key={goal.id} className="crm-panel crm-goal-card">
            <div className="crm-goal-card-head">
              <div>
                <strong>{goal.name}</strong>
                <span>{goal.period} · {goal.owner}</span>
              </div>
              <div className="crm-goal-card-actions">
                <StatusBadge value={`${goal.progress}%`} tone={goal.progress >= 80 ? 'success' : 'warning'} />
                <div className="crm-row-actions">
                  <button className="crm-icon-button" type="button" aria-label="编辑目标" title="编辑" onClick={() => handleOpenEdit(goal)}>
                    <Pencil size={15} />
                  </button>
                  <button
                    className="crm-icon-button crm-icon-button--danger"
                    type="button"
                    aria-label="删除目标"
                    title="删除"
                    onClick={() => handleDeleteGoal(goal)}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </div>
            <div className="crm-goal-values">
              <strong>{formatCurrency(goal.current)}</strong>
              <span>目标 {formatCurrency(goal.target)}</span>
            </div>
            <div className="crm-progress-track">
              <div className="crm-progress-bar tone-won" style={{ width: `${goal.progress}%` }} />
            </div>
            <p>{goal.note}</p>
          </article>
        ))}
      </section>
      {!loading && !error && !goals.length ? <EmptyState icon={Trophy} title="暂无销售目标" subtitle="后端目标数据同步后会显示在这里。" /> : null}
      <CreateRecordModal
        open={createOpen}
        title={editingGoal ? '编辑目标' : '新建目标'}
        columns={goalCreateColumns}
        draft={draft}
        onDraftChange={setDraft}
        onClose={() => {
          setCreateOpen(false)
          setEditingGoal(null)
        }}
        onSubmit={handleSubmitCreate}
        submitting={createSaving}
      />
      <ConfirmDialog
        open={Boolean(confirmRequest)}
        title={confirmRequest?.title ?? ''}
        message={confirmRequest?.message ?? ''}
        confirmLabel={confirmRequest?.confirmLabel ?? '确认'}
        submitting={deleteSaving}
        onCancel={() => setConfirmRequest(null)}
        onConfirm={confirmRequest?.onConfirm}
      />
    </div>
  )
}

function ProfilePage() {
  const navigate = useNavigate()
  const { selectedOrg, userProfile: activeProfile, onLogout, onSessionRefresh } = useOutletContext()
  const [profileDraft, setProfileDraft] = useState(() => createProfileDraft(activeProfile))
  const [passwordDraft, setPasswordDraft] = useState(createPasswordDraft)
  const [profileSaving, setProfileSaving] = useState(false)
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [sessions, setSessions] = useState([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [sessionsError, setSessionsError] = useState('')
  const [sessionStatus, setSessionStatus] = useState('')
  const [revokingSessionId, setRevokingSessionId] = useState(null)
  const [bulkRevokingSessions, setBulkRevokingSessions] = useState(false)
  const [profileStatus, setProfileStatus] = useState('')
  const [passwordStatus, setPasswordStatus] = useState('')
  const {
    id: profileId,
    name: profileName,
    email: profileEmail,
    phone: profilePhone,
    position: profilePosition,
    department: profileDepartment,
    location: profileLocation,
  } = activeProfile

  useEffect(() => {
    setProfileDraft({
      fullName: profileName ?? '',
      email: profileEmail ?? '',
      phone: profilePhone ?? '',
      position: profilePosition ?? '',
      department: profileDepartment ?? '',
      location: profileLocation ?? '',
    })
  }, [profileId, profileName, profileEmail, profilePhone, profilePosition, profileDepartment, profileLocation])

  const loadAuthSessions = useCallback(async () => {
    setSessionsLoading(true)
    setSessionsError('')
    try {
      const payload = await fetchAuthSessions()
      setSessions(Array.isArray(payload) ? payload : [])
    } catch (requestError) {
      setSessionsError(requestError.message || '会话同步失败')
    } finally {
      setSessionsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAuthSessions()
  }, [loadAuthSessions])

  const securityInfo = [
    { label: '登录方式', value: '账号密码', tone: 'neutral' },
    { label: '账户状态', value: activeProfile.status === 'active' ? '正常' : '停用', tone: activeProfile.status === 'active' ? 'success' : 'danger' },
    { label: '组织权限', value: selectedOrg.role, tone: 'accent' },
    { label: '权限策略', value: activeProfile.permissions.includes('*') ? '全部权限' : `${activeProfile.permissions.length} 项权限`, tone: 'info' },
    { label: '数据范围', value: dataScopeLabelMap[activeProfile.dataScope] ?? activeProfile.dataScope, tone: activeProfile.dataScope === 'own' ? 'warning' : 'success' },
  ]

  const activeSessionCount = sessions.filter((session) => session.status === 'active').length
  const otherActiveSessionCount = sessions.filter((session) => session.status === 'active' && !session.current).length

  const handleProfileDraftChange = (field, value) => {
    setProfileDraft((currentDraft) => ({ ...currentDraft, [field]: value }))
    setProfileStatus('')
    setProfileError('')
  }

  const handlePasswordDraftChange = (field, value) => {
    setPasswordDraft((currentDraft) => ({ ...currentDraft, [field]: value }))
    setPasswordStatus('')
    setPasswordError('')
  }

  const handleProfileSubmit = async (event) => {
    event.preventDefault()
    setProfileSaving(true)
    setProfileError('')
    setProfileStatus('')
    try {
      const payload = await updateAuthProfile(buildProfilePayload(profileDraft))
      onSessionRefresh?.(payload)
      setProfileStatus('个人资料已保存')
    } catch (requestError) {
      setProfileError(requestError.message || '个人资料保存失败')
    } finally {
      setProfileSaving(false)
    }
  }

  const handlePasswordSubmit = async (event) => {
    event.preventDefault()
    setPasswordSaving(true)
    setPasswordError('')
    setPasswordStatus('')
    try {
      await changeAuthPassword(buildPasswordPayload(passwordDraft))
      setPasswordDraft(createPasswordDraft())
      setPasswordStatus('密码已更新，其他设备的旧会话已撤销')
      loadAuthSessions()
    } catch (requestError) {
      setPasswordError(requestError.message || '密码修改失败')
    } finally {
      setPasswordSaving(false)
    }
  }

  const handleRevokeSession = async (sessionId) => {
    setRevokingSessionId(sessionId)
    setSessionStatus('')
    setSessionsError('')
    try {
      await revokeAuthSession(sessionId)
      setSessionStatus('会话已撤销')
      await loadAuthSessions()
    } catch (requestError) {
      setSessionsError(requestError.message || '会话撤销失败')
    } finally {
      setRevokingSessionId(null)
    }
  }

  const handleRevokeOtherSessions = async () => {
    setBulkRevokingSessions(true)
    setSessionStatus('')
    setSessionsError('')
    try {
      const payload = await revokeOtherAuthSessions()
      setSessionStatus(`已撤销其他会话 ${payload.revoked_sessions ?? 0} 个`)
      await loadAuthSessions()
    } catch (requestError) {
      setSessionsError(requestError.message || '批量撤销失败')
    } finally {
      setBulkRevokingSessions(false)
    }
  }

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-profile-hero">
        <div className="crm-profile-hero-main">
          <img className="crm-profile-avatar" src={smartCrmLogo} alt="Smart CRM 小猪头像" />
          <div className="crm-profile-copy">
            <span className="crm-overline">个人主页</span>
            <h2>{activeProfile.name}</h2>
            <div className="crm-profile-meta">
              <span>{activeProfile.position}</span>
              <span>{selectedOrg.name}</span>
              <span>{selectedOrg.role}</span>
            </div>
          </div>
        </div>

        <div className="crm-profile-actions">
          <button className="crm-ghost-button" type="button" onClick={() => navigate('/org')}>
            <Building2 size={16} />
            切换组织
          </button>
          <button
            className="crm-ghost-button crm-ghost-button--danger"
            type="button"
            onClick={async () => {
              await onLogout()
              navigate('/login')
            }}
          >
            <LogOut size={16} />
            退出登录
          </button>
        </div>
      </section>

      <section className="crm-profile-workspace">
        <article className="crm-panel crm-profile-card crm-profile-card--wide">
          <PanelHeader title="基础信息" subtitle="这些资料来自当前登录账号，保存后会写入后端并刷新全局会话。" actionLabel={profileStatus || '真实账号资料'} />
          <form className="crm-profile-form" onSubmit={handleProfileSubmit}>
            <div className="crm-form-grid">
              <label className="crm-field">
                <span>姓名</span>
                <input value={profileDraft.fullName} onChange={(event) => handleProfileDraftChange('fullName', event.target.value)} required minLength={2} />
              </label>
              <label className="crm-field">
                <span>邮箱</span>
                <input type="email" value={profileDraft.email} onChange={(event) => handleProfileDraftChange('email', event.target.value)} required />
              </label>
              <label className="crm-field">
                <span>手机号</span>
                <input value={profileDraft.phone} onChange={(event) => handleProfileDraftChange('phone', event.target.value)} />
              </label>
              <label className="crm-field">
                <span>岗位</span>
                <input value={profileDraft.position} onChange={(event) => handleProfileDraftChange('position', event.target.value)} />
              </label>
              <label className="crm-field">
                <span>部门</span>
                <input value={profileDraft.department} onChange={(event) => handleProfileDraftChange('department', event.target.value)} />
              </label>
              <label className="crm-field">
                <span>办公地点</span>
                <input value={profileDraft.location} onChange={(event) => handleProfileDraftChange('location', event.target.value)} />
              </label>
            </div>
            {profileError ? <div className="crm-form-error">{profileError}</div> : null}
            {profileStatus ? <div className="crm-form-success">{profileStatus}</div> : null}
            <div className="crm-form-actions">
              <button className="crm-ghost-button" type="button" onClick={() => setProfileDraft(createProfileDraft(activeProfile))}>
                <RefreshCw size={16} />
                恢复当前资料
              </button>
              <button className="crm-primary-button" type="submit" disabled={profileSaving}>
                <Save size={16} />
                {profileSaving ? '保存中...' : '保存资料'}
              </button>
            </div>
          </form>
        </article>

        <div className="crm-profile-side">
          <article className="crm-panel crm-profile-card">
            <PanelHeader title="账号安全" subtitle="修改密码会保留当前会话，并撤销同账号其他旧会话。" actionLabel={passwordStatus || '会话保护'} />
            <div className="crm-profile-info-list">
              {securityInfo.map((item) => (
                <div key={item.label} className="crm-profile-info-item">
                  <span>{item.label}</span>
                  <StatusBadge value={item.value} tone={item.tone} />
                </div>
              ))}
            </div>
            <form className="crm-profile-form crm-profile-password-form" onSubmit={handlePasswordSubmit}>
              <label className="crm-field">
                <span>当前密码</span>
                <input type="password" value={passwordDraft.currentPassword} onChange={(event) => handlePasswordDraftChange('currentPassword', event.target.value)} autoComplete="current-password" required />
              </label>
              <label className="crm-field">
                <span>新密码</span>
                <input type="password" value={passwordDraft.newPassword} onChange={(event) => handlePasswordDraftChange('newPassword', event.target.value)} autoComplete="new-password" required minLength={6} />
              </label>
              <label className="crm-field">
                <span>确认新密码</span>
                <input type="password" value={passwordDraft.confirmPassword} onChange={(event) => handlePasswordDraftChange('confirmPassword', event.target.value)} autoComplete="new-password" required minLength={6} />
              </label>
              {passwordError ? <div className="crm-form-error">{passwordError}</div> : null}
              {passwordStatus ? <div className="crm-form-success">{passwordStatus}</div> : null}
              <div className="crm-form-actions">
                <button className="crm-primary-button" type="submit" disabled={passwordSaving}>
                  <KeyRound size={16} />
                  {passwordSaving ? '更新中...' : '更新密码'}
                </button>
              </div>
            </form>
          </article>

          <article className="crm-panel crm-profile-card">
            <PanelHeader title="当前组织" actionLabel="已连接" />
            <div className="crm-profile-info-list">
              <div className="crm-profile-info-item">
                <span>组织名称</span>
                <strong>{selectedOrg.name}</strong>
              </div>
              <div className="crm-profile-info-item">
                <span>我的角色</span>
                <strong>{selectedOrg.role}</strong>
              </div>
              <div className="crm-profile-info-item">
                <span>加入时间</span>
                <strong>{activeProfile.joinDate}</strong>
              </div>
              <div className="crm-profile-info-item">
                <span>工作区状态</span>
                <StatusBadge value="已连接" tone="success" />
              </div>
            </div>
          </article>

          <article className="crm-panel crm-profile-card">
            <PanelHeader
              title="登录会话"
              subtitle="从后端 AuthSession 表读取，可撤销当前账号的其他活跃会话。"
              actionLabel={sessionsLoading ? '同步中' : `${activeSessionCount} 个活跃`}
            />
            {sessionsError ? <div className="crm-form-error">{sessionsError}</div> : null}
            {sessionStatus ? <div className="crm-form-success">{sessionStatus}</div> : null}
            <div className="crm-profile-session-list">
              {sessions.map((session) => (
                <div key={session.id} className="crm-profile-session-item">
                  <div className="crm-profile-session-head">
                    <div>
                      <strong>{session.current ? '当前会话' : `会话 #${session.id}`}</strong>
                      <span>创建 {formatDateTime(session.created_at)}</span>
                    </div>
                    <StatusBadge
                      value={session.current ? '当前' : authSessionStatusLabelMap[session.status] ?? session.status}
                      tone={session.current ? 'accent' : authSessionStatusToneMap[session.status] ?? 'neutral'}
                    />
                  </div>
                  <div className="crm-profile-session-meta">
                    <span>过期 {formatDateTime(session.expires_at)}</span>
                    {session.revoked_at ? <span>撤销 {formatDateTime(session.revoked_at)}</span> : null}
                  </div>
                  {session.status === 'active' && !session.current ? (
                    <button
                      className="crm-ghost-button crm-ghost-button--danger"
                      type="button"
                      onClick={() => handleRevokeSession(session.id)}
                      disabled={revokingSessionId === session.id}
                    >
                      <Trash2 size={16} />
                      {revokingSessionId === session.id ? '撤销中...' : '撤销会话'}
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
            {!sessionsLoading && !sessions.length ? <EmptyState icon={Shield} title="暂无会话记录" subtitle="重新登录后会显示当前账号的会话。" /> : null}
            <div className="crm-form-actions">
              <button className="crm-ghost-button" type="button" onClick={loadAuthSessions} disabled={sessionsLoading}>
                <RefreshCw size={16} />
                刷新会话
              </button>
              <button
                className="crm-ghost-button crm-ghost-button--danger"
                type="button"
                onClick={handleRevokeOtherSessions}
                disabled={bulkRevokingSessions || otherActiveSessionCount === 0}
              >
                <Shield size={16} />
                {bulkRevokingSessions ? '撤销中...' : `撤销其他 ${otherActiveSessionCount} 个`}
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>
  )
}

function ResourceHeader({
  title,
  subtitle,
  icon: Icon,
  createLabel,
  tabs = [],
  activeTab,
  onTabChange,
  onCreate,
  onFocusSearch,
  onExport,
  exportDisabled = false,
}) {
  return (
    <section className="crm-resource-header">
      <div>
        <div className="crm-resource-title">
          <div className="crm-resource-icon">
            <Icon size={18} />
          </div>
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>
        </div>

        {tabs.length ? (
          <div className="crm-tabs">
            {tabs.map((tab) => (
              <button key={tab.key} className={activeTab === tab.key ? 'is-active' : ''} type="button" onClick={() => onTabChange(tab.key)}>
                {tab.label}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      <div className="crm-toolbar-actions">
        <button className="crm-ghost-button" type="button" onClick={onFocusSearch}>
          <Filter size={16} />
          过滤器
        </button>
        <button className="crm-ghost-button" type="button" onClick={onExport} disabled={exportDisabled}>
          <Download size={16} />
          导出 CSV
        </button>
        <button className="crm-primary-button" type="button" onClick={onCreate}>
          <Plus size={16} />
          {createLabel}
        </button>
      </div>
    </section>
  )
}

function OrderItemsEditor({ products, items, totalAmount, onAddItem, onRemoveItem, onItemChange }) {
  return (
    <div className="crm-order-lines-editor">
      <div className="crm-order-lines-head">
        <div>
          <strong>订单商品明细</strong>
          <small>保存后自动重算订单金额，并按净差额扣减或回补库存。</small>
        </div>
        <button className="crm-ghost-button" type="button" onClick={onAddItem} disabled={!products.length}>
          <Plus size={16} />
          添加明细
        </button>
      </div>

      <div className="crm-table-wrap">
        <table className="crm-table crm-order-lines-table">
          <thead>
            <tr>
              <th>商品</th>
              <th>数量</th>
              <th>单价</th>
              <th>小计</th>
              <th className="crm-table-actions-cell">操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.draftId}>
                <td>
                  <select
                    className="crm-order-line-control"
                    value={item.productId}
                    onChange={(event) => onItemChange(item.draftId, 'productId', event.target.value)}
                    required
                  >
                    <option value="">选择商品</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name} / {product.sku}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    className="crm-order-line-control is-number"
                    type="number"
                    min="1"
                    step="1"
                    value={item.quantity}
                    onChange={(event) => onItemChange(item.draftId, 'quantity', event.target.value)}
                    required
                  />
                </td>
                <td>
                  <input
                    className="crm-order-line-control is-number"
                    type="number"
                    min="0.01"
                    step="100"
                    value={item.unitPrice}
                    onChange={(event) => onItemChange(item.draftId, 'unitPrice', event.target.value)}
                    required
                  />
                </td>
                <td>{formatCurrency(calculateOrderLineTotal(item))}</td>
                <td className="crm-table-actions-cell">
                  <button className="crm-icon-button crm-icon-button--danger" type="button" aria-label="删除订单明细" title="删除" onClick={() => onRemoveItem(item.draftId)} disabled={items.length <= 1}>
                    <Trash2 size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="crm-order-lines-total">
        <span>重算订单总额</span>
        <strong>{formatCurrency(totalAmount)}</strong>
      </div>
    </div>
  )
}

function TeamMemberModal({ open, editingMember, draft, currentUserId, currentUserRole, onDraftChange, onClose, onSubmit, submitting = false }) {
  if (!open) {
    return null
  }

  const editableRoles = currentUserRole === '管理员'
    ? teamRoleOptions
    : teamRoleOptions.filter((role) => role !== '管理员')
  const isSelf = editingMember?.id === currentUserId

  const handleChange = (key, value) => {
    onDraftChange((currentDraft) => ({ ...currentDraft, [key]: value }))
  }

  return (
    <div className="crm-modal-backdrop" role="presentation">
      <form className="crm-modal" onSubmit={onSubmit}>
        <div className="crm-modal-head">
          <div>
            <span className="crm-overline">组织成员</span>
            <h3>{editingMember ? '编辑团队成员' : '新增团队成员'}</h3>
          </div>
          <button className="crm-icon-button" type="button" aria-label="关闭" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="crm-form-grid">
          <label className="crm-field">
            <span>姓名</span>
            <input value={draft.fullName} onChange={(event) => handleChange('fullName', event.target.value)} required />
          </label>
          <label className="crm-field">
            <span>邮箱</span>
            <input type="email" value={draft.email} onChange={(event) => handleChange('email', event.target.value)} required />
          </label>
          <label className="crm-field">
            <span>手机</span>
            <input value={draft.phone} onChange={(event) => handleChange('phone', event.target.value)} />
          </label>
          <label className="crm-field">
            <span>角色</span>
            <select value={draft.role} onChange={(event) => handleChange('role', event.target.value)} disabled={isSelf}>
              {editableRoles.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
          </label>
          <label className="crm-field">
            <span>岗位</span>
            <input value={draft.position} onChange={(event) => handleChange('position', event.target.value)} required />
          </label>
          <label className="crm-field">
            <span>部门</span>
            <input value={draft.department} onChange={(event) => handleChange('department', event.target.value)} required />
          </label>
          <label className="crm-field">
            <span>地点</span>
            <input value={draft.location} onChange={(event) => handleChange('location', event.target.value)} required />
          </label>
          <label className="crm-field">
            <span>账号状态</span>
            <select value={draft.status} onChange={(event) => handleChange('status', event.target.value)} disabled={isSelf}>
              {teamStatusOptions.map((status) => <option key={status} value={status}>{teamStatusLabelMap[status]}</option>)}
            </select>
          </label>
          <label className="crm-field">
            <span>{editingMember ? '新密码' : '登录密码'}</span>
            <input type="password" value={draft.password} onChange={(event) => handleChange('password', event.target.value)} required={!editingMember} minLength={6} />
          </label>
          <label className="crm-field">
            <span>{editingMember ? '确认新密码' : '确认密码'}</span>
            <input type="password" value={draft.confirmPassword} onChange={(event) => handleChange('confirmPassword', event.target.value)} required={!editingMember} minLength={6} />
          </label>
        </div>

        <div className="crm-modal-actions">
          <button className="crm-ghost-button" type="button" onClick={onClose}>
            取消
          </button>
          <button className="crm-primary-button" type="submit" disabled={submitting}>
            {submitting ? '保存中' : '保存成员'}
          </button>
        </div>
      </form>
    </div>
  )
}

function ConfirmDialog({ open, title, message, confirmLabel = '确认', cancelLabel = '取消', submitting = false, onCancel, onConfirm }) {
  if (!open) {
    return null
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!onConfirm || submitting) {
      return
    }
    await onConfirm()
  }

  return (
    <div className="crm-modal-backdrop" role="presentation">
      <form className="crm-modal crm-confirm-modal" onSubmit={handleSubmit}>
        <div className="crm-modal-head">
          <div>
            <span className="crm-overline">确认操作</span>
            <h3>{title}</h3>
          </div>
          <button className="crm-icon-button" type="button" aria-label="关闭" onClick={onCancel} disabled={submitting}>
            <X size={16} />
          </button>
        </div>

        <div className="crm-confirm-body">
          <div className="crm-confirm-icon" aria-hidden="true">
            <Trash2 size={18} />
          </div>
          <p>{message}</p>
        </div>

        <div className="crm-modal-actions">
          <button className="crm-ghost-button" type="button" onClick={onCancel} disabled={submitting}>
            {cancelLabel}
          </button>
          <button className="crm-ghost-button crm-ghost-button--danger" type="submit" disabled={submitting || !onConfirm}>
            <Trash2 size={16} />
            {submitting ? '处理中...' : confirmLabel}
          </button>
        </div>
      </form>
    </div>
  )
}

function CreateRecordModal({ open, title, columns, workflowField, draft, onDraftChange, onClose, onSubmit, submitting = false, children }) {
  if (!open) {
    return null
  }

  const handleChange = (key, value) => {
    onDraftChange((currentDraft) => ({ ...currentDraft, [key]: value }))
  }

  return (
    <div className="crm-modal-backdrop" role="presentation">
      <form className="crm-modal" onSubmit={onSubmit}>
        <div className="crm-modal-head">
          <div>
            <span className="crm-overline">{title.startsWith('编辑') ? '记录维护' : '快速创建'}</span>
            <h3>{title}</h3>
          </div>
          <button className="crm-icon-button" type="button" aria-label="关闭" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="crm-form-grid">
          {workflowField ? (
            <label className="crm-field">
              <span>{workflowField.label}</span>
              <select value={draft[workflowField.key] ?? workflowField.value} onChange={(event) => handleChange(workflowField.key, event.target.value)}>
                {workflowField.options.map((option) => (
                  <option key={option} value={option}>
                    {workflowField.optionLabels?.[option] ?? option}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {columns.map((column) => (
            <label key={column.key} className="crm-field">
              <span>{column.label}</span>
              {column.options ? (
                <select value={draft[column.key] ?? column.defaultValue ?? column.options[0] ?? ''} onChange={(event) => handleChange(column.key, event.target.value)} required={column.required !== false}>
                  {column.options.map((option) => (
                    <option key={option} value={option}>
                      {column.optionLabels?.[option] ?? option}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={column.inputType ?? (column.format === 'currency' ? 'number' : 'text')}
                  min={column.format === 'currency' ? '0' : undefined}
                  step={column.format === 'currency' ? '1000' : undefined}
                  value={draft[column.key] ?? ''}
                  onChange={(event) => handleChange(column.key, event.target.value)}
                  required={column.required !== false}
                />
              )}
            </label>
          ))}
        </div>

        {children ? <div className="crm-modal-extra">{children}</div> : null}

        <div className="crm-modal-actions">
          <button className="crm-ghost-button" type="button" onClick={onClose}>
            取消
          </button>
          <button className="crm-primary-button" type="submit" disabled={submitting}>
            {submitting ? '保存中' : '保存'}
          </button>
        </div>
      </form>
    </div>
  )
}

function BulkEditModal({ open, title, columns, draft, selectedCount, onDraftChange, onClose, onSubmit, submitting = false }) {
  if (!open) {
    return null
  }

  const enabledCount = columns.filter((column) => draft[column.key]?.enabled).length

  const handleToggleField = (key) => {
    onDraftChange((currentDraft) => ({
      ...currentDraft,
      [key]: {
        enabled: !currentDraft[key]?.enabled,
        value: currentDraft[key]?.value ?? '',
      },
    }))
  }

  const handleChangeValue = (key, value) => {
    onDraftChange((currentDraft) => ({
      ...currentDraft,
      [key]: {
        enabled: currentDraft[key]?.enabled ?? true,
        value,
      },
    }))
  }

  return (
    <div className="crm-modal-backdrop" role="presentation">
      <form className="crm-modal" onSubmit={onSubmit}>
        <div className="crm-modal-head">
          <div>
            <span className="crm-overline">批量维护 · {selectedCount} 条</span>
            <h3>{title}</h3>
          </div>
          <button className="crm-icon-button" type="button" aria-label="关闭" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="crm-bulk-edit-grid">
          {columns.map((column) => {
            const field = draft[column.key] ?? { enabled: false, value: '' }
            return (
              <label key={column.key} className={`crm-bulk-edit-field${field.enabled ? ' is-enabled' : ''}`}>
                <span className="crm-bulk-edit-toggle">
                  <input type="checkbox" checked={field.enabled} onChange={() => handleToggleField(column.key)} />
                  <strong>{column.label}</strong>
                </span>
                {column.options ? (
                  <select
                    value={field.value || column.defaultValue || column.options[0] || ''}
                    disabled={!field.enabled}
                    onChange={(event) => handleChangeValue(column.key, event.target.value)}
                  >
                    {column.options.map((option) => (
                      <option key={option} value={option}>
                        {column.optionLabels?.[option] ?? option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={column.inputType ?? (column.format === 'currency' ? 'number' : 'text')}
                    min={column.format === 'currency' ? '0' : undefined}
                    step={column.format === 'currency' ? '1000' : undefined}
                    value={field.value}
                    disabled={!field.enabled}
                    placeholder={`批量设置${column.label}`}
                    onChange={(event) => handleChangeValue(column.key, event.target.value)}
                  />
                )}
              </label>
            )
          })}
        </div>

        <div className="crm-modal-actions">
          <button className="crm-ghost-button" type="button" onClick={onClose}>
            取消
          </button>
          <button className="crm-primary-button" type="submit" disabled={submitting || !enabledCount}>
            {submitting ? '保存中' : `更新 ${selectedCount} 条`}
          </button>
        </div>
      </form>
    </div>
  )
}

function ResourceToolbar({ query, onQueryChange, columnCount, children, inputRef, preferenceStatus = '' }) {
  return (
    <section className="crm-toolbar-card">
      <label className="crm-search-box">
        <Search size={16} />
        <input ref={inputRef} placeholder="搜索姓名、公司、负责人或备注" value={query} onChange={(event) => onQueryChange(event.target.value)} />
      </label>
      <div className="crm-toolbar-right">
        {children}
        {preferenceStatus ? <div className="crm-column-badge">{preferenceStatus}</div> : null}
        <div className="crm-column-badge">{columnCount} 列</div>
      </div>
    </section>
  )
}

function PanelHeader({ title, subtitle = '', actionLabel, actionHref = '', actionOnClick }) {
  const actionContent = actionLabel ? (
    <>
      {actionLabel}
      {actionHref || actionOnClick ? <ArrowRight size={14} /> : null}
    </>
  ) : null

  return (
    <div className="crm-panel-header">
      <div>
        <strong>{title}</strong>
        {subtitle ? <small>{subtitle}</small> : null}
      </div>
      {actionHref ? <NavLink className="crm-link-button" to={actionHref}>{actionContent}</NavLink> : null}
      {!actionHref && actionOnClick ? (
        <button className="crm-link-button" type="button" onClick={actionOnClick}>
          {actionContent}
        </button>
      ) : null}
      {!actionHref && !actionOnClick && actionLabel ? <span className="crm-panel-action-label">{actionContent}</span> : null}
    </div>
  )
}

function EmptyState({ icon: Icon, title, subtitle }) {
  return (
    <div className="crm-empty-state">
      <div className="crm-empty-icon">
        <Icon size={22} />
      </div>
      <strong>{title}</strong>
      <span>{subtitle}</span>
    </div>
  )
}

function ResourceSyncState({ loading, error }) {
  if (!loading && !error) {
    return null
  }

  return (
    <div className={`crm-sync-state ${error ? 'is-error' : ''}`}>
      {error ? <Shield size={16} /> : <Activity size={16} />}
      <span>{error || '正在同步后端演示数据'}</span>
    </div>
  )
}

function StatusBadge({ value, tone = 'neutral', isNumeric = false }) {
  return <span className={`crm-badge tone-${tone} ${isNumeric ? 'is-numeric' : ''}`}>{value}</span>
}

function formatApprovalSla(approval) {
  const statusLabel = approvalSlaLabelMap[approval?.sla_status] ?? 'SLA 未设置'
  const remainingHours = Number(approval?.sla_hours_remaining)
  const hasRemainingHours = Number.isFinite(remainingHours)
  const hourText = hasRemainingHours
    ? remainingHours < 0
      ? `逾期 ${Math.abs(remainingHours)} 小时`
      : `剩余 ${remainingHours} 小时`
    : '暂无倒计时'
  const dueText = approval?.sla_due_at ? formatDateTime(approval.sla_due_at) : '未设置截止时间'
  return `${statusLabel} / ${dueText} / ${hourText}`
}

function renderCell(value, column) {
  if (column.type === 'badge') {
    return <StatusBadge value={String(value)} tone={statusToneMap[String(value)] ?? 'neutral'} />
  }
  if (column.format === 'currency') {
    return formatCurrency(Number(value))
  }
  return value
}

function formatCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatCompactCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

function formatPercent(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'percent',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDateTime(value) {
  if (!value) {
    return '未记录'
  }
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatProfileDate(value) {
  if (!value) {
    return userProfile.joinDate
  }
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(value))
}

function buildUserProfile(user) {
  if (!user) {
    return userProfile
  }
  return {
    id: user.id ?? userProfile.id,
    name: user.full_name || userProfile.name,
    email: user.email || userProfile.email,
    phone: user.phone || userProfile.phone,
    role: user.role || userProfile.role,
    position: user.position || user.role || userProfile.position,
    department: user.department || userProfile.department,
    location: user.location || userProfile.location,
    status: user.status || userProfile.status,
    joinDate: formatProfileDate(user.created_at),
    permissions: user.permissions ?? [],
    dataScope: user.data_scope ?? userProfile.dataScope,
  }
}

function loadStoredAuthSession() {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) {
      return null
    }
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function persistAuthSession(session) {
  try {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
  } catch {
    return undefined
  }
  return undefined
}

function clearStoredAuthSession() {
  try {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
  } catch {
    return undefined
  }
  return undefined
}

function loadStoredOrg(authSession) {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return resolveSelectedOrg(authSession)
    }
    return resolveSelectedOrg(authSession, JSON.parse(raw))
  } catch {
    return resolveSelectedOrg(authSession)
  }
}

function persistOrg(org) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(org))
  } catch {
    return undefined
  }
  return undefined
}

export default App
