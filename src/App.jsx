import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  ArrowRight,
  Bell,
  Briefcase,
  Building2,
  Calendar,
  CheckSquare,
  ChevronRight,
  ChevronsUpDown,
  Eye,
  Filter,
  Flame,
  LayoutDashboard,
  LayoutGrid,
  LayoutList,
  LogOut,
  Menu,
  PanelLeftClose,
  Percent,
  Phone,
  Plus,
  Search,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  Users,
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
} from 'react-router-dom'
import avatar from './assets/vendor/unnamed.png'
import {
  accounts,
  activities,
  contacts,
  dashboardMetrics,
  dashboardStages,
  focusItems,
  goals,
  hotLeads,
  leads,
  opportunities,
  orgs,
  pipelineCards,
  supportCases,
  taskCards,
  taskItems,
} from './data/mockData.js'

const STORAGE_KEY = 'bottlecrm:selected-org'

const navItems = [
  { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard, title: 'Dashboard | BottleCRM' },
  { path: '/leads', label: '线索', icon: Target, title: 'Leads | BottleCRM' },
  { path: '/contacts', label: '联系人', icon: Users, title: 'Contacts | BottleCRM' },
  { path: '/accounts', label: '客户', icon: Building2, title: 'Accounts | BottleCRM' },
  { path: '/opportunities', label: '商机', icon: Sparkles, title: 'Opportunities | BottleCRM' },
  { path: '/goals', label: '销售目标', icon: Trophy, title: 'Sales Goals | BottleCRM' },
  { path: '/cases', label: '工单', icon: Briefcase, title: 'Cases | BottleCRM' },
  { path: '/tasks', label: '任务', icon: CheckSquare, title: 'Tasks | BottleCRM' },
]

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
        <Route
          path="/accounts"
          element={
            <TableResourcePage
              title="客户"
              subtitle="企业档案、年度收入、客户负责人和状态概览。"
              icon={Building}
              records={accounts}
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
          }
        />
        <Route
          path="/contacts"
          element={
            <TableResourcePage
              title="联系人"
              subtitle="跟踪关键联系人、角色、所属公司和最近互动。"
              icon={Users}
              records={contacts}
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
          }
        />
        <Route
          path="/leads"
          element={
            <BoardResourcePage
              title="线索"
              subtitle="在列表和看板之间切换，快速管理线索评级与跟进进度。"
              icon={Target}
              records={leads}
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
          }
        />
        <Route
          path="/opportunities"
          element={
            <BoardResourcePage
              title="商机"
              subtitle="聚焦阶段、金额和预计成交时间，保持销售管道清晰。"
              icon={Sparkles}
              records={opportunities}
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
          }
        />
        <Route
          path="/cases"
          element={
            <BoardResourcePage
              title="工单"
              subtitle="支持团队当前工作负载、优先级和处理 SLA 一览。"
              icon={Briefcase}
              records={supportCases}
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
          }
        />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/goals" element={<GoalsPage />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/login" />} />
    </Routes>
  )
}

function LoginPage() {
  const navigate = useNavigate()
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    document.title = '登录 | BottleCRM'
  }, [])

  return (
    <div className="crm-auth-page">
      <div className="crm-auth-orb crm-auth-orb--primary" />
      <div className="crm-auth-orb crm-auth-orb--secondary" />

      <main className="crm-auth-shell">
        <section className="crm-auth-showcase">
          <div className="crm-auth-brand">
            <div className="crm-brand-mark">瓶</div>
            <div>
              <strong>瓶子 CRM</strong>
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
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    document.title = '注册 | BottleCRM'
  }, [])

  return (
    <div className="crm-auth-page">
      <div className="crm-auth-orb crm-auth-orb--primary" />
      <div className="crm-auth-orb crm-auth-orb--secondary" />

      <main className="crm-auth-shell crm-auth-shell--reverse">
        <section className="crm-auth-panel">
          <div className="crm-auth-panel-head">
            <span className="crm-overline">注册</span>
            <h2>创建一个新的前端演示账号</h2>
            <p>当前仅为前端页面演示，提交后将直接跳回登录页。</p>
          </div>

          <form
            className="crm-auth-form"
            onSubmit={(event) => {
              event.preventDefault()
              navigate('/login')
            }}
          >
            <label className="crm-auth-field">
              <span>账号</span>
              <input
                type="text"
                value={account}
                onChange={(event) => setAccount(event.target.value)}
                placeholder="邮箱号或手机号"
                autoComplete="username"
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

            <button className="crm-primary-button crm-auth-submit" type="submit">
              注册并返回登录
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

        <section className="crm-auth-showcase">
          <div className="crm-auth-brand">
            <div className="crm-brand-mark">瓶</div>
            <div>
              <strong>瓶子 CRM</strong>
              <span>延续当前项目的深色玻璃拟态风格</span>
            </div>
          </div>

          <div className="crm-auth-copy">
            <span className="crm-overline">快速开始</span>
            <h1>用一个账号连接销售漏斗与客户协作</h1>
            <p>注册页仅保留账号和密码字段，满足当前前端演示和路由联调需求。</p>
          </div>

          <div className="crm-auth-stats">
            <article className="crm-auth-stat-card">
              <strong>8+</strong>
              <span>业务页面已接入</span>
            </article>
            <article className="crm-auth-stat-card">
              <strong>100%</strong>
              <span>前端内链跳转</span>
            </article>
            <article className="crm-auth-stat-card">
              <strong>2步</strong>
              <span>注册后回到登录</span>
            </article>
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
  const currentPage = navItems.find((item) => location.pathname.startsWith(item.path)) ?? navItems[0]

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
              <div className="crm-brand-mark">瓶</div>
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
            <button className="crm-user-card" type="button" onClick={() => navigate('/org')}>
              <img src={avatar} alt="用户头像" />
              <div>
                <strong>ZRC 673468472</strong>
                <span>zrc673468472@gmail.com</span>
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
    document.title = '选择组织 | BottleCRM'
  }, [])

  return (
    <div className="crm-org-page">
      <header className="crm-org-header">
        <div className="crm-org-brand">
          <div className="crm-brand-mark">瓶</div>
          <strong>瓶子 CRM</strong>
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
  return (
    <div className="crm-page-stack">
      <section className="crm-hero-panel">
        <div>
          <span className="crm-overline">下午好</span>
          <h2>仪表盘</h2>
          <p>以下是你今天的 CRM 概况，聚焦重点任务、跟进和销售管道。</p>
        </div>
      </section>

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
        {pipelineCards.map((stage) => (
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
              <strong>{metric.format === 'percent' ? `${metric.value}%` : formatCurrency(metric.value)}</strong>
              <small>{metric.note}</small>
            </div>
          </article>
        ))}
      </section>

      <section className="crm-dashboard-grid">
        <div className="crm-panel">
          <PanelHeader title="各阶段流程" actionLabel="全部流水线" />
          <div className="crm-progress-list">
            {dashboardStages.map((stage) => (
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
            {taskCards.map((task) => (
              <article key={task.id} className="crm-list-item">
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.owner}</span>
                </div>
                <StatusBadge value={task.dueLabel} tone={statusToneMap[task.tone]} />
              </article>
            ))}
          </div>
        </div>

        <div className="crm-panel">
          <PanelHeader title="我的商机" actionLabel="查看全部" />
          <div className="crm-list compact">
            {opportunities.slice(0, 3).map((item) => (
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
            {goals.map((goal) => (
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
      </section>
    </div>
  )
}

function TableResourcePage({ title, subtitle, icon: Icon, records, columns, tabs, createLabel }) {
  const [activeTab, setActiveTab] = useState(tabs[0].key)
  const [query, setQuery] = useState('')

  const visibleRecords = useMemo(() => {
    const tab = tabs.find((item) => item.key === activeTab)
    return records.filter((record) => {
      const matchesTab = tab?.predicate ? tab.predicate(record) : true
      if (!matchesTab) {
        return false
      }
      if (!query.trim()) {
        return true
      }
      return Object.values(record).some((value) => String(value).toLowerCase().includes(query.toLowerCase()))
    })
  }, [activeTab, query, records, tabs])

  return (
    <div className="crm-page-stack">
      <ResourceHeader title={title} subtitle={subtitle} icon={Icon} createLabel={createLabel} tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
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
    </div>
  )
}

function BoardResourcePage({ title, subtitle, icon: Icon, records, columns, createLabel, boardKey }) {
  const [view, setView] = useState('list')
  const [query, setQuery] = useState('')

  const visibleRecords = useMemo(() => {
    if (!query.trim()) {
      return records
    }
    return records.filter((record) => Object.values(record).some((value) => String(value).toLowerCase().includes(query.toLowerCase())))
  }, [query, records])

  const groups = useMemo(() => {
    return visibleRecords.reduce((accumulator, record) => {
      const key = record[boardKey]
      accumulator[key] = accumulator[key] ? [...accumulator[key], record] : [record]
      return accumulator
    }, {})
  }, [boardKey, visibleRecords])

  return (
    <div className="crm-page-stack">
      <ResourceHeader title={title} subtitle={subtitle} icon={Icon} createLabel={createLabel} />
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
    </div>
  )
}

function TasksPage() {
  const tabs = [
    { key: 'all', label: '全部' },
    { key: 'overdue', label: '逾期', predicate: (item) => item.status === 'overdue' },
    { key: 'today', label: '今天', predicate: (item) => item.status === 'today' },
    { key: 'week', label: '本周', predicate: (item) => item.status === 'week' },
  ]

  const [activeTab, setActiveTab] = useState('all')
  const visibleTasks = tabs.find((tab) => tab.key === activeTab)?.predicate
    ? taskItems.filter(tabs.find((tab) => tab.key === activeTab).predicate)
    : taskItems

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
    </div>
  )
}

function GoalsPage() {
  return (
    <div className="crm-page-stack">
      <ResourceHeader title="销售目标" subtitle="季度目标、完成进度和预测结果一屏查看。" icon={Trophy} createLabel="新建目标" />

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
    </div>
  )
}

function ResourceHeader({ title, subtitle, icon: Icon, createLabel, tabs = [], activeTab, onTabChange }) {
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
        <button className="crm-primary-button" type="button">
          <Plus size={16} />
          {createLabel}
        </button>
      </div>
    </section>
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
    currency: 'USD',
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
