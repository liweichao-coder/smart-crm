import { useEffect, useRef, useState } from 'react'
import {
  App as AntApp,
  Avatar,
  Button,
  Card,
  Col,
  Empty,
  Input,
  List,
  Rate,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import { RobotOutlined, SendOutlined, UserOutlined, BulbOutlined, FileTextOutlined } from '@ant-design/icons'
import {
  askCopilot,
  fetchCopilotSummary,
  fetchCopilotRecommendations,
  convertCopilotRecommendationToTask,
  submitCopilotRecommendationFeedback,
  generateOrderDraft,
  fetchCustomers,
  fetchProducts,
} from '../api.js'
import PageHeader from '../components/PageHeader.jsx'
import { LEAD_STAGES, labelOf, colorOf, formatCurrency } from '../constants.js'
import { BRAND } from '../theme.js'

const SUGGESTED = [
  '本月哪些商机最值得优先跟进？',
  '哪些客户存在流失风险，应该如何处理？',
  '帮我总结当前销售管道的整体健康度',
]

function ModelTag({ fallback }) {
  return fallback ? (
    <Tag color="orange">本地降级</Tag>
  ) : (
    <Tag color="green">DeepSeek 实时</Tag>
  )
}

function ChatPanel() {
  const { message } = AntApp.useApp()
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好，我是智销 CRM 的销售 Copilot。我可以基于你的客户、商机和订单数据回答经营问题，并给出下一步建议。试试下面的问题，或直接输入。' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const question = (text ?? input).trim()
    if (!question || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: question }])
    setLoading(true)
    try {
      const res = await askCopilot({ question })
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: res.answer,
          next_actions: res.next_actions,
          evidence: res.evidence,
          fallback: res.fallback_used,
          model: res.model,
        },
      ])
    } catch (e) {
      message.error(e.message || 'AI 回答失败')
      setMessages((m) => [...m, { role: 'assistant', content: '抱歉，我暂时无法回答，请稍后再试。', fallback: true }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card bordered={false} style={{ height: '100%', display: 'flex', flexDirection: 'column' }} styles={{ body: { display: 'flex', flexDirection: 'column', height: 560 } }}>
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: 6 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 18, flexDirection: m.role === 'user' ? 'row-reverse' : 'row' }}>
            <Avatar
              icon={m.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
              style={{ background: m.role === 'user' ? '#8694AD' : BRAND.primary, flexShrink: 0 }}
            />
            <div
              style={{
                maxWidth: '78%',
                background: m.role === 'user' ? BRAND.primary : '#F5F8FF',
                color: m.role === 'user' ? '#fff' : '#1F2A44',
                borderRadius: 12,
                padding: '10px 14px',
              }}
            >
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{m.content}</div>
              {m.next_actions?.length ? (
                <div style={{ marginTop: 8 }}>
                  <Typography.Text strong style={{ fontSize: 12 }}>建议动作：</Typography.Text>
                  <ul style={{ margin: '4px 0 0', paddingInlineStart: 18 }}>
                    {m.next_actions.map((a, j) => (
                      <li key={j} style={{ fontSize: 13 }}>{a}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {m.evidence?.length ? (
                <div style={{ marginTop: 6 }}>
                  {m.evidence.map((e, j) => (
                    <Tag key={j} style={{ marginBottom: 4 }}>{e}</Tag>
                  ))}
                </div>
              ) : null}
              {m.role === 'assistant' && m.model ? <div style={{ marginTop: 6 }}><ModelTag fallback={m.fallback} /></div> : null}
            </div>
          </div>
        ))}
        {loading ? (
          <div style={{ display: 'flex', gap: 10 }}>
            <Avatar icon={<RobotOutlined />} style={{ background: BRAND.primary }} />
            <div style={{ background: '#F5F8FF', borderRadius: 12, padding: '10px 14px' }}>
              <Spin size="small" /> <span style={{ color: '#8694AD', marginInlineStart: 8 }}>正在思考…</span>
            </div>
          </div>
        ) : null}
        <div ref={endRef} />
      </div>

      <div style={{ marginTop: 12 }}>
        <Space wrap style={{ marginBottom: 8 }}>
          {SUGGESTED.map((s) => (
            <Button key={s} size="small" onClick={() => send(s)} disabled={loading}>
              {s}
            </Button>
          ))}
        </Space>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            size="large"
            placeholder="输入你的经营问题…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={() => send()}
            disabled={loading}
          />
          <Button size="large" type="primary" icon={<SendOutlined />} onClick={() => send()} loading={loading}>
            发送
          </Button>
        </Space.Compact>
      </div>
    </Card>
  )
}

function RecommendationsPanel() {
  const { message } = AntApp.useApp()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState(null)

  const load = () => {
    setLoading(true)
    fetchCopilotRecommendations({ limit: 20 })
      .then((d) => setRows(Array.isArray(d) ? d : d?.items ?? []))
      .catch((e) => message.error(e.message || '加载推荐失败'))
      .finally(() => setLoading(false))
  }
  useEffect(load, []) // eslint-disable-line react-hooks/exhaustive-deps

  const toTask = async (rec) => {
    setBusyId(rec.id)
    try {
      await convertCopilotRecommendationToTask(rec.id)
      message.success('已转为跟进任务')
    } catch (e) {
      message.error(e.message || '转任务失败')
    } finally {
      setBusyId(null)
    }
  }

  const feedback = async (rec, status) => {
    try {
      await submitCopilotRecommendationFeedback(rec.id, { feedback_status: status })
      message.success('已记录反馈')
      load()
    } catch (e) {
      message.error(e.message || '反馈失败')
    }
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!rows.length) return <Empty description="暂无 AI 推荐" />

  return (
    <List
      dataSource={rows}
      pagination={{ pageSize: 5 }}
      renderItem={(rec) => (
        <List.Item style={{ display: 'block' }}>
          <Card size="small" bordered style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
              <Space>
                <Typography.Text strong>{rec.lead_title}</Typography.Text>
                <Tag color={colorOf(LEAD_STAGES, rec.stage)}>{labelOf(LEAD_STAGES, rec.stage)}</Tag>
                <Tag color="blue">评分 {rec.rule_score} · {rec.grade} 级</Tag>
                <Tag>赢率 {Math.round((rec.win_rate ?? 0) * 100)}%</Tag>
              </Space>
              <Typography.Text type="secondary">{rec.customer_name} · {formatCurrency(rec.expected_amount)}</Typography.Text>
            </div>
            <Typography.Paragraph style={{ margin: '8px 0', fontSize: 13 }} ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}>
              {rec.next_best_action}
            </Typography.Paragraph>
            <Space wrap>
              <Button size="small" type="primary" ghost loading={busyId === rec.id} onClick={() => toTask(rec)}>
                转为跟进任务
              </Button>
              <Button size="small" onClick={() => feedback(rec, 'accepted')}>采纳</Button>
              <Button size="small" onClick={() => feedback(rec, 'not_helpful')}>无帮助</Button>
              {rec.feedback_status ? <Tag color="green">已反馈：{rec.feedback_status}</Tag> : null}
              <ModelTag fallback={rec.fallback_used} />
            </Space>
          </Card>
        </List.Item>
      )}
    />
  )
}

function OrderDraftPanel() {
  const { message } = AntApp.useApp()
  const [customers, setCustomers] = useState([])
  const [products, setProducts] = useState([])
  const [customerId, setCustomerId] = useState(null)
  const [productIds, setProductIds] = useState([])
  const [goal, setGoal] = useState('')
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchCustomers({}).then((d) => setCustomers(Array.isArray(d) ? d : d?.items ?? [])).catch(() => {})
    fetchProducts({}).then((d) => setProducts(Array.isArray(d) ? d : d?.items ?? [])).catch(() => {})
  }, [])

  const generate = async () => {
    if (!customerId) {
      message.warning('请选择客户')
      return
    }
    setLoading(true)
    try {
      const res = await generateOrderDraft({ customer_id: customerId, product_ids: productIds, business_goal: goal })
      setDraft(res)
    } catch (e) {
      message.error(e.message || '生成失败')
    } finally {
      setLoading(false)
    }
  }

  const total = (draft?.items ?? []).reduce((s, i) => s + i.unit_price * i.quantity, 0)

  return (
    <Row gutter={16}>
      <Col xs={24} md={10}>
        <Card size="small" title="录单条件" bordered>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Select
              showSearch
              placeholder="选择客户"
              style={{ width: '100%' }}
              value={customerId}
              onChange={setCustomerId}
              optionFilterProp="label"
              options={customers.map((c) => ({ value: c.id, label: c.company || c.name }))}
            />
            <Select
              mode="multiple"
              placeholder="选择意向产品（可多选）"
              style={{ width: '100%' }}
              value={productIds}
              onChange={setProductIds}
              optionFilterProp="label"
              options={products.map((p) => ({ value: p.id, label: `${p.name}（${formatCurrency(p.unit_price)}）` }))}
            />
            <Input.TextArea rows={3} placeholder="业务目标 / 补充说明（可选）" value={goal} onChange={(e) => setGoal(e.target.value)} />
            <Button type="primary" icon={<FileTextOutlined />} block loading={loading} onClick={generate}>
              AI 生成订单草稿
            </Button>
          </Space>
        </Card>
      </Col>
      <Col xs={24} md={14}>
        <Card size="small" title="订单草稿" bordered>
          {draft ? (
            <div>
              <Typography.Text strong>{draft.customer_name}</Typography.Text> <ModelTag fallback={draft.fallback_used} />
              <List
                size="small"
                style={{ marginTop: 8 }}
                dataSource={draft.items ?? []}
                renderItem={(i) => (
                  <List.Item>
                    <span>{i.product_name}</span>
                    <span>{i.quantity} × {formatCurrency(i.unit_price)} = <strong>{formatCurrency(i.quantity * i.unit_price)}</strong></span>
                  </List.Item>
                )}
              />
              <div style={{ textAlign: 'right', marginTop: 8 }}>
                <Statistic title="合计" value={formatCurrency(total)} valueStyle={{ color: BRAND.primary, fontSize: 20 }} />
              </div>
              {draft.suggested_notes ? (
                <div style={{ background: '#F5F8FF', borderRadius: 8, padding: 10, marginTop: 8 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>建议备注：{draft.suggested_notes}</Typography.Text>
                </div>
              ) : null}
              {draft.llm_summary ? (
                <Typography.Paragraph style={{ fontSize: 13, marginTop: 8 }}>{draft.llm_summary}</Typography.Paragraph>
              ) : null}
              <Typography.Text type="warning" style={{ fontSize: 12 }}>
                * AI 生成结果需人工确认后再正式提交，草稿不会直接入库。
              </Typography.Text>
            </div>
          ) : (
            <Empty description="选择客户与产品后生成草稿" />
          )}
        </Card>
      </Col>
    </Row>
  )
}

function SummaryStrip() {
  const [summary, setSummary] = useState(null)
  useEffect(() => {
    fetchCopilotSummary().then(setSummary).catch(() => {})
  }, [])
  if (!summary) return null
  return (
    <Row gutter={16} style={{ marginBottom: 16 }}>
      <Col xs={8}>
        <Card bordered={false}><Statistic title="预测成交额" value={formatCurrency(summary.forecast_amount)} valueStyle={{ color: BRAND.primary }} /></Card>
      </Col>
      <Col xs={8}>
        <Card bordered={false}><Statistic title="风险商机" value={summary.at_risk_count} suffix="个" valueStyle={{ color: '#F76C6C' }} /></Card>
      </Col>
      <Col xs={8}>
        <Card bordered={false}>
          <Statistic title="头部商机" value={summary.top_opportunity?.title ?? '-'} valueStyle={{ fontSize: 16 }} />
        </Card>
      </Col>
    </Row>
  )
}

export default function CopilotPage() {
  return (
    <div>
      <PageHeader
        title={<><RobotOutlined style={{ color: BRAND.primary }} /> AI 销售助手</>}
        subtitle="DeepSeek 驱动的对话洞察、商机评分与智能录单"
      />
      <SummaryStrip />
      <Tabs
        defaultActiveKey="chat"
        items={[
          { key: 'chat', label: <span><BulbOutlined /> 对话助手</span>, children: <ChatPanel /> },
          { key: 'rec', label: '商机推荐与评分', children: <Card bordered={false}><RecommendationsPanel /></Card> },
          { key: 'draft', label: 'AI 订单草稿', children: <OrderDraftPanel /> },
        ]}
      />
    </div>
  )
}
