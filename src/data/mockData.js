import {
  Activity,
  Calendar,
  DollarSign,
  Flame,
  Percent,
  Phone,
  Sparkles,
  TrendingUp,
} from 'lucide-react'

export const orgs = [
  { id: 'org-1', name: '永酌公司', role: 'ADMIN' },
  { id: 'org-2', name: '南山科技', role: 'SALES' },
  { id: 'org-3', name: '北极星资本', role: 'MANAGER' },
]

export const focusItems = [
  { label: '今天截止', value: 3, href: '/tasks', icon: Calendar },
  { label: '需要电话跟进', value: 5, href: '/leads', icon: Phone },
  { label: '本周成交预测', value: '$98K', href: '/opportunities', icon: Sparkles },
]

export const pipelineCards = [
  { label: '勘探', count: 12, amount: 62000, tone: 'new' },
  { label: '资格确认', count: 8, amount: 138000, tone: 'qualified' },
  { label: '方案提案', count: 5, amount: 187000, tone: 'proposal' },
  { label: '商务谈判', count: 3, amount: 96000, tone: 'negotiation' },
  { label: '已成交', count: 4, amount: 142000, tone: 'won' },
]

export const dashboardMetrics = [
  { label: '管道价值', value: 483000, note: '全部商机总额', tone: 'accent', icon: DollarSign },
  { label: '加权管道', value: 276000, note: '按阶段概率折算', tone: 'proposal', icon: TrendingUp },
  { label: '本月赢单', value: 142000, note: '已成交金额', tone: 'won', icon: Flame },
  { label: '转化率', value: 36, note: '线索到成交', tone: 'qualified', icon: Percent, format: 'percent' },
]

export const dashboardStages = [
  { label: '勘探', amount: 62000, progress: 24, tone: 'new' },
  { label: '资格确认', amount: 138000, progress: 52, tone: 'qualified' },
  { label: '方案提案', amount: 187000, progress: 70, tone: 'proposal' },
  { label: '商务谈判', amount: 96000, progress: 36, tone: 'negotiation' },
]

export const hotLeads = [
  { id: 'hl-1', name: '李嘉然', company: '云舟智能', rating: 'hot' },
  { id: 'hl-2', name: '王思远', company: '拓海医疗', rating: 'warm' },
  { id: 'hl-3', name: '赵可', company: '峰值数据', rating: 'hot' },
]

export const taskCards = [
  { id: 'tc-1', title: '回访北极星资本', owner: '王蕾', dueLabel: '今天', tone: 'today' },
  { id: 'tc-2', title: '更新本周管道预测', owner: '陈卓', dueLabel: '本周', tone: 'week' },
  { id: 'tc-3', title: '补充商机合同信息', owner: '刘涵', dueLabel: '逾期', tone: 'overdue' },
]

export const accounts = [
  { id: 'acc-1', name: '永酌公司', industry: '制造业', owner: '王蕾', revenue: 860000, status: 'active' },
  { id: 'acc-2', name: '峰值数据', industry: '软件服务', owner: '陈卓', revenue: 530000, status: 'active' },
  { id: 'acc-3', name: '拓海医疗', industry: '医疗健康', owner: '赵可', revenue: 1180000, status: 'proposal' },
  { id: 'acc-4', name: '云舟智能', industry: '人工智能', owner: '刘涵', revenue: 760000, status: 'active' },
  { id: 'acc-5', name: '辰星物流', industry: '供应链', owner: '王蕾', revenue: 420000, status: 'closed' },
]

export const contacts = [
  { id: 'con-1', name: '李嘉然', company: '云舟智能', role: '采购总监', email: 'jran@yunzhou.ai', status: 'active' },
  { id: 'con-2', name: '王思远', company: '拓海医疗', role: '营运负责人', email: 'siyuan@tuohai.com', status: 'nurturing' },
  { id: 'con-3', name: '孙伊', company: '峰值数据', role: 'CEO', email: 'sunyi@fengzhi.cn', status: 'active' },
  { id: 'con-4', name: '吴青', company: '永酌公司', role: '行政负责人', email: 'wuqing@yongzhuo.com', status: 'active' },
  { id: 'con-5', name: '韩澈', company: '辰星物流', role: 'IT 经理', email: 'hanche@chenxing.io', status: 'closed' },
]

export const leads = [
  { id: 'lead-1', name: '李嘉然', company: '云舟智能', owner: '王蕾', nextStep: '安排产品演示', rating: 'hot', stage: 'New' },
  { id: 'lead-2', name: '韩知意', company: '北宸制造', owner: '刘涵', nextStep: '确认预算', rating: 'warm', stage: 'Qualified' },
  { id: 'lead-3', name: '许川', company: '拓海医疗', owner: '赵可', nextStep: '发送案例集', rating: 'warm', stage: 'Contacted' },
  { id: 'lead-4', name: '陈墨', company: '峰值数据', owner: '陈卓', nextStep: '提交报价单', rating: 'hot', stage: 'Proposal' },
  { id: 'lead-5', name: '林渡', company: '南山科技', owner: '王蕾', nextStep: '二次沟通需求', rating: 'cold', stage: 'New' },
  { id: 'lead-6', name: '沈听澜', company: '星火教育', owner: '赵可', nextStep: '讨论落地范围', rating: 'warm', stage: 'Qualified' },
]

export const opportunities = [
  { id: 'opp-1', name: '云舟年度 CRM 升级', account: '云舟智能', owner: '王蕾', amount: 98000, closeDate: '2026-04-20', stage: 'Prospecting' },
  { id: 'opp-2', name: '拓海销售自动化', account: '拓海医疗', owner: '赵可', amount: 154000, closeDate: '2026-04-28', stage: 'Qualification' },
  { id: 'opp-3', name: '峰值客户数据治理', account: '峰值数据', owner: '陈卓', amount: 83000, closeDate: '2026-05-02', stage: 'Proposal' },
  { id: 'opp-4', name: '永酌流程整合项目', account: '永酌公司', owner: '刘涵', amount: 126000, closeDate: '2026-05-10', stage: 'Negotiation' },
  { id: 'opp-5', name: '北宸售后工单系统', account: '北宸制造', owner: '王蕾', amount: 64000, closeDate: '2026-05-18', stage: 'Prospecting' },
  { id: 'opp-6', name: '辰星仓配看板', account: '辰星物流', owner: '赵可', amount: 71000, closeDate: '2026-05-21', stage: 'Proposal' },
]

export const supportCases = [
  { id: 'case-1', title: '导入联系人失败', account: '峰值数据', owner: '徐柠', priority: 'hot', status: 'open', statusLabel: 'Open' },
  { id: 'case-2', title: '移动端表格显示错位', account: '拓海医疗', owner: '顾川', priority: 'warm', status: 'working', statusLabel: 'Pending' },
  { id: 'case-3', title: '审批流通知延迟', account: '永酌公司', owner: '陆远', priority: 'hot', status: 'working', statusLabel: 'Pending' },
  { id: 'case-4', title: '权限组配置咨询', account: '云舟智能', owner: '徐柠', priority: 'cold', status: 'closed', statusLabel: 'Resolved' },
  { id: 'case-5', title: '工单 SLA 报表校对', account: '辰星物流', owner: '顾川', priority: 'warm', status: 'open', statusLabel: 'Open' },
]

export const taskItems = [
  { id: 'task-1', title: '回访云舟智能采购团队', description: '确认五月采购窗口与预算审批节奏。', owner: '王蕾', dueDate: '今天 18:00', priority: 'hot', status: 'today', statusLabel: '今天' },
  { id: 'task-2', title: '补充拓海医疗实施排期', description: '将实施节点同步到销售计划与商机详情。', owner: '赵可', dueDate: '明天 10:00', priority: 'warm', status: 'week', statusLabel: '本周' },
  { id: 'task-3', title: '整理峰值数据合同附件', description: '核对法务意见并更新签署版本。', owner: '陈卓', dueDate: '昨天 15:00', priority: 'hot', status: 'overdue', statusLabel: '逾期' },
  { id: 'task-4', title: '检查辰星物流工单报表', description: '修正筛选条件并补充导出字段。', owner: '刘涵', dueDate: '周四 11:00', priority: 'cold', status: 'week', statusLabel: '本周' },
  { id: 'task-5', title: '安排永酌公司需求研讨会', description: '同步销售、产品和实施的关键问题。', owner: '王蕾', dueDate: '今天 14:30', priority: 'warm', status: 'today', statusLabel: '今天' },
  { id: 'task-6', title: '复盘四月赢单策略', description: '输出下月复制打法。', owner: '陈卓', dueDate: '周五 17:00', priority: 'warm', status: 'week', statusLabel: '本周' },
]

export const goals = [
  { id: 'goal-1', name: 'Q2 新签 ARR', period: '2026 Q2', current: 388000, target: 520000, progress: 75, note: '距离季度目标还差 132K，重点依赖 3 个谈判中商机。' },
  { id: 'goal-2', name: '大客户续约率', period: '2026 Q2', current: 84, target: 92, progress: 91, note: '高于历史同期，需重点盯住 2 个高风险续约客户。' },
  { id: 'goal-3', name: '线索转商机率', period: '2026 Q2', current: 31, target: 40, progress: 77, note: '优化首轮跟进模板后，本月已连续两周提升。' },
]

export const activities = [
  { id: 'act-1', title: '云舟智能完成产品演示', description: '王蕾记录了 4 条新需求，商机金额提升到 98K。', time: '10 分钟前', icon: Activity },
  { id: 'act-2', title: '拓海医疗已进入资格确认', description: '赵可更新预算范围，并将预计成交时间调整到 4 月底。', time: '35 分钟前', icon: TrendingUp },
  { id: 'act-3', title: '峰值数据新增高优先级工单', description: '支持团队已接手导入失败问题，预计今天给出修复方案。', time: '1 小时前', icon: Flame },
]