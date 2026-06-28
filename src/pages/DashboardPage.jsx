import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App as AntApp, Card, Col, Row, Spin, Statistic, Table, Tag, Typography, Progress } from 'antd'
import { RobotOutlined, RiseOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { fetchDashboard, fetchCopilotSummary } from '../api.js'
import { BarChart, DonutChart } from '../components/Charts.jsx'
import PageHeader from '../components/PageHeader.jsx'
import { LEAD_STAGES, labelOf, colorOf, formatCurrency } from '../constants.js'
import { BRAND } from '../theme.js'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { message } = AntApp.useApp()
  const [data, setData] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    fetchDashboard()
      .then((d) => active && setData(d))
      .catch((e) => active && message.error(e.message || '加载工作台失败'))
      .finally(() => active && setLoading(false))
    fetchCopilotSummary()
      .then((s) => active && setSummary(s))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [message])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    )
  }
  if (!data) return null

  const trend = (data.revenue_trend ?? []).map((d) => ({ label: d.month?.slice(5) ?? d.month, value: d.revenue }))
  const stages = (data.stage_distribution ?? []).map((d) => ({ label: labelOf(LEAD_STAGES, d.stage), value: d.count }))

  const leadColumns = [
    { title: '商机', dataIndex: 'title', render: (t, r) => (
      <a onClick={() => navigate('/leads')}>{t}{r.ai_assisted ? <Tag color={BRAND.primary} style={{ marginInlineStart: 6 }}>AI</Tag> : null}</a>
    ) },
    { title: '客户', dataIndex: 'customer_name' },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    { title: '阶段', dataIndex: 'stage', width: 100, render: (s) => <Tag color={colorOf(LEAD_STAGES, s)}>{labelOf(LEAD_STAGES, s)}</Tag> },
    { title: '预计金额', dataIndex: 'expected_amount', align: 'right', render: (v) => formatCurrency(v) },
    { title: '下一步', dataIndex: 'next_action', ellipsis: true },
    { title: '截止', dataIndex: 'due_date', width: 110 },
  ]

  return (
    <div>
      <PageHeader title="工作台" subtitle="销售经营全景与 AI 洞察" />

      <Row gutter={[16, 16]}>
        {(data.metrics ?? []).map((m, i) => (
          <Col xs={12} md={6} key={m.label}>
            <Card bordered={false} style={{ height: '100%' }}>
              <Statistic
                title={m.label}
                value={m.value}
                valueStyle={{ color: i === 1 ? BRAND.primary : '#1F2A44', fontWeight: 700 }}
              />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>{m.hint}</Typography.Text>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card bordered={false} title={<><RiseOutlined style={{ color: BRAND.primary }} /> 销售额趋势</>}>
            <BarChart data={trend} valueFormatter={(v) => formatCurrency(v)} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card bordered={false} title="商机阶段分布">
            <DonutChart data={stages} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card bordered={false} title={<><ThunderboltOutlined style={{ color: '#F7A23B' }} /> 紧急跟进商机</>}>
            <Table
              size="small"
              rowKey="id"
              columns={leadColumns}
              dataSource={data.urgent_leads ?? []}
              pagination={false}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            bordered={false}
            title={<><RobotOutlined style={{ color: BRAND.primary }} /> AI 销售 Copilot 摘要</>}
            extra={<a onClick={() => navigate('/copilot')}>进入助手</a>}
          >
            {summary ? (
              <div>
                <Row gutter={12}>
                  <Col span={12}>
                    <Statistic title="预测成交额" value={formatCurrency(summary.forecast_amount)} valueStyle={{ fontSize: 18, color: BRAND.primary }} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="风险商机" value={summary.at_risk_count} suffix="个" valueStyle={{ fontSize: 18, color: '#F76C6C' }} />
                  </Col>
                </Row>
                {summary.top_opportunity ? (
                  <div style={{ marginTop: 14, background: '#F5F8FF', borderRadius: 10, padding: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography.Text strong>{summary.top_opportunity.title}</Typography.Text>
                      <Tag color="blue">评分 {summary.top_opportunity.rule_score} · {summary.top_opportunity.grade} 级</Tag>
                    </div>
                    <Progress
                      percent={Math.round((summary.top_opportunity.win_rate ?? 0) * 100)}
                      size="small"
                      strokeColor={BRAND.primary}
                      style={{ marginTop: 6 }}
                    />
                    <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 6, marginBottom: 0 }} ellipsis={{ rows: 3 }}>
                      {summary.top_opportunity.next_best_action}
                    </Typography.Paragraph>
                  </div>
                ) : null}
                <Typography.Paragraph style={{ fontSize: 13, marginTop: 12, marginBottom: 0 }} ellipsis={{ rows: 4, expandable: true, symbol: '展开' }}>
                  {summary.recommendation}
                </Typography.Paragraph>
              </div>
            ) : (
              <Typography.Text type="secondary">AI 摘要生成中…</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
