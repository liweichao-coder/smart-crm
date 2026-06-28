import { useEffect, useState } from 'react'
import { App as AntApp, Card, Col, Row, Spin, Statistic, Table, Tag, Typography } from 'antd'
import { fetchSalesPerformanceReport } from '../api.js'
import PageHeader from '../components/PageHeader.jsx'
import { BarChart } from '../components/Charts.jsx'
import { formatCurrency } from '../constants.js'
import { BRAND } from '../theme.js'

export default function ReportsPage() {
  const { message } = AntApp.useApp()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    fetchSalesPerformanceReport({})
      .then((d) => active && setData(d))
      .catch((e) => active && message.error(e.message || '加载报表失败'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [message])

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  if (!data) return null

  const trend = (data.revenue_trend ?? []).map((d) => ({ label: d.month?.slice(5) ?? d.month, value: d.revenue }))

  const ownerColumns = [
    { title: '销售', dataIndex: 'name', render: (v) => <strong>{v}</strong> },
    { title: '订单收入', dataIndex: 'revenue', align: 'right', render: (v) => formatCurrency(v) },
    { title: '订单数', dataIndex: 'order_count', align: 'right', width: 90 },
    { title: 'AI 订单', dataIndex: 'ai_order_count', align: 'right', width: 90, render: (v) => <Tag color={BRAND.primary}>{v}</Tag> },
    { title: '客单价', dataIndex: 'average_order_value', align: 'right', render: (v) => formatCurrency(v) },
    { title: '管道金额', dataIndex: 'pipeline_amount', align: 'right', render: (v) => formatCurrency(v) },
  ]

  const regionColumns = [
    { title: '区域', dataIndex: 'name', render: (v) => <strong>{v}</strong> },
    { title: '订单收入', dataIndex: 'revenue', align: 'right', render: (v) => formatCurrency(v) },
    { title: '订单数', dataIndex: 'order_count', align: 'right', width: 90 },
    { title: '管道金额', dataIndex: 'pipeline_amount', align: 'right', render: (v) => formatCurrency(v) },
  ]

  return (
    <div>
      <PageHeader title="报表分析" subtitle="多维度销售经营统计（按销售、区域、阶段、AI 贡献）" />

      <Row gutter={[16, 16]}>
        {(data.metrics ?? []).map((m) => (
          <Col xs={12} md={8} lg={4} key={m.label}>
            <Card bordered={false} style={{ height: '100%' }}>
              <Statistic title={m.label} value={m.value} valueStyle={{ fontSize: 20, fontWeight: 700 }} />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>{m.hint}</Typography.Text>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card bordered={false} title="销售额趋势">
            <BarChart data={trend} valueFormatter={(v) => formatCurrency(v)} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card bordered={false} title="区域业绩">
            <Table size="small" rowKey="name" columns={regionColumns} dataSource={data.region_performance ?? []} pagination={false} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card bordered={false} title="销售人员业绩排行">
            <Table size="small" rowKey="name" columns={ownerColumns} dataSource={data.owner_performance ?? []} pagination={false} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
