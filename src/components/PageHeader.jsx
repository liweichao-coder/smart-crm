import { Typography } from 'antd'

export default function PageHeader({ title, subtitle, extra }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        marginBottom: 16,
        gap: 16,
        flexWrap: 'wrap',
      }}
    >
      <div>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {title}
        </Typography.Title>
        {subtitle ? (
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            {subtitle}
          </Typography.Text>
        ) : null}
      </div>
      {extra ? <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>{extra}</div> : null}
    </div>
  )
}
