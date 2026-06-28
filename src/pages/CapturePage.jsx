import { useEffect, useMemo, useState } from 'react'
import {
  App as AntApp,
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Input,
  InputNumber,
  Progress,
  Row,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
} from 'antd'
import { InboxOutlined, RobotOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { extractOrderFromFile, createOrder, fetchCustomers, fetchProducts } from '../api.js'
import PageHeader from '../components/PageHeader.jsx'
import { useAuth } from '../auth/AuthContext.jsx'
import { formatCurrency } from '../constants.js'
import { BRAND } from '../theme.js'

const SAMPLE = `北辰教育科技 王凯
采购：移动录单套件 x3，AI 商机评分模块 x2
预计本月底前交付，含一年质保`

export default function CapturePage() {
  const { user } = useAuth()
  const { message } = AntApp.useApp()
  const [text, setText] = useState(SAMPLE)
  const [extracting, setExtracting] = useState(false)
  const [draft, setDraft] = useState(null)
  const [customers, setCustomers] = useState([])
  const [products, setProducts] = useState([])

  // 提交表单字段
  const [customerId, setCustomerId] = useState(null)
  const [region, setRegion] = useState('华南')
  const [items, setItems] = useState([])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchCustomers({}).then((d) => setCustomers(Array.isArray(d) ? d : d?.items ?? [])).catch(() => {})
    fetchProducts({}).then((d) => setProducts(Array.isArray(d) ? d : d?.items ?? [])).catch(() => {})
  }, [])

  const applyDraft = (res) => {
    setDraft(res)
    setCustomerId(res.customer_id ?? null)
    setItems(
      (res.items ?? []).map((it, idx) => ({
        key: idx,
        product_id: it.product_id ?? null,
        quantity: it.quantity ?? 1,
        unit_price: it.unit_price ?? 0,
      })),
    )
  }

  const runText = async () => {
    if (!text.trim()) {
      message.warning('请输入订单文本')
      return
    }
    setExtracting(true)
    try {
      const blob = new File([text], 'order.txt', { type: 'text/plain' })
      const res = await extractOrderFromFile(blob)
      applyDraft(res)
      message.success(res.fallback_used ? '已用本地解析生成草稿' : 'DeepSeek 识别完成')
    } catch (e) {
      message.error(e.message || '识别失败')
    } finally {
      setExtracting(false)
    }
  }

  const runImage = async (file) => {
    setExtracting(true)
    try {
      const res = await extractOrderFromFile(file)
      applyDraft(res)
      message.success('已生成订单草稿，请人工复核')
    } catch (e) {
      message.error(e.message || '识别失败')
    } finally {
      setExtracting(false)
    }
    return false
  }

  const total = useMemo(
    () => items.reduce((s, it) => s + (it.unit_price || 0) * (it.quantity || 0), 0),
    [items],
  )

  const submit = async () => {
    if (!customerId) {
      message.warning('请选择客户')
      return
    }
    if (!items.length || items.some((it) => !it.product_id)) {
      message.warning('每个明细行都需选择产品')
      return
    }
    setSubmitting(true)
    try {
      const today = new Date()
      const due = new Date(today.getTime() + 7 * 86400000)
      const fmt = (d) => d.toISOString().slice(0, 10)
      await createOrder({
        customer_id: customerId,
        owner: user?.full_name || '销售',
        region,
        currency: 'CNY',
        status: 'draft',
        order_date: fmt(today),
        due_date: fmt(due),
        notes: `AI 智能录单生成，来源 ${draft?.source ?? 'capture'}；已人工复核。`,
        created_by_ai: true,
        ai_confidence_score: draft?.confidence ?? 0.8,
        items: items.map((it) => ({ product_id: it.product_id, quantity: it.quantity, unit_price: it.unit_price })),
      })
      message.success('订单已创建（草稿状态），可在「订单」页查看')
      setDraft(null)
      setItems([])
      setCustomerId(null)
    } catch (e) {
      message.error(e.message || '创建订单失败')
    } finally {
      setSubmitting(false)
    }
  }

  const itemColumns = [
    {
      title: '产品',
      dataIndex: 'product_id',
      render: (v, r) => (
        <Select
          showSearch
          style={{ width: 220 }}
          placeholder="选择产品"
          value={v}
          optionFilterProp="label"
          options={products.map((p) => ({ value: p.id, label: p.name }))}
          onChange={(val) => {
            const p = products.find((x) => x.id === val)
            setItems((prev) => prev.map((it) => (it.key === r.key ? { ...it, product_id: val, unit_price: p ? p.unit_price : it.unit_price } : it)))
          }}
        />
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      width: 110,
      render: (v, r) => (
        <InputNumber min={1} value={v} onChange={(val) => setItems((prev) => prev.map((it) => (it.key === r.key ? { ...it, quantity: val || 1 } : it)))} />
      ),
    },
    {
      title: '单价',
      dataIndex: 'unit_price',
      width: 130,
      render: (v, r) => (
        <InputNumber min={0} value={v} formatter={(val) => `¥${val}`} parser={(val) => val.replace(/[^\d.]/g, '')} onChange={(val) => setItems((prev) => prev.map((it) => (it.key === r.key ? { ...it, unit_price: val || 0 } : it)))} />
      ),
    },
    { title: '小计', width: 120, align: 'right', render: (_, r) => formatCurrency((r.unit_price || 0) * (r.quantity || 0)) },
    {
      title: '',
      width: 60,
      render: (_, r) => <Button type="link" danger size="small" onClick={() => setItems((prev) => prev.filter((it) => it.key !== r.key))}>删除</Button>,
    },
  ]

  return (
    <div>
      <PageHeader
        title={<><ThunderboltOutlined style={{ color: BRAND.primary }} /> AI 智能录单</>}
        subtitle="粘贴订单文本由 DeepSeek 自动提取，或上传截图生成草稿，人工确认后入库"
      />
      <Row gutter={16}>
        <Col xs={24} lg={10}>
          <Card bordered={false} title="① 录入来源">
            <Tabs
              items={[
                {
                  key: 'text',
                  label: '粘贴文本（DeepSeek 提取）',
                  children: (
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Input.TextArea rows={7} value={text} onChange={(e) => setText(e.target.value)} placeholder="例如：北辰教育科技 采购 移动录单套件 x3 ..." />
                      <Button type="primary" icon={<RobotOutlined />} loading={extracting} onClick={runText} block>
                        AI 识别订单信息
                      </Button>
                    </Space>
                  ),
                },
                {
                  key: 'image',
                  label: '上传图片/文件',
                  children: (
                    <>
                      <Upload.Dragger accept="image/*,.txt,.csv,.md" beforeUpload={runImage} showUploadList={false} disabled={extracting}>
                        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                        <p className="ant-upload-text">点击或拖拽订单截图/文件到此处</p>
                        <p className="ant-upload-hint" style={{ fontSize: 12 }}>支持订单截图、报价单、文本文件</p>
                      </Upload.Dragger>
                      <Alert
                        style={{ marginTop: 12 }}
                        type="info"
                        showIcon
                        message="说明：图片为本地启发式解析草稿；文本内容由 DeepSeek 实时结构化提取。"
                      />
                    </>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card bordered={false} title="② 复核并创建订单">
            {draft ? (
              <div>
                <Space wrap style={{ marginBottom: 12 }}>
                  <Tag color={draft.fallback_used ? 'orange' : 'green'}>{draft.fallback_used ? '本地解析' : 'DeepSeek 实时'}</Tag>
                  <span style={{ color: '#5B6B86', fontSize: 13 }}>识别置信度</span>
                  <Progress percent={Math.round((draft.confidence ?? 0) * 100)} size="small" style={{ width: 160 }} strokeColor={BRAND.primary} />
                </Space>
                {draft.summary ? <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>{draft.summary}</Typography.Paragraph> : null}
                <Row gutter={12} style={{ marginBottom: 12 }}>
                  <Col span={14}>
                    <div style={{ fontSize: 12, color: '#8694AD', marginBottom: 4 }}>客户</div>
                    <Select showSearch style={{ width: '100%' }} placeholder="选择客户" value={customerId} optionFilterProp="label" options={customers.map((c) => ({ value: c.id, label: c.company || c.name }))} onChange={setCustomerId} />
                  </Col>
                  <Col span={10}>
                    <div style={{ fontSize: 12, color: '#8694AD', marginBottom: 4 }}>区域</div>
                    <Input value={region} onChange={(e) => setRegion(e.target.value)} />
                  </Col>
                </Row>
                <Table size="small" rowKey="key" columns={itemColumns} dataSource={items} pagination={false} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 14 }}>
                  <Typography.Text strong>合计：<span style={{ color: BRAND.primary, fontSize: 18 }}>{formatCurrency(total)}</span></Typography.Text>
                  <Space>
                    <Button onClick={() => setItems((prev) => [...prev, { key: Date.now(), product_id: null, quantity: 1, unit_price: 0 }])}>添加明细</Button>
                    <Button type="primary" loading={submitting} onClick={submit}>确认并创建订单</Button>
                  </Space>
                </div>
                <Alert style={{ marginTop: 12 }} type="warning" showIcon message="AI 提取结果不会直接入库，确认无误后才会创建订单（草稿状态）。" />
              </div>
            ) : (
              <Empty description="先在左侧识别，生成订单草稿" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
