import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Avatar, Badge, Dropdown, Layout, Menu, Tag, Tooltip, theme } from 'antd'
import {
  AppstoreOutlined,
  AuditOutlined,
  BarChartOutlined,
  BellOutlined,
  ContactsOutlined,
  DashboardOutlined,
  FundProjectionScreenOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RobotOutlined,
  ShoppingOutlined,
  SolutionOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useAuth, hasPermission } from '../auth/AuthContext.jsx'
import { fetchNotifications } from '../api.js'
import { BRAND } from '../theme.js'
import logo from '../assets/smart-crm-logo.png'

const { Header, Sider, Content } = Layout

const MENU = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台', perm: 'dashboard:read' },
  { key: '/customers', icon: <SolutionOutlined />, label: '客户', perm: 'crm:read' },
  { key: '/contacts', icon: <ContactsOutlined />, label: '联系人', perm: 'crm:read' },
  { key: '/leads', icon: <FundProjectionScreenOutlined />, label: '商机', perm: 'crm:read' },
  { key: '/products', icon: <AppstoreOutlined />, label: '产品', perm: 'catalog:manage' },
  { key: '/orders', icon: <ShoppingOutlined />, label: '订单', perm: 'order:manage' },
  { key: '/copilot', icon: <RobotOutlined />, label: 'AI 助手', perm: 'ai:use', highlight: true },
  { key: '/capture', icon: <ThunderboltOutlined />, label: '智能录单', perm: 'ai:use', highlight: true },
  { key: '/reports', icon: <BarChartOutlined />, label: '报表分析', perm: 'reports:read' },
  { key: '/team', icon: <TeamOutlined />, label: '团队成员', perm: 'team:manage' },
  { key: '/audit', icon: <AuditOutlined />, label: '审计日志', perm: 'audit:read' },
]

export default function AppLayout() {
  const { user, permissions, logout, organizations } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [unread, setUnread] = useState(0)
  const { token } = theme.useToken()

  useEffect(() => {
    let active = true
    fetchNotifications({ status: 'unread' })
      .then((data) => {
        if (!active) return
        const list = Array.isArray(data) ? data : data?.items ?? []
        setUnread(list.length)
      })
      .catch(() => active && setUnread(0))
    return () => {
      active = false
    }
  }, [location.pathname])

  const items = MENU.filter((m) => hasPermission(permissions, m.perm)).map((m) => ({
    key: m.key,
    icon: m.icon,
    label: (
      <Link to={m.key}>
        {m.label}
        {m.highlight ? (
          <Tag color={BRAND.primary} style={{ marginInlineStart: 8, transform: 'scale(.82)' }}>
            AI
          </Tag>
        ) : null}
      </Link>
    ),
  }))

  const org = organizations?.[0]
  const selectedKey = '/' + (location.pathname.split('/')[1] || 'dashboard')

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="light"
        collapsible
        collapsed={collapsed}
        trigger={null}
        width={220}
        style={{ borderInlineEnd: '1px solid #EEF1F6', position: 'sticky', top: 0, height: '100vh' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, height: 56, padding: collapsed ? '0 18px' : '0 18px' }}>
          <img src={logo} alt="logo" width={30} height={30} />
          {!collapsed && (
            <div style={{ lineHeight: 1.1 }}>
              <div style={{ fontWeight: 700, fontSize: 16, color: '#1F2A44' }}>{BRAND.name}</div>
              <div style={{ fontSize: 11, color: '#9AA6BC' }}>{BRAND.tagline}</div>
            </div>
          )}
        </div>
        <Menu mode="inline" selectedKeys={[selectedKey]} items={items} style={{ borderInlineEnd: 0, marginTop: 8 }} />
      </Sider>

      <Layout>
        <Header
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            borderBottom: '1px solid #EEF1F6',
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}
        >
          <div
            onClick={() => setCollapsed((c) => !c)}
            style={{ cursor: 'pointer', fontSize: 18, color: '#5B6B86', marginInlineEnd: 16 }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
          <Tag bordered={false} color="processing">
            {org?.name ?? user?.organization_name ?? '深大 AI CRM 课程组'}
          </Tag>
          <div style={{ flex: 1 }} />
          <Tooltip title="通知中心">
            <Badge count={unread} size="small" offset={[-2, 4]}>
              <BellOutlined
                style={{ fontSize: 18, color: '#5B6B86', cursor: 'pointer' }}
                onClick={() => navigate('/dashboard')}
              />
            </Badge>
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                { key: 'role', label: `角色：${user?.role ?? '-'}`, disabled: true },
                { key: 'scope', label: `数据范围：${user?.data_scope === 'all' ? '全部数据' : '本人数据'}`, disabled: true },
                { type: 'divider' },
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' },
              ],
              onClick: async ({ key }) => {
                if (key === 'logout') {
                  await logout()
                  navigate('/login')
                }
              },
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginInlineStart: 20 }}>
              <Avatar size={32} style={{ background: token.colorPrimary }} icon={<UserOutlined />} />
              <div style={{ lineHeight: 1.2 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#1F2A44' }}>{user?.full_name ?? '用户'}</div>
                <div style={{ fontSize: 11, color: '#9AA6BC' }}>{user?.department ?? ''}</div>
              </div>
            </div>
          </Dropdown>
        </Header>

        <Content style={{ margin: 20 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
