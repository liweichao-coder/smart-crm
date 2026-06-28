import { Tag } from 'antd'
import ResourceTable from '../components/ResourceTable.jsx'
import { fetchContacts, createContact, updateContact, deleteContact } from '../api.js'
import { useAuth, hasPermission } from '../auth/AuthContext.jsx'

const STATUS = [
  { value: 'active', label: '活跃', color: 'green' },
  { value: 'nurturing', label: '培育中', color: 'blue' },
  { value: 'closed', label: '已关闭', color: 'default' },
]

export default function ContactsPage() {
  const { permissions } = useAuth()
  const canWrite = hasPermission(permissions, 'crm:write')

  const columns = [
    { title: '姓名', dataIndex: 'name', render: (v) => <strong>{v}</strong> },
    { title: '公司', dataIndex: 'company' },
    { title: '职务', dataIndex: 'role' },
    { title: '电话', dataIndex: 'phone', width: 130 },
    { title: '邮箱', dataIndex: 'email' },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v) => {
        const s = STATUS.find((i) => i.value === v)
        return <Tag color={s?.color ?? 'default'}>{s?.label ?? v}</Tag>
      },
    },
  ]

  const formFields = [
    { name: 'name', label: '姓名', required: true },
    { name: 'company', label: '公司' },
    { name: 'role', label: '职务' },
    { name: 'phone', label: '电话' },
    { name: 'email', label: '邮箱' },
    { name: 'owner', label: '负责人' },
    { name: 'status', label: '状态', type: 'select', options: STATUS },
  ]

  return (
    <ResourceTable
      title="联系人"
      subtitle="关键决策人与对接人维护"
      columns={columns}
      fetchList={fetchContacts}
      createItem={canWrite ? createContact : undefined}
      updateItem={canWrite ? updateContact : undefined}
      deleteItem={canWrite ? deleteContact : undefined}
      formFields={formFields}
      canWrite={canWrite}
      searchKeys={['name', 'company', 'role', 'owner']}
    />
  )
}
