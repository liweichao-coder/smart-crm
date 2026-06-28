import { useCallback, useEffect, useState } from 'react'
import { App as AntApp, Card, Table, Tabs, Tag } from 'antd'
import { fetchAiAuditLogs, fetchBusinessAuditLogs, fetchAuthAuditLogs } from '../api.js'
import PageHeader from '../components/PageHeader.jsx'

const time = (v) => (v ? new Date(v).toLocaleString('zh-CN') : '—')

function AuditTable({ fetcher, columns }) {
  const { message } = AntApp.useApp()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const load = useCallback(() => {
    setLoading(true)
    fetcher({ limit: 100 })
      .then((d) => setRows(Array.isArray(d) ? d : d?.items ?? []))
      .catch((e) => message.error(e.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [fetcher, message])
  useEffect(load, [load])
  return (
    <Table
      rowKey="id"
      size="small"
      loading={loading}
      columns={columns}
      dataSource={rows}
      scroll={{ x: 'max-content' }}
      pagination={{ pageSize: 12, showTotal: (t) => `共 ${t} 条` }}
    />
  )
}

export default function AuditPage() {
  const aiCols = [
    { title: '时间', dataIndex: 'created_at', width: 160, render: time },
    { title: '操作', dataIndex: 'operation', width: 140 },
    { title: '模型', dataIndex: 'model', width: 140 },
    { title: '状态', dataIndex: 'status', width: 90, render: (v) => <Tag color={v === 'llm' ? 'green' : 'orange'}>{v}</Tag> },
    { title: '降级', dataIndex: 'fallback_used', width: 70, render: (v) => (v ? <Tag color="orange">是</Tag> : <Tag>否</Tag>) },
    { title: '耗时(ms)', dataIndex: 'latency_ms', width: 90, align: 'right' },
    { title: '请求摘要', dataIndex: 'request_summary', ellipsis: true },
    { title: '响应摘要', dataIndex: 'response_summary', ellipsis: true },
  ]
  const bizCols = [
    { title: '时间', dataIndex: 'created_at', width: 160, render: time },
    { title: '操作人', dataIndex: 'actor', width: 110, render: (v, r) => v ?? r.user ?? r.operator ?? '—' },
    { title: '动作', dataIndex: 'action', width: 160, render: (v, r) => v ?? r.operation ?? '—' },
    { title: '对象', dataIndex: 'entity_type', width: 120, render: (v, r) => v ?? r.target_type ?? '—' },
    { title: '详情', dataIndex: 'summary', ellipsis: true, render: (v, r) => v ?? r.detail ?? r.description ?? '' },
  ]
  const authCols = [
    { title: '时间', dataIndex: 'created_at', width: 160, render: time },
    { title: '账号', dataIndex: 'account', width: 200, render: (v, r) => v ?? r.email ?? r.actor ?? '—' },
    { title: '事件', dataIndex: 'event', width: 160, render: (v, r) => v ?? r.action ?? r.operation ?? '—' },
    { title: '结果', dataIndex: 'status', width: 100, render: (v, r) => { const s = v ?? r.result; return <Tag color={s === 'success' || s === 'ok' ? 'green' : 'red'}>{s ?? '—'}</Tag> } },
    { title: '详情', dataIndex: 'detail', ellipsis: true, render: (v, r) => v ?? r.summary ?? r.ip ?? '' },
  ]

  return (
    <div>
      <PageHeader title="审计日志" subtitle="AI 调用、业务操作与登录认证全程留痕" />
      <Card bordered={false}>
        <Tabs
          items={[
            { key: 'ai', label: 'AI 审计', children: <AuditTable fetcher={fetchAiAuditLogs} columns={aiCols} /> },
            { key: 'biz', label: '业务审计', children: <AuditTable fetcher={fetchBusinessAuditLogs} columns={bizCols} /> },
            { key: 'auth', label: '认证审计', children: <AuditTable fetcher={fetchAuthAuditLogs} columns={authCols} /> },
          ]}
        />
      </Card>
    </div>
  )
}
