import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App as AntApp,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
} from 'antd'
import { PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import PageHeader from './PageHeader.jsx'

/**
 * 通用资源表格：列表 + 搜索 + 新建/编辑弹窗 + 删除。
 * props:
 *  - title, subtitle
 *  - columns: antd 列定义（不含操作列）
 *  - fetchList(params) -> array
 *  - createItem(payload), updateItem(id, payload), deleteItem(id)
 *  - formFields: [{ name, label, type, options, required, rules, span, placeholder }]
 *  - rowKey (默认 'id')
 *  - canWrite (是否显示新建/编辑/删除)
 *  - expandable (antd expandable 配置)
 *  - searchKeys: 本地搜索匹配的字段
 *  - extraActions(record) -> ReactNode（追加到操作列）
 */
export default function ResourceTable({
  title,
  subtitle,
  columns,
  fetchList,
  createItem,
  updateItem,
  deleteItem,
  formFields = [],
  rowKey = 'id',
  canWrite = true,
  expandable,
  searchKeys = [],
  extraActions,
  extraToolbar,
}) {
  const { message } = AntApp.useApp()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = useCallback(() => {
    setLoading(true)
    fetchList({})
      .then((data) => setRows(Array.isArray(data) ? data : data?.items ?? []))
      .catch((e) => message.error(e.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [fetchList, message])

  useEffect(() => {
    load()
  }, [load])

  const filtered = useMemo(() => {
    if (!keyword.trim() || !searchKeys.length) return rows
    const kw = keyword.trim().toLowerCase()
    return rows.filter((r) => searchKeys.some((k) => String(r[k] ?? '').toLowerCase().includes(kw)))
  }, [rows, keyword, searchKeys])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    const values = { ...record }
    formFields.forEach((f) => {
      if (f.type === 'date' && values[f.name]) {
        values[f.name] = dayjs(values[f.name])
      }
    })
    form.setFieldsValue(values)
    setModalOpen(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    formFields.forEach((f) => {
      if (f.type === 'date' && values[f.name]) {
        values[f.name] = dayjs(values[f.name]).format('YYYY-MM-DD')
      }
    })
    setSaving(true)
    try {
      if (editing) {
        await updateItem(editing[rowKey], values)
        message.success('已更新')
      } else {
        await createItem(values)
        message.success('已创建')
      }
      setModalOpen(false)
      load()
    } catch (e) {
      message.error(e.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (record) => {
    try {
      await deleteItem(record[rowKey])
      message.success('已删除')
      load()
    } catch (e) {
      message.error(e.message || '删除失败')
    }
  }

  const fullColumns = useMemo(() => {
    const hasActions = canWrite && (updateItem || deleteItem || extraActions)
    if (!hasActions) return columns
    return [
      ...columns,
      {
        title: '操作',
        key: '__actions',
        fixed: 'right',
        width: 160,
        render: (_, record) => (
          <Space size={4}>
            {extraActions ? extraActions(record, load) : null}
            {updateItem ? (
              <Button type="link" size="small" onClick={() => openEdit(record)}>
                编辑
              </Button>
            ) : null}
            {deleteItem ? (
              <Popconfirm title="确认删除该记录？" onConfirm={() => handleDelete(record)} okText="删除" cancelText="取消">
                <Button type="link" size="small" danger>
                  删除
                </Button>
              </Popconfirm>
            ) : null}
          </Space>
        ),
      },
    ]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns, canWrite, updateItem, deleteItem, extraActions])

  return (
    <div>
      <PageHeader
        title={title}
        subtitle={subtitle}
        extra={
          <Space wrap>
            {searchKeys.length ? (
              <Input
                allowClear
                prefix={<SearchOutlined />}
                placeholder="搜索"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                style={{ width: 220 }}
              />
            ) : null}
            <Button icon={<ReloadOutlined />} onClick={load}>
              刷新
            </Button>
            {extraToolbar}
            {canWrite && createItem ? (
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                新建
              </Button>
            ) : null}
          </Space>
        }
      />
      <Card bordered={false} styles={{ body: { padding: 0 } }}>
        <Table
          rowKey={rowKey}
          loading={loading}
          columns={fullColumns}
          dataSource={filtered}
          expandable={expandable}
          scroll={{ x: 'max-content' }}
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
        />
      </Card>

      <Modal
        open={modalOpen}
        title={editing ? `编辑${title}` : `新建${title}`}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        destroyOnClose
        width={640}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0 16px' }}>
            {formFields.map((f) => (
              <Form.Item
                key={f.name}
                name={f.name}
                label={f.label}
                rules={f.rules ?? (f.required ? [{ required: true, message: `请输入${f.label}` }] : undefined)}
                style={{ flex: f.span === 'full' ? '1 1 100%' : '1 1 45%', minWidth: 220 }}
              >
                {f.type === 'textarea' ? (
                  <Input.TextArea rows={3} placeholder={f.placeholder} />
                ) : f.type === 'number' ? (
                  <InputNumber style={{ width: '100%' }} placeholder={f.placeholder} min={f.min ?? 0} />
                ) : f.type === 'select' ? (
                  <Select options={f.options} placeholder={f.placeholder} allowClear />
                ) : f.type === 'date' ? (
                  <DatePicker style={{ width: '100%' }} />
                ) : (
                  <Input placeholder={f.placeholder} />
                )}
              </Form.Item>
            ))}
          </div>
        </Form>
      </Modal>
    </div>
  )
}
