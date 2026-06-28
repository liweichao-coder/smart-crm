import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App as AntApp, Button, Card, Form, Input, Typography } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useAuth } from '../auth/AuthContext.jsx'
import { BRAND } from '../theme.js'
import logo from '../assets/smart-crm-logo.png'

const DEMO_ACCOUNTS = [
  { account: 'demo@smart-crm.local', label: '管理员 · 李伟超' },
  { account: 'manager@smart-crm.local', label: '销售经理 · 王蕾' },
  { account: 'sales@smart-crm.local', label: '销售 · 赵可' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const { message } = AntApp.useApp()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const onFinish = async (values) => {
    setLoading(true)
    try {
      await login(values.account, values.password)
      message.success('登录成功')
      navigate('/dashboard')
    } catch (err) {
      message.error(err.message || '登录失败，请检查账号或密码')
    } finally {
      setLoading(false)
    }
  }

  const quickFill = (account) => {
    form.setFieldsValue({ account, password: 'SmartCRM@2026' })
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex' }}>
      {/* 品牌侧 */}
      <div
        style={{
          flex: 1.1,
          background: `linear-gradient(135deg, ${BRAND.primary} 0%, #1B3BB0 100%)`,
          color: '#fff',
          padding: '64px 56px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
        className="login-brand-side"
      >
        {/* 居中大 Logo 作为视觉中心 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
          <span
            style={{
              display: 'inline-flex',
              padding: 22,
              background: '#fff',
              borderRadius: 28,
              boxShadow: '0 16px 48px rgba(0,0,0,0.22)',
            }}
          >
            <img src={logo} alt="logo" width={120} height={120} />
          </span>
          <h1 style={{ color: '#fff', fontSize: 34, fontWeight: 800, margin: '28px 0 0' }}>{BRAND.name}</h1>
          <p style={{ fontSize: 16, opacity: 0.92, marginTop: 12, maxWidth: 380 }}>
            AI 驱动的智能销售管理平台，内置销售 Copilot、智能录单、商机评分与自动周报。
          </p>
          <div style={{ display: 'flex', gap: 28, marginTop: 32 }}>
            {[
              ['Copilot', '对话式洞察'],
              ['智能录单', '一键成单'],
              ['商机评分', '优先级排序'],
            ].map(([t, d]) => (
              <div key={t}>
                <div style={{ fontSize: 18, fontWeight: 700 }}>{t}</div>
                <div style={{ fontSize: 13, opacity: 0.85 }}>{d}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ fontSize: 13, opacity: 0.7, textAlign: 'center' }}>深大 AI CRM 课程组 · 软件工程实训项目</div>
      </div>

      {/* 表单侧 */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F4F6FB' }}>
        <Card style={{ width: 380, boxShadow: '0 12px 40px rgba(31,42,68,0.08)' }} bordered={false}>
          <Typography.Title level={3} style={{ marginTop: 0 }}>
            欢迎回来
          </Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginTop: -8 }}>
            登录 {BRAND.name} 控制台
          </Typography.Paragraph>
          <Form form={form} layout="vertical" onFinish={onFinish} requiredMark={false} initialValues={{ password: '' }}>
            <Form.Item name="account" label="账号" rules={[{ required: true, message: '请输入账号 / 邮箱' }]}>
              <Input size="large" prefix={<UserOutlined />} placeholder="邮箱或用户名" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password size="large" prefix={<LockOutlined />} placeholder="密码" onPressEnter={() => form.submit()} />
            </Form.Item>
            <Button type="primary" size="large" block htmlType="submit" loading={loading}>
              登录
            </Button>
          </Form>
          <div style={{ marginTop: 18, fontSize: 12, color: '#8694AD' }}>演示账号（密码统一 SmartCRM@2026）：</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {DEMO_ACCOUNTS.map((a) => (
              <Button key={a.account} size="small" onClick={() => quickFill(a.account)}>
                {a.label}
              </Button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
