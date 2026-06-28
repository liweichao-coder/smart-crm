import { Tag } from 'antd'
import ResourceTable from '../components/ResourceTable.jsx'
import { fetchCustomers, createCustomer, updateCustomer, deleteCustomer } from '../api.js'
import { useAuth, hasPermission } from '../auth/AuthContext.jsx'
import { CUSTOMER_STATUS, labelOf, colorOf, formatCurrency } from '../constants.js'

const LEVELS = [
  { value: 'S', label: 'S 级' },
  { value: 'A', label: 'A 级' },
  { value: 'B', label: 'B 级' },
  { value: 'C', label: 'C 级' },
]

export default function CustomersPage() {
  const { permissions } = useAuth()
  const canWrite = hasPermission(permissions, 'crm:write')

  const columns = [
    { title: '客户', dataIndex: 'company', render: (v, r) => <strong>{v || r.name}</strong> },
    { title: '联系人', dataIndex: 'contact_person' },
    { title: '行业', dataIndex: 'industry' },
    { title: '城市', dataIndex: 'city', width: 80 },
    { title: '等级', dataIndex: 'level', width: 70, render: (v) => <Tag color="blue">{v}</Tag> },
    { title: '年营收', dataIndex: 'annual_revenue', align: 'right', render: (v) => formatCurrency(v) },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    { title: '来源', dataIndex: 'source' },
    { title: '状态', dataIndex: 'status', width: 100, render: (v) => <Tag color={colorOf(CUSTOMER_STATUS, v)}>{labelOf(CUSTOMER_STATUS, v)}</Tag> },
    { title: '电话', dataIndex: 'phone', width: 120 },
  ]

  const formFields = [
    { name: 'name', label: '客户名称', required: true },
    { name: 'company', label: '公司' },
    { name: 'industry', label: '行业' },
    { name: 'city', label: '城市' },
    { name: 'contact_person', label: '联系人' },
    { name: 'phone', label: '电话' },
    { name: 'email', label: '邮箱' },
    { name: 'source', label: '来源' },
    { name: 'level', label: '等级', type: 'select', options: LEVELS },
    { name: 'annual_revenue', label: '年营收', type: 'number' },
    { name: 'status', label: '状态', type: 'select', options: CUSTOMER_STATUS },
    { name: 'owner', label: '负责人' },
  ]

  return (
    <ResourceTable
      title="客户"
      subtitle="客户资产沉淀与分级管理"
      columns={columns}
      fetchList={fetchCustomers}
      createItem={canWrite ? createCustomer : undefined}
      updateItem={canWrite ? updateCustomer : undefined}
      deleteItem={canWrite ? deleteCustomer : undefined}
      formFields={formFields}
      canWrite={canWrite}
      searchKeys={['name', 'company', 'contact_person', 'industry', 'city', 'owner']}
    />
  )
}
