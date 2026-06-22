import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  ArrowRight,
  Bell,
  Bot,
  Briefcase,
  Building2,
  Calendar,
  CheckSquare,
  ChevronRight,
  ChevronsUpDown,
  Eye,
  Filter,
  FileText,
  Flame,
  LayoutDashboard,
  LayoutGrid,
  LayoutList,
  LogOut,
  Menu,
  PanelLeftClose,
  Phone,
  Plus,
  Search,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
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
} from 'react-router-dom'
import avatar from './assets/vendor/unnamed.png'
import {
  orgs,
} from './data/mockData.js'
import {
  fetchCases,
  fetchContacts,
  fetchCopilotSummary,
  createOrder,
  fetchCustomers,
  fetchDashboard,
  fetchGoals,
  fetchLeads,
  fetchOrders,
  fetchProducts,
  fetchTasks,
  extractOrderFromFile,
  generateFollowUp,
} from './api.js'
import { buildOrderPayloadFromCapture } from './captureUtils.js'
import { ORDER_FILTERS, filterOrders, getStockTone, pickLowStockProducts, summarizeOrders } from './orderUtils.js'
import { buildClientRecord, createDraftFromColumns } from './resourceUtils.js'

const STORAGE_KEY = 'huahenuancrm:selected-org'

const navItems = [
  { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard, title: 'Dashboard | 深大 AI CRM' },
  { path: '/copilot', label: 'AI 副驾', icon: Bot, title: 'AI Copilot | 深大 AI CRM' },
  { path: '/capture', label: '智能录单', icon: FileText, title: 'AI Capture | 深大 AI CRM' },
  { path: '/orders', label: '订单', icon: Activity, title: 'Orders | 深大 AI CRM' },
  { path: '/leads', label: '线索', icon: Target, title: 'Leads | 深大 AI CRM' },
  { path: '/contacts', label: '联系人', icon: Users, title: 'Contacts | 深大 AI CRM' },
  { path: '/accounts', label: '客户', icon: Building2, title: 'Accounts | 深大 AI CRM' },
  { path: '/opportunities', label: '商机', icon: Sparkles, title: 'Opportunities | 深大 AI CRM' },
  { path: '/goals', label: '销售目标', icon: Trophy, title: 'Sales Goals | 深大 AI CRM' },
  { path: '/cases', label: '工单', icon: Briefcase, title: 'Cases | 深大 AI CRM' },
  { path: '/tasks', label: '任务', icon: CheckSquare, title: 'Tasks | 深大 AI CRM' },
]

const pageItems = [...navItems, { path: '/profile', label: '个人主页', title: 'Profile | 深大 AI CRM' }]

const userProfile = {
  name: 'ZRC 673468472',
  email: 'zrc673468472@gmail.com',
  phone: '+86 186 0000 2048',
  position: 'CRM 运营管理员',
  department: '客户增长中心',
  location: '上海 · 浦东',
  joinDate: '2024 年 2 月 18 日',
}

const statusToneMap = {
  active: 'success',
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
}

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
  qualified: 'Qualified',
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  won: 'Won',
  lost: 'Lost',
}

const dashboardStageMeta = {
  new: { label: '新线索', tone: 'new' },
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
}

const orderStatusLabelMap = {
  draft: '草稿',
  confirmed: '已确认',
  fulfilled: '已履约',
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

function mapCustomerRecord(customer) {
  return {
    id: customer.id,
    name: customer.company,
    industry: customer.industry,
    owner: customer.contact_person,
    revenue: customer.annual_revenue,
    status: customer.status,
  }
}

function mapContactRecord(contact) {
  return {
    id: contact.id,
    name: contact.name,
    company: contact.company,
    role: contact.role,
    email: contact.email,
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
    current: goal.current,
    target: goal.target,
    progress: goal.progress,
    note: goal.note,
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
          setRecords(payload.map(mapper))
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

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/org" element={<OrgSelectionPage />} />
      <Route path="/" element={<Navigate replace to="/login" />} />
      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/copilot" element={<CopilotPage />} />
        <Route path="/capture" element={<CapturePage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/accounts" element={<AccountsPage />} />
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

function AccountsPage() {
  const { records, loading, error } = useRemoteRecords(fetchCustomers, mapCustomerRecord)

  return (
    <TableResourcePage
      title="客户"
      subtitle="企业档案、年度收入、客户负责人和状态概览。"
      icon={Building}
      records={records}
      loading={loading}
      error={error}
      createLabel="新建客户"
      columns={[
        { key: 'name', label: '客户名称' },
        { key: 'industry', label: '行业' },
        { key: 'owner', label: '负责人' },
        { key: 'revenue', label: '年度收入', format: 'currency' },
        { key: 'status', label: '状态', type: 'badge' },
      ]}
      tabs={[
        { key: 'all', label: '全部' },
        { key: 'active', label: '活跃', predicate: (item) => item.status === 'active' },
        { key: 'closed', label: '关闭', predicate: (item) => item.status === 'closed' },
      ]}
    />
  )
}

function ContactsPage() {
  const { records, loading, error } = useRemoteRecords(fetchContacts, mapContactRecord)

  return (
    <TableResourcePage
      title="联系人"
      subtitle="跟踪关键联系人、角色、所属公司和最近互动。"
      icon={Users}
      records={records}
      loading={loading}
      error={error}
      createLabel="新建联系人"
      columns={[
        { key: 'name', label: '姓名' },
        { key: 'company', label: '所属客户' },
        { key: 'role', label: '职位' },
        { key: 'email', label: '邮箱' },
        { key: 'status', label: '状态', type: 'badge' },
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
  const { records, loading, error } = useRemoteRecords(fetchLeads, mapLeadRecord)

  return (
    <BoardResourcePage
      title="线索"
      subtitle="在列表和看板之间切换，快速管理线索评级与跟进进度。"
      icon={Target}
      records={records}
      loading={loading}
      error={error}
      createLabel="新建线索"
      boardKey="stage"
      columns={[
        { key: 'name', label: '线索' },
        { key: 'company', label: '公司' },
        { key: 'owner', label: '负责人' },
        { key: 'nextStep', label: '下一步' },
        { key: 'rating', label: '评级', type: 'badge' },
      ]}
    />
  )
}

function OpportunitiesPage() {
  const { records, loading, error } = useRemoteRecords(fetchLeads, mapOpportunityRecord)

  return (
    <BoardResourcePage
      title="商机"
      subtitle="聚焦阶段、金额和预计成交时间，保持销售管道清晰。"
      icon={Sparkles}
      records={records}
      loading={loading}
      error={error}
      createLabel="新建商机"
      boardKey="stage"
      columns={[
        { key: 'name', label: '商机' },
        { key: 'account', label: '客户' },
        { key: 'owner', label: '负责人' },
        { key: 'amount', label: '金额', format: 'currency' },
        { key: 'closeDate', label: '预计成交' },
      ]}
    />
  )
}

function CasesPage() {
  const { records, loading, error } = useRemoteRecords(fetchCases, mapCaseRecord)

  return (
    <BoardResourcePage
      title="工单"
      subtitle="支持团队当前工作负载、优先级和处理 SLA 一览。"
      icon={Briefcase}
      records={records}
      loading={loading}
      error={error}
      createLabel="新建工单"
      boardKey="statusLabel"
      columns={[
        { key: 'title', label: '工单标题' },
        { key: 'account', label: '客户' },
        { key: 'owner', label: '负责人' },
        { key: 'priority', label: '优先级', type: 'badge' },
        { key: 'status', label: '状态', type: 'badge' },
      ]}
    />
  )
}

function LoginPage() {
  const navigate = useNavigate()
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    document.title = '登录 | 深大 AI CRM'
  }, [])

  return (
    <div className="crm-auth-page">
      <div className="crm-auth-orb crm-auth-orb--primary" />
      <div className="crm-auth-orb crm-auth-orb--secondary" />

      <main className="crm-auth-shell">
        <section className="crm-auth-showcase">
          <div className="crm-auth-brand">
            <div className="crm-brand-mark">深</div>
            <div>
              <strong>深大 AI CRM</strong>
              <span>销售、客户与任务协同平台</span>
            </div>
          </div>

          <div className="crm-auth-copy">
            <span className="crm-overline">欢迎回来</span>
            <h1>登录后继续处理你的客户流程</h1>
            
          </div>

          <div className="crm-auth-highlights">
            
           
          </div>
        </section>

        <section className="crm-auth-panel">
          <div className="crm-auth-panel-head">
            <span className="crm-overline">登录</span>
            <h2>进入你的工作台</h2>
            
          </div>

          <form
            className="crm-auth-form"
            onSubmit={(event) => {
              event.preventDefault()
              navigate('/org')
            }}
          >
            <label className="crm-auth-field">
              <span>账号</span>
              <input
                type="text"
                value={account}
                onChange={(event) => setAccount(event.target.value)}
                placeholder="请输入邮箱号或手机号"
                autoComplete="username"
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
              />
            </label>

            <button className="crm-primary-button crm-auth-submit" type="submit">
              登录
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

function RegisterPage() {
  const navigate = useNavigate()
  const [companyName, setCompanyName] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [agreed, setAgreed] = useState(true)

  useEffect(() => {
    document.title = '注册 | 深大 AI CRM'
  }, [])

  return (
    <div className="crm-auth-page">
      <div className="crm-auth-orb crm-auth-orb--primary" />
      <div className="crm-auth-orb crm-auth-orb--secondary" />

      <main className="crm-auth-shell crm-auth-shell--compact">
        <section className="crm-auth-panel">
          <div className="crm-auth-brand crm-auth-brand--panel">
            <div className="crm-brand-mark">深</div>
            <div>
              <strong>深大 AI CRM</strong>
              <span>管理员
                注册</span>
            </div>
          </div>

          <div className="crm-auth-panel-head">
            <span className="crm-overline"></span>
            <h2>创建你的工作空间</h2>
            
          </div>

          <form
            className="crm-auth-form"
            onSubmit={(event) => {
              event.preventDefault()
              if (!agreed) {
                return
              }
              navigate('/login')
            }}
          >
            <label className="crm-auth-field">
              <span>企业名称</span>
              <input
                type="text"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                placeholder="请输入企业或团队名称"
                autoComplete="organization"
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
              />
            </label>

            <label className="crm-auth-check">
              <input type="checkbox" checked={agreed} onChange={(event) => setAgreed(event.target.checked)} />
              <span>我已阅读并同意服务协议与隐私政策</span>
            </label>

            <button className="crm-primary-button crm-auth-submit" type="submit">
              创建账号
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

function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedOrg, setSelectedOrg] = useState(loadStoredOrg())
  const location = useLocation()
  const navigate = useNavigate()
  const currentPage = pageItems.find((item) => location.pathname.startsWith(item.path)) ?? navItems[0]
  const isProfilePage = location.pathname.startsWith('/profile')

  useEffect(() => {
    document.title = currentPage.title
  }, [currentPage.title])

  useEffect(() => {
    persistOrg(selectedOrg)
  }, [selectedOrg])

  return (
    <div className="crm-shell">
      <div className={`crm-sidebar-backdrop ${sidebarOpen ? 'is-visible' : ''}`} onClick={() => setSidebarOpen(false)} />
      <aside className={`crm-sidebar ${collapsed ? 'is-collapsed' : ''} ${sidebarOpen ? 'is-open' : ''}`}>
        <div className="crm-sidebar-inner">
          <div className="crm-sidebar-header">
            <button className="crm-brand" type="button" onClick={() => navigate('/org')}>
              <div className="crm-brand-mark">深</div>
              <div className="crm-brand-copy">
                <strong>{selectedOrg.name}</strong>
                <span>CRM 平台</span>
              </div>
            </button>
          </div>

          <div className="crm-sidebar-group">
            <div className="crm-sidebar-label">CRM</div>
            <nav className="crm-nav">
              {navItems.map(({ path, label, icon: Icon }) => (
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
              <img src={avatar} alt="用户头像" />
              <div>
                <strong>{userProfile.name}</strong>
                <span>{userProfile.email}</span>
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
              <span>{selectedOrg.name}</span>
              <h1>{currentPage.label}</h1>
            </div>
          </div>
          <div className="crm-topbar-actions">
            <button className="crm-icon-button" type="button" aria-label="通知">
              <Bell size={18} />
            </button>
            <button className="crm-ghost-button" type="button" onClick={() => navigate('/org')}>
              <LogOut size={16} />
              切换组织
            </button>
          </div>
        </header>

        <section className="crm-content">
          <Outlet context={{ selectedOrg, setSelectedOrg }} />
        </section>
      </main>
    </div>
  )
}

function OrgSelectionPage() {
  const navigate = useNavigate()

  useEffect(() => {
    document.title = '选择组织 | 深大 AI CRM'
  }, [])

  return (
    <div className="crm-org-page">
      <header className="crm-org-header">
        <div className="crm-org-brand">
          <div className="crm-brand-mark">深</div>
          <strong>深大 AI CRM</strong>
        </div>
        <button className="crm-ghost-button" type="button" onClick={() => navigate('/login')}>
          <LogOut size={16} />
          退出
        </button>
      </header>

      <main className="crm-org-main">
        <div className="crm-org-copy">
          <h1>选择一个组织</h1>
          <p>选择你想进入的组织。当前版本仅包含前端页面与简单逻辑，方便你继续开发。</p>
        </div>

        <div className="crm-org-list">
          {orgs.map((org) => (
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

        <button className="crm-dashed-button" type="button">
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
          <PanelHeader title="各阶段流程" actionLabel="全部流水线" />
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
          <PanelHeader title="热门线索" actionLabel="查看全部" />
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
          <PanelHeader title="我的任务" actionLabel="查看全部" />
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
          <PanelHeader title="我的商机" actionLabel="查看全部" />
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
          <PanelHeader title="目标进展" actionLabel="查看全部" />
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
        <PanelHeader title="近期活动" actionLabel="查看全部" />
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

function CopilotPage() {
  const [summary, setSummary] = useState(null)
  const [selectedId, setSelectedId] = useState('')
  const [followUp, setFollowUp] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generating, setGenerating] = useState(false)

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
      })
      .catch((requestError) => {
        if (mounted) {
          setError(requestError.message || 'AI 副驾接口请求失败')
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
    } catch (requestError) {
      setError(requestError.message || '生成跟进话术失败')
    } finally {
      setGenerating(false)
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
          <strong>{loading ? '正在从后端加载 AI 副驾建议...' : summary?.llm_summary ?? summary?.recommendation ?? '后端 Copilot 暂无建议。'}</strong>
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

      <section className="crm-copilot-grid">
        <div className="crm-panel">
          <PanelHeader title="商机智能评分" actionLabel="查看评分规则" />
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
                <p>{followUp?.message_draft ?? '点击下方按钮，后端将根据真实商机上下文调用 OpenAI 兼容接口生成话术；未配置密钥时返回规则兜底文案。'}</p>
                <button className="crm-primary-button" type="button" onClick={handleGenerateFollowUp} disabled={generating}>
                  <Bot size={16} />
                  {generating ? '生成中...' : followUp ? '重新生成话术' : '生成跟进话术'}
                </button>
                {followUp ? (
                  <small>{followUp.fallback_used ? '当前使用规则兜底，配置 SMART_CRM_LLM_API_KEY 后可启用真实 LLM。' : followUp.llm_summary}</small>
                ) : null}
              </div>
            </>
          ) : (
            <EmptyState icon={Bot} title="暂无 Copilot 建议" subtitle="接入真实商机数据后将自动生成。" />
          )}
        </div>
      </section>
    </div>
  )
}

function CapturePage() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [catalog, setCatalog] = useState({ customers: [], products: [] })
  const [submittedOrder, setSubmittedOrder] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

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

  const totalAmount = useMemo(() => {
    if (!result?.items?.length) {
      return 0
    }
    return result.items.reduce((total, item) => total + Number(item.quantity) * Number(item.unit_price), 0)
  }, [result])

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
        setResult(payload)
        setSubmittedOrder(null)
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
    setSubmitting(true)
    setError('')
    try {
      const payload = buildOrderPayloadFromCapture({
        captureResult: result,
        customers: catalog.customers,
        products: catalog.products,
        owner: userProfile.name,
        region: '华南',
      })
      const order = await createOrder(payload)
      setSubmittedOrder(order)
    } catch (nextError) {
      setError(nextError.message || '订单提交失败')
    } finally {
      setSubmitting(false)
    }
  }

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
                  <span>{result.customer_name}</span>
                </div>
                <StatusBadge value={formatPercent(result.confidence)} tone={result.confidence >= 0.8 ? 'success' : 'warning'} />
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
              <p>{result.summary}</p>
            </div>
          ) : (
            <EmptyState icon={UploadCloud} title="暂无草稿" subtitle="上传材料后会显示结构化订单草稿。" />
          )}
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
                  <th>数量</th>
                  <th>单价</th>
                  <th>小计</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((item) => (
                  <tr key={`${item.product_name}-${item.quantity}-${item.unit_price}`}>
                    <td>{item.product_name}</td>
                    <td>{item.quantity}</td>
                    <td>{formatCurrency(item.unit_price)}</td>
                    <td>{formatCurrency(item.quantity * item.unit_price)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>{result.suggested_notes}</p>
          <div className="crm-toolbar-actions">
            <button className="crm-primary-button" type="button" onClick={handleCreateOrder} disabled={submitting || Boolean(submittedOrder)}>
              <CheckSquare size={16} />
              {submittedOrder ? '已提交订单' : submitting ? '提交中' : '复核并提交订单'}
            </button>
            {submittedOrder ? <span className="crm-list-value">{formatCurrency(submittedOrder.total_amount)}</span> : null}
          </div>
          {result.raw_text_excerpt ? <small>{result.raw_text_excerpt}</small> : null}
        </section>
      ) : null}
    </div>
  )
}

function OrdersPage() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [products, setProducts] = useState([])
  const [activeTab, setActiveTab] = useState('all')
  const [selectedOrderId, setSelectedOrderId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    Promise.all([fetchOrders(), fetchProducts()])
      .then(([nextOrders, nextProducts]) => {
        if (mounted) {
          setOrders(nextOrders)
          setProducts(nextProducts)
          setSelectedOrderId(nextOrders[0]?.id ?? null)
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

  const summary = useMemo(() => summarizeOrders(orders), [orders])
  const visibleOrders = useMemo(() => filterOrders(orders, activeTab), [activeTab, orders])
  const selectedOrder = useMemo(() => {
    return visibleOrders.find((order) => order.id === selectedOrderId) ?? visibleOrders[0] ?? orders[0] ?? null
  }, [orders, selectedOrderId, visibleOrders])
  const lowStockProducts = useMemo(() => pickLowStockProducts(products), [products])
  const maxStock = useMemo(() => Math.max(1, ...products.map((product) => Number(product.stock ?? 0))), [products])

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
      <ResourceSyncState loading={loading} error={error} />

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
            <small>可从智能录单继续提交</small>
          </div>
        </article>
        <article className="crm-panel crm-metric-card">
          <div className="crm-metric-icon tone-qualified">
            <Shield size={18} />
          </div>
          <div>
            <span>低库存关注</span>
            <strong>{lowStockProducts.filter((product) => getStockTone(product) !== 'success').length}</strong>
            <small>按库存余量自动排序</small>
          </div>
        </article>
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="订单列表" />
          <small>{visibleOrders.length} 条订单，点击任意行查看明细。</small>
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
          <PanelHeader title="订单明细" />
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
              {selectedOrder.items.map((item) => (
                <div key={item.id} className="crm-list-item">
                  <div>
                    <strong>{item.product_name}</strong>
                    <span>{item.quantity} 件 x {formatCurrency(item.unit_price)}</span>
                  </div>
                  <div className="crm-list-value">{formatCurrency(item.line_total)}</div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={Activity} title="暂无订单明细" subtitle="后端订单数据同步后会显示在这里。" />
          )}
        </div>
      </section>

      <section className="crm-panel">
        <PanelHeader title="库存扣减追踪" />
        <div className="crm-stock-grid">
          {lowStockProducts.map((product) => {
            const tone = getStockTone(product)
            const stockWidth = Math.max(8, Math.round((Number(product.stock ?? 0) / maxStock) * 100))
            return (
              <article key={product.id} className="crm-stock-card">
                <div>
                  <strong>{product.name}</strong>
                  <span>{product.sku} · {product.category} · {formatCurrency(product.unit_price)}</span>
                </div>
                <StatusBadge value={`${product.stock} 件`} tone={tone} />
                <div className="crm-progress-track">
                  <div className={`crm-progress-bar tone-${tone}`} style={{ width: `${stockWidth}%` }} />
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}

function TableResourcePage({ title, subtitle, icon: Icon, records, columns, tabs, createLabel, loading = false, error = '' }) {
  const [rows, setRows] = useState(records)
  const [activeTab, setActiveTab] = useState(tabs[0].key)
  const [query, setQuery] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [draft, setDraft] = useState(() => createDraftFromColumns(columns))

  useEffect(() => {
    setRows(records)
  }, [records])

  const visibleRecords = useMemo(() => {
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

  const handleOpenCreate = () => {
    setDraft(createDraftFromColumns(columns))
    setCreateOpen(true)
  }

  const handleSubmitCreate = (event) => {
    event.preventDefault()
    const record = buildClientRecord({ draft, columns, existingCount: rows.length })
    setRows((currentRows) => [record, ...currentRows])
    setCreateOpen(false)
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
      />
      <ResourceSyncState loading={loading} error={error} />
      <ResourceToolbar query={query} onQueryChange={setQuery} columnCount={columns.length} />
      <div className="crm-panel">
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleRecords.map((record) => (
                <tr key={record.id}>
                  {columns.map((column) => (
                    <td key={column.key}>{renderCell(record[column.key], column)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {!loading && !error && !visibleRecords.length ? <EmptyState icon={Icon} title={`暂无${title}数据`} subtitle="后端演示数据同步后会显示在这里。" /> : null}
      <CreateRecordModal
        open={createOpen}
        title={createLabel}
        columns={columns}
        draft={draft}
        onDraftChange={setDraft}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleSubmitCreate}
      />
    </div>
  )
}

function BoardResourcePage({ title, subtitle, icon: Icon, records, columns, createLabel, boardKey, loading = false, error = '' }) {
  const [rows, setRows] = useState(records)
  const [view, setView] = useState('list')
  const [query, setQuery] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const boardValues = useMemo(() => [...new Set(rows.map((record) => record[boardKey]))], [boardKey, rows])
  const workflowField = useMemo(
    () => ({ key: boardKey, label: '阶段', value: boardValues[0] ?? 'New', options: boardValues.length ? boardValues : ['New'] }),
    [boardKey, boardValues],
  )
  const [draft, setDraft] = useState(() => createDraftFromColumns(columns, workflowField))

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
    }, {})
  }, [boardKey, visibleRecords])

  const handleOpenCreate = () => {
    setDraft(createDraftFromColumns(columns, workflowField))
    setCreateOpen(true)
  }

  const handleSubmitCreate = (event) => {
    event.preventDefault()
    const record = buildClientRecord({ draft, columns, existingCount: rows.length, workflowField })
    setRows((currentRows) => [record, ...currentRows])
    setCreateOpen(false)
    setView('list')
  }

  return (
    <div className="crm-page-stack">
      <ResourceHeader title={title} subtitle={subtitle} icon={Icon} createLabel={createLabel} onCreate={handleOpenCreate} />
      <ResourceSyncState loading={loading} error={error} />
      <ResourceToolbar query={query} onQueryChange={setQuery} columnCount={columns.length}>
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
                </tr>
              </thead>
              <tbody>
                {visibleRecords.map((record) => (
                  <tr key={record.id}>
                    {columns.map((column) => (
                      <td key={column.key}>{renderCell(record[column.key], column)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="crm-board-grid">
          {Object.entries(groups).map(([group, items]) => (
            <section key={group} className="crm-board-column">
              <div className="crm-board-head">
                <div>
                  <strong>{group}</strong>
                  <span>{items.length} 条</span>
                </div>
                <StatusBadge value={items.length} tone={boardToneMap[group] ?? 'neutral'} isNumeric />
              </div>
              <div className="crm-board-list">
                {items.map((item) => (
                  <article key={item.id} className="crm-board-card">
                    <strong>{item.name ?? item.title}</strong>
                    <p>{item.company ?? item.account ?? item.owner}</p>
                    {'amount' in item ? <span>{formatCurrency(item.amount)}</span> : null}
                    {'nextStep' in item ? <span>{item.nextStep}</span> : null}
                    {'priority' in item ? <StatusBadge value={item.priority} tone={statusToneMap[item.priority] ?? 'neutral'} /> : null}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
      {!loading && !error && !visibleRecords.length ? <EmptyState icon={Icon} title={`暂无${title}数据`} subtitle="后端演示数据同步后会显示在这里。" /> : null}
      <CreateRecordModal
        open={createOpen}
        title={createLabel}
        columns={columns}
        workflowField={workflowField}
        draft={draft}
        onDraftChange={setDraft}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleSubmitCreate}
      />
    </div>
  )
}

function TasksPage() {
  const { records: tasks, loading, error } = useRemoteRecords(fetchTasks, mapTaskRecord)
  const tabs = [
    { key: 'all', label: '全部' },
    { key: 'overdue', label: '逾期', predicate: (item) => item.status === 'overdue' },
    { key: 'today', label: '今天', predicate: (item) => item.status === 'today' },
    { key: 'week', label: '本周', predicate: (item) => item.status === 'week' },
  ]

  const [activeTab, setActiveTab] = useState('all')
  const visibleTasks = tabs.find((tab) => tab.key === activeTab)?.predicate
    ? tasks.filter(tabs.find((tab) => tab.key === activeTab).predicate)
    : tasks

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
      />
      <ResourceSyncState loading={loading} error={error} />

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
          </article>
        ))}
      </section>
      {!loading && !error && !visibleTasks.length ? <EmptyState icon={CheckSquare} title="暂无任务" subtitle="后端任务数据同步后会显示在这里。" /> : null}
    </div>
  )
}

function GoalsPage() {
  const { records: goals, loading, error } = useRemoteRecords(fetchGoals, mapGoalRecord)

  return (
    <div className="crm-page-stack">
      <ResourceHeader title="销售目标" subtitle="季度目标、完成进度和预测结果一屏查看。" icon={Trophy} createLabel="新建目标" />
      <ResourceSyncState loading={loading} error={error} />

      <section className="crm-goal-grid">
        {goals.map((goal) => (
          <article key={goal.id} className="crm-panel crm-goal-card">
            <div className="crm-goal-card-head">
              <div>
                <strong>{goal.name}</strong>
                <span>{goal.period}</span>
              </div>
              <StatusBadge value={`${goal.progress}%`} tone={goal.progress >= 80 ? 'success' : 'warning'} />
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
    </div>
  )
}

function ProfilePage() {
  const navigate = useNavigate()
  const { selectedOrg } = useOutletContext()

  const profileInfo = [
    { label: '邮箱', value: userProfile.email },
    { label: '手机号', value: userProfile.phone },
    { label: '岗位', value: userProfile.position },
    { label: '部门', value: userProfile.department },
    { label: '办公地点', value: userProfile.location },
    { label: '加入时间', value: userProfile.joinDate },
  ]

  const securityInfo = [
    { label: '登录方式', value: '账号密码', tone: 'neutral' },
    { label: '账户状态', value: '正常', tone: 'success' },
    { label: '组织权限', value: '管理员', tone: 'accent' },
  ]

  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel crm-profile-hero">
        <div className="crm-profile-hero-main">
          <img className="crm-profile-avatar" src={avatar} alt="用户头像" />
          <div className="crm-profile-copy">
            <span className="crm-overline">个人主页</span>
            <h2>{userProfile.name}</h2>
            <div className="crm-profile-meta">
              <span>{userProfile.position}</span>
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
          <button className="crm-ghost-button crm-ghost-button--danger" type="button" onClick={() => navigate('/login')}>
            <LogOut size={16} />
            退出登录
          </button>
        </div>
      </section>

      <section className="crm-three-col-grid crm-profile-cards">
        <article className="crm-panel crm-profile-card">
          <PanelHeader title="基础信息" />
          <div className="crm-profile-info-list">
            {profileInfo.map((item) => (
              <div key={item.label} className="crm-profile-info-item">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="crm-panel crm-profile-card">
          <PanelHeader title="账号安全" />
          <div className="crm-profile-info-list">
            {securityInfo.map((item) => (
              <div key={item.label} className="crm-profile-info-item">
                <span>{item.label}</span>
                <StatusBadge value={item.value} tone={item.tone} />
              </div>
            ))}
          </div>
        </article>

        <article className="crm-panel crm-profile-card">
          <PanelHeader title="当前组织" />
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
              <span>工作区状态</span>
              <StatusBadge value="已连接" tone="success" />
            </div>
          </div>
        </article>
      </section>
    </div>
  )
}

function ResourceHeader({ title, subtitle, icon: Icon, createLabel, tabs = [], activeTab, onTabChange, onCreate }) {
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
        <button className="crm-ghost-button" type="button">
          <Filter size={16} />
          过滤器
        </button>
        <button className="crm-ghost-button" type="button">
          <Eye size={16} />
          列
        </button>
        <button className="crm-primary-button" type="button" onClick={onCreate}>
          <Plus size={16} />
          {createLabel}
        </button>
      </div>
    </section>
  )
}

function CreateRecordModal({ open, title, columns, workflowField, draft, onDraftChange, onClose, onSubmit }) {
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
            <span className="crm-overline">快速创建</span>
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
                    {option}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {columns.map((column) => (
            <label key={column.key} className="crm-field">
              <span>{column.label}</span>
              <input
                type={column.format === 'currency' ? 'number' : 'text'}
                min={column.format === 'currency' ? '0' : undefined}
                step={column.format === 'currency' ? '1000' : undefined}
                value={draft[column.key] ?? ''}
                onChange={(event) => handleChange(column.key, event.target.value)}
                required
              />
            </label>
          ))}
        </div>

        <div className="crm-modal-actions">
          <button className="crm-ghost-button" type="button" onClick={onClose}>
            取消
          </button>
          <button className="crm-primary-button" type="submit">
            保存
          </button>
        </div>
      </form>
    </div>
  )
}

function ResourceToolbar({ query, onQueryChange, columnCount, children }) {
  return (
    <section className="crm-toolbar-card">
      <label className="crm-search-box">
        <Search size={16} />
        <input placeholder="搜索姓名、公司、负责人或备注" value={query} onChange={(event) => onQueryChange(event.target.value)} />
      </label>
      <div className="crm-toolbar-right">
        {children}
        <div className="crm-column-badge">{columnCount} 列</div>
      </div>
    </section>
  )
}

function PanelHeader({ title, actionLabel }) {
  return (
    <div className="crm-panel-header">
      <strong>{title}</strong>
      {actionLabel ? (
        <button className="crm-link-button" type="button">
          {actionLabel}
          <ArrowRight size={14} />
        </button>
      ) : null}
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

function loadStoredOrg() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return orgs[0]
    }
    return JSON.parse(raw)
  } catch {
    return orgs[0]
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
