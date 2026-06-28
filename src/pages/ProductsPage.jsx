import { Tag } from 'antd'
import ResourceTable from '../components/ResourceTable.jsx'
import { fetchProducts, createProduct, updateProduct, deleteProduct } from '../api.js'
import { useAuth, hasPermission } from '../auth/AuthContext.jsx'
import { formatCurrency } from '../constants.js'

const CATEGORIES = [
  { value: '硬件', label: '硬件' },
  { value: '软件', label: '软件' },
  { value: '服务', label: '服务' },
]

export default function ProductsPage() {
  const { permissions } = useAuth()
  const canWrite = hasPermission(permissions, 'catalog:manage')

  const columns = [
    { title: '产品', dataIndex: 'name', render: (v) => <strong>{v}</strong> },
    { title: 'SKU', dataIndex: 'sku' },
    { title: '类别', dataIndex: 'category', width: 90, render: (v) => <Tag>{v}</Tag> },
    { title: '单价', dataIndex: 'unit_price', align: 'right', render: (v) => formatCurrency(v) },
    {
      title: '库存',
      dataIndex: 'stock',
      align: 'right',
      width: 100,
      render: (v) => <span style={{ color: v < 60 ? '#F76C6C' : '#1F2A44', fontWeight: 600 }}>{v}</span>,
    },
  ]

  const formFields = [
    { name: 'name', label: '产品名称', required: true },
    { name: 'sku', label: 'SKU' },
    { name: 'category', label: '类别', type: 'select', options: CATEGORIES },
    { name: 'unit_price', label: '单价', type: 'number' },
    { name: 'stock', label: '库存', type: 'number' },
  ]

  return (
    <ResourceTable
      title="产品"
      subtitle="商品目录与库存"
      columns={columns}
      fetchList={fetchProducts}
      createItem={canWrite ? createProduct : undefined}
      updateItem={canWrite ? updateProduct : undefined}
      deleteItem={canWrite ? deleteProduct : undefined}
      formFields={formFields}
      canWrite={canWrite}
      searchKeys={['name', 'sku', 'category']}
    />
  )
}
