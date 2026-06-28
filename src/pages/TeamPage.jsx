import { Tag } from 'antd'
import ResourceTable from '../components/ResourceTable.jsx'
import { fetchTeamMembers, createTeamMember, updateTeamMember } from '../api.js'
import { useAuth, hasPermission } from '../auth/AuthContext.jsx'

const ROLES = [
  { value: '管理员', label: '管理员' },
  { value: '销售经理', label: '销售经理' },
  { value: '销售', label: '销售' },
  { value: '支持', label: '支持' },
  { value: '审计员', label: '审计员' },
]
const SCOPES = [
  { value: 'all', label: '全部数据' },
  { value: 'own', label: '本人数据' },
]
const STATUS = [
  { value: 'active', label: '在职', color: 'green' },
  { value: 'inactive', label: '停用', color: 'default' },
]

export default function TeamPage() {
  const { permissions } = useAuth()
  const canWrite = hasPermission(permissions, 'team:manage')

  const columns = [
    { title: '姓名', dataIndex: 'full_name', render: (v) => <strong>{v}</strong> },
    { title: '邮箱', dataIndex: 'email' },
    { title: '电话', dataIndex: 'phone', width: 130 },
    { title: '角色', dataIndex: 'role', width: 100, render: (v) => <Tag color="blue">{v}</Tag> },
    { title: '部门', dataIndex: 'department' },
    { title: '岗位', dataIndex: 'position' },
    { title: '数据范围', dataIndex: 'data_scope', width: 100, render: (v) => (v === 'all' ? '全部数据' : '本人数据') },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v) => {
        const s = STATUS.find((i) => i.value === v)
        return <Tag color={s?.color ?? 'default'}>{s?.label ?? v}</Tag>
      },
    },
    { title: '最近登录', dataIndex: 'last_login_at', width: 160, render: (v) => (v ? new Date(v).toLocaleString('zh-CN') : '—') },
  ]

  const formFields = [
    { name: 'full_name', label: '姓名', required: true },
    { name: 'email', label: '邮箱', required: true },
    { name: 'phone', label: '电话' },
    { name: 'password', label: '初始密码', required: true, placeholder: '至少 8 位' },
    { name: 'role', label: '角色', type: 'select', options: ROLES, required: true },
    { name: 'data_scope', label: '数据范围', type: 'select', options: SCOPES },
    { name: 'position', label: '岗位' },
    { name: 'department', label: '部门' },
    { name: 'status', label: '状态', type: 'select', options: STATUS },
  ]

  return (
    <ResourceTable
      title="团队成员"
      subtitle="销售人员与角色权限管理（RBAC）"
      columns={columns}
      fetchList={fetchTeamMembers}
      createItem={canWrite ? createTeamMember : undefined}
      updateItem={canWrite ? updateTeamMember : undefined}
      formFields={formFields}
      canWrite={canWrite}
      searchKeys={['full_name', 'email', 'role', 'department']}
    />
  )
}
