import { useCallback, useEffect, useState } from 'react'
import { App as AntApp, Button, Card, Space, Table, Tag } from 'antd'
import { DownloadOutlined, ReloadOutlined, RobotOutlined } from '@ant-design/icons'
import { fetchOrders, exportOrdersCsv } from '../api.js'
import PageHeader from '../components/PageHeader.jsx'
import { ORDER_STATUS, labelOf, colorOf, formatCurrency } from '../constants.js'
import { BRAND } from '../theme.js'

export default function OrdersPage() {
  const { message } = AntApp.useApp()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    fetchOrders({})
      .then((d) => setRows(Array.isArray(d) ? d : d?.items ?? []))
      .catch((e) => message.error(e.message || '加载订单失败'))
      .finally(() => setLoading(false))
  }, [message])

  useEffect(() => {
    load()
  }, [load])

  const handleExport = async () => {
    try {
      const blob = await exportOrdersCsv()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'orders.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      message.error(e.message || '导出失败')
    }
  }

  const columns = [
    { title: '订单号', dataIndex: 'id', width: 90, render: (v) => `#${v}` },
    { title: '客户', dataIndex: 'customer_name', render: (v, r) => (
      <strong>{v}{r.created_by_ai ? <Tag color={BRAND.primary} icon={<RobotOutlined />} style={{ marginInlineStart: 6 }}>AI</Tag> : null}</strong>
    ) },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    { title: '区域', dataIndex: 'region', width: 80 },
    { title: '金额', dataIndex: 'total_amount', align: 'right', render: (v, r) => formatCurrency(v, r.currency) },
    { title: '状态', dataIndex: 'status', width: 100, render: (v) => <Tag color={colorOf(ORDER_STATUS, v)}>{labelOf(ORDER_STATUS, v)}</Tag> },
    { title: 'AI 置信度', dataIndex: 'ai_confidence_score', width: 110, align: 'right', render: (v, r) => (r.created_by_ai ? `${Math.round((v ?? 0) * 100)}%` : '-') },
    { title: '下单日期', dataIndex: 'order_date', width: 120 },
    { title: '交付日期', dataIndex: 'due_date', width: 120 },
  ]

  const expandedRowRender = (record) => (
    <Table
      size="small"
      rowKey="id"
      pagination={false}
      dataSource={record.items ?? []}
      columns={[
        { title: '产品', dataIndex: 'product_name' },
        { title: '数量', dataIndex: 'quantity', align: 'right', width: 80 },
        { title: '单价', dataIndex: 'unit_price', align: 'right', render: (v) => formatCurrency(v) },
        { title: '小计', dataIndex: 'line_total', align: 'right', render: (v) => formatCurrency(v) },
      ]}
    />
  )

  return (
    <div>
      <PageHeader
        title="订单"
        subtitle="销售订单与明细（含 AI 录单标记）"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={load}>刷新</Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
          </Space>
        }
      />
      <Card bordered={false} styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={rows}
          expandable={{ expandedRowRender, rowExpandable: (r) => (r.items ?? []).length > 0 }}
          scroll={{ x: 'max-content' }}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        />
      </Card>
    </div>
  )
}
