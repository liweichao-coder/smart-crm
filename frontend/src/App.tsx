import { useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  createOrder,
  extractVision,
  fetchCustomers,
  fetchDashboard,
  fetchLeads,
  fetchOrders,
  fetchProducts,
} from './api'
import type {
  Customer,
  DashboardData,
  Lead,
  Order,
  OrderPayload,
  Product,
  VisionResult,
} from './types'

type SectionKey = 'overview' | 'leads' | 'customers' | 'products' | 'orders' | 'create'

const sections: Array<{ key: SectionKey; label: string; hint: string }> = [
  { key: 'overview', label: '经营总览', hint: '今日数据与趋势' },
  { key: 'leads', label: '商机跟进', hint: '阶段、负责人、行动项' },
  { key: 'customers', label: '客户资产', hint: '联系方式与分级' },
  { key: 'products', label: '商品目录', hint: '价格、库存、SKU' },
  { key: 'orders', label: '订单中心', hint: '手工与 AI 订单' },
  { key: 'create', label: '智能录单', hint: '上传图片辅助填单' },
]

const today = new Date().toISOString().slice(0, 10)
const nextWeek = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10)

const stageLabels: Record<string, string> = {
  new: '新线索',
  qualified: '已资格确认',
  proposal: '方案报价',
  negotiation: '商务洽谈',
  won: '赢单',
  lost: '丢单',
}

function currency(value: number) {
  return `¥${value.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  })
}

function App() {
  const [activeSection, setActiveSection] = useState<SectionKey>('overview')
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [leads, setLeads] = useState<Lead[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [visionResult, setVisionResult] = useState<VisionResult | null>(null)
  const [orderForm, setOrderForm] = useState<OrderPayload>({
    customer_id: 0,
    owner: '李伟超',
    region: '华东',
    currency: 'CNY',
    status: 'draft',
    order_date: today,
    due_date: nextWeek,
    notes: '',
    created_by_ai: false,
    ai_confidence_score: 0,
    items: [],
  })

  async function loadData() {
    setIsLoading(true)
    setError('')
    try {
      const [dashboardData, customersData, productsData, leadsData, ordersData] =
        await Promise.all([
          fetchDashboard(),
          fetchCustomers(),
          fetchProducts(),
          fetchLeads(),
          fetchOrders(),
        ])

      setDashboard(dashboardData)
      setCustomers(customersData)
      setProducts(productsData)
      setLeads(leadsData)
      setOrders(ordersData)

      if (!orderForm.customer_id && customersData[0]) {
        setOrderForm((current) => ({ ...current, customer_id: customersData[0].id }))
      }

      if (!orderForm.items.length && productsData[0]) {
        setOrderForm((current) => ({
          ...current,
          items: [
            {
              product_id: productsData[0].id,
              quantity: 1,
              unit_price: productsData[0].unit_price,
            },
          ],
        }))
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '加载失败')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  const totalDraftAmount = useMemo(
    () =>
      orderForm.items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0),
    [orderForm.items],
  )

  function updateItem(
    index: number,
    patch: Partial<{ product_id: number; quantity: number; unit_price: number }>,
  ) {
    setOrderForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    }))
  }

  function handleProductChange(index: number, productId: number) {
    const selected = products.find((product) => product.id === productId)
    updateItem(index, {
      product_id: productId,
      unit_price: selected?.unit_price ?? 0,
    })
  }

  function addItem() {
    if (!products[0]) {
      return
    }

    setOrderForm((current) => ({
      ...current,
      items: [
        ...current.items,
        {
          product_id: products[0].id,
          quantity: 1,
          unit_price: products[0].unit_price,
        },
      ],
    }))
  }

  function removeItem(index: number) {
    setOrderForm((current) => ({
      ...current,
      items: current.items.filter((_, itemIndex) => itemIndex !== index),
    }))
  }

  async function handleExtract(file: File) {
    setIsExtracting(true)
    setNotice('')
    setError('')
    try {
      const result = await extractVision(file)
      setVisionResult(result)

      const matchedCustomer =
        customers.find((customer) => customer.company === result.company) ?? customers[0]
      const matchedItems = result.items
        .map((item) => {
          const matchedProduct = products.find((product) => product.name === item.product_name)
          if (!matchedProduct) {
            return null
          }
          return {
            product_id: matchedProduct.id,
            quantity: item.quantity,
            unit_price: item.unit_price,
          }
        })
        .filter((item): item is NonNullable<typeof item> => Boolean(item))

      setOrderForm((current) => ({
        ...current,
        customer_id: matchedCustomer?.id ?? current.customer_id,
        notes: result.suggested_notes,
        created_by_ai: true,
        ai_confidence_score: result.confidence,
        items: matchedItems.length ? matchedItems : current.items,
      }))
      setNotice('AI 识别已完成，数据已写入草稿，请人工复核后再提交。')
    } catch (extractError) {
      setError(extractError instanceof Error ? extractError.message : '识别失败')
    } finally {
      setIsExtracting(false)
    }
  }

  async function handleSubmit() {
    if (!orderForm.customer_id || !orderForm.items.length) {
      setError('请至少选择一个客户并保留一条商品明细。')
      return
    }

    setIsSubmitting(true)
    setError('')
    setNotice('')
    try {
      await createOrder(orderForm)
      setNotice('订单已提交，订单列表与仪表盘已刷新。')
      setVisionResult(null)
      setOrderForm((current) => ({
        ...current,
        notes: '',
        created_by_ai: false,
        ai_confidence_score: 0,
        items: products[0]
          ? [{ product_id: products[0].id, quantity: 1, unit_price: products[0].unit_price }]
          : [],
      }))
      await loadData()
      setActiveSection('orders')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '提交失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SC</div>
          <div>
            <strong>Smart CRM</strong>
            <p>多模态智能销售管理系统</p>
          </div>
        </div>

        <div className="sidebar-group">
          {sections.map((section) => (
            <button
              key={section.key}
              className={section.key === activeSection ? 'nav-card active' : 'nav-card'}
              onClick={() => setActiveSection(section.key)}
              type="button"
            >
              <span>{section.label}</span>
              <small>{section.hint}</small>
            </button>
          ))}
        </div>

        <div className="sidebar-panel">
          <h3>课程验收要点</h3>
          <ul>
            <li>前后端分离与数据库落地</li>
            <li>AI 智能录单与人工确认闭环</li>
            <li>计划、架构、文档、分工齐备</li>
          </ul>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Sales Console</p>
            <h1>智能销售管理工作台</h1>
          </div>
          <div className="topbar-actions">
            <div className="status-pill online">Agent 全自动执行中</div>
            <div className="status-pill neutral">负责人: 李伟超</div>
          </div>
        </header>

        {error ? <div className="banner error">{error}</div> : null}
        {notice ? <div className="banner success">{notice}</div> : null}

        {isLoading ? (
          <section className="loading-panel">
            <div className="spinner" />
            <p>正在同步客户、商品、商机与订单数据...</p>
          </section>
        ) : (
          <>
            <section className={activeSection === 'overview' ? 'panel visible' : 'panel hidden'}>
              <div className="grid metrics-grid">
                {dashboard?.metrics.map((metric) => (
                  <article key={metric.label} className="metric-card">
                    <span>{metric.label}</span>
                    <strong>{metric.value}</strong>
                    <small>{metric.hint}</small>
                  </article>
                ))}
              </div>

              <div className="grid dashboard-grid">
                <article className="card">
                  <div className="card-head">
                    <div>
                      <h2>月度收入趋势</h2>
                      <p>使用订单金额生成演示趋势图。</p>
                    </div>
                    <span className="badge">
                      AI 订单占比 {(dashboard?.ai_orders_ratio ?? 0) * 100}%
                    </span>
                  </div>
                  <div className="bars">
                    {dashboard?.revenue_trend.map((point) => (
                      <div key={point.month} className="bar-column">
                        <div
                          className="bar-fill"
                          style={{ height: `${Math.max(32, point.revenue / 1200)}px` }}
                        />
                        <strong>{point.month.slice(5)}</strong>
                        <span>{currency(point.revenue)}</span>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="card">
                  <div className="card-head">
                    <div>
                      <h2>商机阶段分布</h2>
                      <p>按当前线索阶段统计，便于老师演示查看。</p>
                    </div>
                  </div>
                  <div className="stage-list">
                    {dashboard?.stage_distribution.map((stage) => (
                      <div key={stage.stage} className="stage-row">
                        <span>{stageLabels[stage.stage] ?? stage.stage}</span>
                        <div className="stage-track">
                          <div
                            className="stage-track-fill"
                            style={{ width: `${stage.count * 24 + 20}px` }}
                          />
                        </div>
                        <strong>{stage.count}</strong>
                      </div>
                    ))}
                  </div>
                </article>
              </div>

              <div className="grid dashboard-grid">
                <article className="card">
                  <div className="card-head">
                    <div>
                      <h2>紧急商机</h2>
                      <p>按照最近截止日期排序。</p>
                    </div>
                  </div>
                  <table>
                    <thead>
                      <tr>
                        <th>商机</th>
                        <th>负责人</th>
                        <th>阶段</th>
                        <th>截止</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard?.urgent_leads.map((lead) => (
                        <tr key={lead.id}>
                          <td>{lead.title}</td>
                          <td>{lead.owner}</td>
                          <td>{stageLabels[lead.stage]}</td>
                          <td>{formatDate(lead.due_date)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </article>

                <article className="card">
                  <div className="card-head">
                    <div>
                      <h2>最近订单</h2>
                      <p>支持区分 AI 辅助订单和传统手工订单。</p>
                    </div>
                  </div>
                  <table>
                    <thead>
                      <tr>
                        <th>客户</th>
                        <th>状态</th>
                        <th>金额</th>
                        <th>来源</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard?.recent_orders.map((order) => (
                        <tr key={order.id}>
                          <td>{order.customer_name}</td>
                          <td>{order.status}</td>
                          <td>{currency(order.total_amount)}</td>
                          <td>{order.created_by_ai ? 'AI 辅助' : '手工'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </article>
              </div>
            </section>

            <section className={activeSection === 'leads' ? 'panel visible' : 'panel hidden'}>
              <article className="card">
                <div className="card-head">
                  <div>
                    <h2>销售商机列表</h2>
                    <p>保留 CRM 信息密度，突出负责人、阶段与下一步行动项。</p>
                  </div>
                  <span className="badge accent">{leads.length} 条商机</span>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>标题</th>
                      <th>客户</th>
                      <th>负责人</th>
                      <th>区域</th>
                      <th>预计金额</th>
                      <th>阶段</th>
                      <th>下一动作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((lead) => (
                      <tr key={lead.id}>
                        <td>{lead.title}</td>
                        <td>{lead.customer_name}</td>
                        <td>{lead.owner}</td>
                        <td>{lead.region}</td>
                        <td>{currency(lead.expected_amount)}</td>
                        <td>{stageLabels[lead.stage]}</td>
                        <td>{lead.next_action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </article>
            </section>

            <section className={activeSection === 'customers' ? 'panel visible' : 'panel hidden'}>
              <article className="card">
                <div className="card-head">
                  <div>
                    <h2>客户资产池</h2>
                    <p>展示客户分级、来源、行业和联系方式。</p>
                  </div>
                </div>
                <div className="customer-grid">
                  {customers.map((customer) => (
                    <article key={customer.id} className="customer-card">
                      <div className="customer-card-top">
                        <strong>{customer.company}</strong>
                        <span className="badge">{customer.level} 级客户</span>
                      </div>
                      <p>{customer.industry}</p>
                      <dl>
                        <div>
                          <dt>联系人</dt>
                          <dd>{customer.contact_person}</dd>
                        </div>
                        <div>
                          <dt>电话</dt>
                          <dd>{customer.phone}</dd>
                        </div>
                        <div>
                          <dt>来源</dt>
                          <dd>{customer.source}</dd>
                        </div>
                        <div>
                          <dt>城市</dt>
                          <dd>{customer.city}</dd>
                        </div>
                      </dl>
                    </article>
                  ))}
                </div>
              </article>
            </section>

            <section className={activeSection === 'products' ? 'panel visible' : 'panel hidden'}>
              <article className="card">
                <div className="card-head">
                  <div>
                    <h2>商品与库存</h2>
                    <p>当前商品目录同时服务报表展示与新建订单。</p>
                  </div>
                </div>
                <div className="product-grid">
                  {products.map((product) => (
                    <article key={product.id} className="product-card">
                      <span className="eyebrow tag">{product.category}</span>
                      <strong>{product.name}</strong>
                      <p>{product.sku}</p>
                      <div className="product-meta">
                        <span>{currency(product.unit_price)}</span>
                        <span>库存 {product.stock}</span>
                      </div>
                    </article>
                  ))}
                </div>
              </article>
            </section>

            <section className={activeSection === 'orders' ? 'panel visible' : 'panel hidden'}>
              <article className="card">
                <div className="card-head">
                  <div>
                    <h2>订单中心</h2>
                    <p>已汇总手工录入和 AI 辅助录入订单。</p>
                  </div>
                  <span className="badge accent">{orders.length} 笔订单</span>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>客户</th>
                      <th>负责人</th>
                      <th>区域</th>
                      <th>状态</th>
                      <th>金额</th>
                      <th>来源</th>
                      <th>交付日</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id}>
                        <td>{order.customer_name}</td>
                        <td>{order.owner}</td>
                        <td>{order.region}</td>
                        <td>{order.status}</td>
                        <td>{currency(order.total_amount)}</td>
                        <td>{order.created_by_ai ? 'AI 辅助' : '手工'}</td>
                        <td>{formatDate(order.due_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </article>
            </section>

            <section className={activeSection === 'create' ? 'panel visible' : 'panel hidden'}>
              <div className="grid create-grid">
                <article className="card">
                  <div className="card-head">
                    <div>
                      <h2>AI 多模态录单面板</h2>
                      <p>上传聊天截图、票据或发票图片后自动填单，再由人工确认提交。</p>
                    </div>
                    <span className="badge accent">
                      {isExtracting ? '识别中' : '人在回路'}
                    </span>
                  </div>

                  <label className="upload-box">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(event) => {
                        const file = event.target.files?.[0]
                        if (file) {
                          void handleExtract(file)
                        }
                      }}
                    />
                    <strong>拖拽或选择图片上传</strong>
                    <p>建议使用 `非代码部分/前端参考图片` 中的图片作为演示素材。</p>
                  </label>

                  {visionResult ? (
                    <div className="vision-result">
                      <div className="result-head">
                        <div>
                          <strong>{visionResult.company}</strong>
                          <p>{visionResult.customer_name}</p>
                        </div>
                        <span className="badge">
                          置信度 {(visionResult.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p>{visionResult.summary}</p>
                      <ul className="result-list">
                        {visionResult.items.map((item) => (
                          <li key={`${item.product_name}-${item.quantity}`}>
                            <span>{item.product_name}</span>
                            <span>
                              {item.quantity} x {currency(item.unit_price)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </article>

                <article className="card">
                  <div className="card-head">
                    <div>
                      <h2>订单草稿复核</h2>
                      <p>系统不会直接入库，必须在这里人工检查并提交。</p>
                    </div>
                    <span className="badge">{currency(totalDraftAmount)}</span>
                  </div>

                  <div className="form-grid">
                    <label>
                      <span>客户</span>
                      <select
                        value={orderForm.customer_id}
                        onChange={(event) =>
                          setOrderForm((current) => ({
                            ...current,
                            customer_id: Number(event.target.value),
                          }))
                        }
                      >
                        {customers.map((customer) => (
                          <option key={customer.id} value={customer.id}>
                            {customer.company}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      <span>负责人</span>
                      <input
                        value={orderForm.owner}
                        onChange={(event) =>
                          setOrderForm((current) => ({ ...current, owner: event.target.value }))
                        }
                      />
                    </label>

                    <label>
                      <span>区域</span>
                      <input
                        value={orderForm.region}
                        onChange={(event) =>
                          setOrderForm((current) => ({ ...current, region: event.target.value }))
                        }
                      />
                    </label>

                    <label>
                      <span>状态</span>
                      <select
                        value={orderForm.status}
                        onChange={(event) =>
                          setOrderForm((current) => ({
                            ...current,
                            status: event.target.value as OrderPayload['status'],
                          }))
                        }
                      >
                        <option value="draft">草稿</option>
                        <option value="confirmed">已确认</option>
                        <option value="fulfilled">已完成</option>
                      </select>
                    </label>

                    <label>
                      <span>下单日期</span>
                      <input
                        type="date"
                        value={orderForm.order_date}
                        onChange={(event) =>
                          setOrderForm((current) => ({
                            ...current,
                            order_date: event.target.value,
                          }))
                        }
                      />
                    </label>

                    <label>
                      <span>交付日期</span>
                      <input
                        type="date"
                        value={orderForm.due_date}
                        onChange={(event) =>
                          setOrderForm((current) => ({
                            ...current,
                            due_date: event.target.value,
                          }))
                        }
                      />
                    </label>
                  </div>

                  <div className="line-items">
                    <div className="line-items-head">
                      <h3>商品明细</h3>
                      <button type="button" className="ghost-button" onClick={addItem}>
                        添加一行
                      </button>
                    </div>
                    {orderForm.items.map((item, index) => (
                      <div key={`${item.product_id}-${index}`} className="line-row">
                        <select
                          value={item.product_id}
                          onChange={(event) => handleProductChange(index, Number(event.target.value))}
                        >
                          {products.map((product) => (
                            <option key={product.id} value={product.id}>
                              {product.name}
                            </option>
                          ))}
                        </select>
                        <input
                          type="number"
                          min="1"
                          value={item.quantity}
                          onChange={(event) =>
                            updateItem(index, { quantity: Number(event.target.value) })
                          }
                        />
                        <input
                          type="number"
                          min="0"
                          value={item.unit_price}
                          onChange={(event) =>
                            updateItem(index, { unit_price: Number(event.target.value) })
                          }
                        />
                        <strong>{currency(item.quantity * item.unit_price)}</strong>
                        <button
                          type="button"
                          className="ghost-button danger"
                          onClick={() => removeItem(index)}
                          disabled={orderForm.items.length === 1}
                        >
                          删除
                        </button>
                      </div>
                    ))}
                  </div>

                  <label className="notes-field">
                    <span>备注</span>
                    <textarea
                      rows={4}
                      value={orderForm.notes}
                      onChange={(event) =>
                        setOrderForm((current) => ({ ...current, notes: event.target.value }))
                      }
                    />
                  </label>

                  <div className="toggle-row">
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={orderForm.created_by_ai}
                        onChange={(event) =>
                          setOrderForm((current) => ({
                            ...current,
                            created_by_ai: event.target.checked,
                          }))
                        }
                      />
                      <span>本订单为 AI 辅助生成</span>
                    </label>
                    <label className="confidence">
                      <span>AI 置信度</span>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={orderForm.ai_confidence_score}
                        onChange={(event) =>
                          setOrderForm((current) => ({
                            ...current,
                            ai_confidence_score: Number(event.target.value),
                          }))
                        }
                      />
                    </label>
                  </div>

                  <div className="submit-row">
                    <div>
                      <strong>草稿总额 {currency(totalDraftAmount)}</strong>
                      <p>提交后将写入数据库，并在订单中心与仪表盘刷新展示。</p>
                    </div>
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => void handleSubmit()}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? '提交中...' : '确认并创建订单'}
                    </button>
                  </div>
                </article>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

export default App
