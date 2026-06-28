import { BRAND } from '../theme.js'

const PALETTE = ['#2B54E6', '#5B8DEF', '#36C5A8', '#F7A23B', '#9254DE', '#F76C6C', '#52A0FF']

// 柱状图：data = [{ label, value }]
export function BarChart({ data = [], height = 220, color = BRAND.primary, valueFormatter }) {
  if (!data.length) return <Empty />
  const max = Math.max(...data.map((d) => d.value), 1)
  const fmt = valueFormatter ?? ((v) => v)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, height, padding: '8px 4px' }}>
      {data.map((d) => {
        const h = Math.max((d.value / max) * (height - 48), 2)
        return (
          <div key={d.label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 12, color: '#5B6B86', fontWeight: 600 }}>{fmt(d.value)}</span>
            <div
              title={`${d.label}: ${fmt(d.value)}`}
              style={{
                width: '70%',
                maxWidth: 48,
                height: h,
                borderRadius: '6px 6px 0 0',
                background: `linear-gradient(180deg, ${color} 0%, ${BRAND.primaryHover} 100%)`,
                transition: 'height .4s ease',
              }}
            />
            <span style={{ fontSize: 12, color: '#8694AD' }}>{d.label}</span>
          </div>
        )
      })}
    </div>
  )
}

// 折线图（面积）：data = [{ label, value }]
export function LineChart({ data = [], height = 220, valueFormatter }) {
  if (data.length < 2) return <Empty />
  const w = 520
  const pad = 28
  const max = Math.max(...data.map((d) => d.value), 1)
  const min = Math.min(...data.map((d) => d.value), 0)
  const span = max - min || 1
  const stepX = (w - pad * 2) / (data.length - 1)
  const y = (v) => height - pad - ((v - min) / span) * (height - pad * 2)
  const pts = data.map((d, i) => [pad + i * stepX, y(d.value)])
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' ')
  const area = `${line} L${pts[pts.length - 1][0]},${height - pad} L${pad},${height - pad} Z`
  const fmt = valueFormatter ?? ((v) => v)
  return (
    <svg viewBox={`0 0 ${w} ${height}`} style={{ width: '100%', height }}>
      <defs>
        <linearGradient id="lc" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={BRAND.primary} stopOpacity="0.28" />
          <stop offset="1" stopColor={BRAND.primary} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#lc)" />
      <path d={line} fill="none" stroke={BRAND.primary} strokeWidth="2.5" strokeLinecap="round" />
      {pts.map((p, i) => (
        <g key={data[i].label}>
          <circle cx={p[0]} cy={p[1]} r="4" fill="#fff" stroke={BRAND.primary} strokeWidth="2" />
          <text x={p[0]} y={height - 8} textAnchor="middle" fontSize="11" fill="#8694AD">{data[i].label}</text>
          <text x={p[0]} y={p[1] - 10} textAnchor="middle" fontSize="11" fontWeight="600" fill="#5B6B86">{fmt(data[i].value)}</text>
        </g>
      ))}
    </svg>
  )
}

// 环形图：data = [{ label, value }]
export function DonutChart({ data = [], size = 180 }) {
  const total = data.reduce((s, d) => s + d.value, 0)
  if (!total) return <Empty />
  const r = size / 2
  const stroke = 26
  const ir = r - stroke / 2
  const circ = 2 * Math.PI * ir
  let offset = 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <g transform={`rotate(-90 ${r} ${r})`}>
          {data.map((d, i) => {
            const frac = d.value / total
            const dash = frac * circ
            const seg = (
              <circle
                key={d.label}
                cx={r}
                cy={r}
                r={ir}
                fill="none"
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={stroke}
                strokeDasharray={`${dash} ${circ - dash}`}
                strokeDashoffset={-offset}
              />
            )
            offset += dash
            return seg
          })}
        </g>
        <text x={r} y={r - 4} textAnchor="middle" fontSize="22" fontWeight="700" fill="#1F2A44">{total}</text>
        <text x={r} y={r + 16} textAnchor="middle" fontSize="12" fill="#8694AD">合计</text>
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {data.map((d, i) => (
          <div key={d.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <span style={{ width: 10, height: 10, borderRadius: 3, background: PALETTE[i % PALETTE.length] }} />
            <span style={{ color: '#5B6B86', minWidth: 88 }}>{d.label}</span>
            <span style={{ fontWeight: 600, color: '#1F2A44' }}>{d.value}</span>
            <span style={{ color: '#A0AABE' }}>{Math.round((d.value / total) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Empty() {
  return <div style={{ color: '#A0AABE', fontSize: 13, padding: 24, textAlign: 'center' }}>暂无数据</div>
}
