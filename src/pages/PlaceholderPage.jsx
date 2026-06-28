import { Card, Empty } from 'antd'
import PageHeader from '../components/PageHeader.jsx'

export default function PlaceholderPage({ title }) {
  return (
    <div>
      <PageHeader title={title} subtitle="该模块正在接入中" />
      <Card bordered={false}>
        <Empty description={`${title} 页面即将上线`} />
      </Card>
    </div>
  )
}
