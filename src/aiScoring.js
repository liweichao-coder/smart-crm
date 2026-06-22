const stageWeights = {
  Prospecting: 12,
  Qualification: 28,
  Proposal: 48,
  Negotiation: 68,
  Won: 92,
}

const actionByStage = {
  Prospecting: '补齐预算、决策人和采购时间线',
  Qualification: '确认痛点强度并安排方案演示',
  Proposal: '发送 ROI 测算并推动试点范围确认',
  Negotiation: '准备让步边界和合同风险清单',
  Won: '沉淀复盘材料并触发续约计划',
}

export function calculateOpportunityScore(opportunity) {
  const stageScore = stageWeights[opportunity.stage] ?? 18
  const amountScore = Math.min(Math.round((opportunity.amount ?? 0) / 4000), 24)
  const urgencyScore = opportunity.closeDate <= '2026-05-10' ? 12 : 6
  return Math.min(stageScore + amountScore + urgencyScore, 99)
}

export function getOpportunityGrade(score) {
  if (score >= 86) {
    return 'A'
  }
  if (score >= 68) {
    return 'B'
  }
  if (score >= 48) {
    return 'C'
  }
  return 'D'
}

export function createOpportunityInsight(opportunity) {
  const score = calculateOpportunityScore(opportunity)
  const grade = getOpportunityGrade(score)

  return {
    ...opportunity,
    score,
    grade,
    winRate: `${Math.max(18, Math.min(score - 8, 88))}%`,
    nextBestAction: actionByStage[opportunity.stage] ?? '补充关键客户信息并生成跟进计划',
  }
}

export function rankOpportunityInsights(opportunities) {
  return opportunities.map(createOpportunityInsight).sort((left, right) => right.score - left.score)
}

export function summarizeCopilot(insights) {
  const topInsight = insights[0]
  const atRiskCount = insights.filter((item) => item.grade === 'D' || item.score < 50).length
  const forecastAmount = insights
    .filter((item) => item.grade === 'A' || item.grade === 'B')
    .reduce((total, item) => total + item.amount, 0)

  return {
    topInsight,
    atRiskCount,
    forecastAmount,
    recommendation:
      atRiskCount > 0
        ? '先处理低分商机的信息缺口，再推进 A/B 级商机的成交动作。'
        : '当前商机质量较稳，建议集中资源推动高分商机进入合同阶段。',
  }
}
