import { useState } from 'react'
import { App as AntApp, Button, Modal, Tag, Typography } from 'antd'
import { RobotOutlined } from '@ant-design/icons'
import ResourceTable from '../components/ResourceTable.jsx'
import { fetchLeads, createLead, updateLead, deleteLead, generateFollowUp } from '../api.js'
import { useAuth, hasPermission } from '../auth/AuthContext.jsx'
import { LEAD_STAGES, labelOf, colorOf, formatCurrency } from '../constants.js'
import { BRAND } from '../theme.js'

export default function LeadsPage() {
  const { permissions } = useAuth()
  const { message } = AntApp.useApp()
  const canWrite = hasPermission(permissions, 'crm:write')
  const canAi = hasPermission(permissions, 'ai:use')
  const [followUp, setFollowUp] = useState(null)
  const [loadingId, setLoadingId] = useState(null)

  const handleFollowUp = async (record) => {
    setLoadingId(record.id)
    try {
      const res = await generateFollowUp(record.id)
      setFollowUp({ lead: record, ...res })
    } catch (e) {
      message.error(e.message || 'AI 跟进生成失败')
    } finally {
      setLoadingId(null)
    }
  }

  const columns = [
    { title: '商机', dataIndex: 'title', render: (v, r) => (
      <strong>{v}{r.ai_assisted ? <Tag color={BRAND.primary} style={{ marginInlineStart: 6 }}>AI</Tag> : null}</strong>
    ) },
    { title: '客户', dataIndex: 'customer_name' },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    { title: '区域', dataIndex: 'region', width: 80 },
    { title: '阶段', dataIndex: 'stage', width: 110, render: (v) => <Tag color={colorOf(LEAD_STAGES, v)}>{labelOf(LEAD_STAGES, v)}</Tag> },
    { title: '预计金额', dataIndex: 'expected_amount', align: 'right', render: (v) => formatCurrency(v) },
    { title: '下一步', dataIndex: 'next_action', ellipsis: true },
    { title: '截止', dataIndex: 'due_date', width: 110 },
  ]

  const formFields = [
    { name: 'title', label: '商机名称', required: true, span: 'full' },
    { name: 'customer_name', label: '客户' },
    { name: 'owner', label: '负责人' },
    { name: 'region', label: '区域' },
    { name: 'stage', label: '阶段', type: 'select', options: LEAD_STAGES },
    { name: 'expected_amount', label: '预计金额', type: 'number' },
    { name: 'due_date', label: '截止日期', type: 'date' },
    { name: 'next_action', label: '下一步动作', type: 'textarea', span: 'full' },
  ]

  return (
    <>
      <ResourceTable
        title="商机"
        subtitle="销售管道与阶段流转（L2C 主链路）"
        columns={columns}
        fetchList={fetchLeads}
        createItem={canWrite ? createLead : undefined}
        updateItem={canWrite ? updateLead : undefined}
        deleteItem={canWrite ? deleteLead : undefined}
        formFields={formFields}
        canWrite={canWrite}
        searchKeys={['title', 'customer_name', 'owner', 'region']}
        extraActions={(record) =>
          canAi ? (
            <Button
              type="link"
              size="small"
              icon={<RobotOutlined />}
              loading={loadingId === record.id}
              onClick={() => handleFollowUp(record)}
            >
              AI 跟进
            </Button>
          ) : null
        }
      />
      <Modal
        open={Boolean(followUp)}
        title={<><RobotOutlined style={{ color: BRAND.primary }} /> AI 跟进建议 · {followUp?.lead?.title}</>}
        footer={<Button type="primary" onClick={() => setFollowUp(null)}>知道了</Button>}
        onCancel={() => setFollowUp(null)}
        width={620}
      >
        {followUp?.next_best_action ? (
          <div style={{ background: '#F5F8FF', borderRadius: 10, padding: 12, marginTop: 12 }}>
            <Typography.Text strong>下一步最佳动作</Typography.Text>
            <Typography.Paragraph style={{ marginBottom: 0, marginTop: 4 }}>{followUp.next_best_action}</Typography.Paragraph>
          </div>
        ) : null}
        <Typography.Text strong style={{ display: 'block', marginTop: 14 }}>跟进话术草稿</Typography.Text>
        <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginTop: 4 }}>
          {followUp?.message_draft || followUp?.llm_summary || '（无内容）'}
        </Typography.Paragraph>
        {followUp?.fallback_used ? (
          <Tag color="orange">本地降级生成（未调用大模型）</Tag>
        ) : (
          <Tag color="green">DeepSeek 实时生成</Tag>
        )}
      </Modal>
    </>
  )
}
