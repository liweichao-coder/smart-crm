import assert from 'node:assert/strict'
import test from 'node:test'

import {
  calculateOpportunityScore,
  createOpportunityInsight,
  getOpportunityGrade,
  rankOpportunityInsights,
  summarizeCopilot,
} from './aiScoring.js'

test('calculateOpportunityScore combines stage, amount, and urgency', () => {
  const score = calculateOpportunityScore({
    amount: 98000,
    closeDate: '2026-05-02',
    stage: 'Proposal',
  })

  assert.equal(score, 84)
})

test('createOpportunityInsight adds explainable AI fields', () => {
  const insight = createOpportunityInsight({
    id: 'opp-1',
    name: '云舟年度 CRM 升级',
    amount: 98000,
    closeDate: '2026-05-02',
    stage: 'Proposal',
  })

  assert.equal(insight.grade, 'B')
  assert.equal(insight.winRate, '76%')
  assert.match(insight.nextBestAction, /ROI/)
})

test('rankOpportunityInsights sorts high-value late-stage deals first', () => {
  const insights = rankOpportunityInsights([
    { id: 'a', name: '早期商机', amount: 62000, closeDate: '2026-05-20', stage: 'Prospecting' },
    { id: 'b', name: '谈判商机', amount: 126000, closeDate: '2026-05-08', stage: 'Negotiation' },
  ])

  assert.equal(insights[0].id, 'b')
})

test('summarizeCopilot returns forecast and risk summary', () => {
  const summary = summarizeCopilot(
    rankOpportunityInsights([
      { id: 'a', name: '早期商机', amount: 62000, closeDate: '2026-05-20', stage: 'Prospecting' },
      { id: 'b', name: '谈判商机', amount: 126000, closeDate: '2026-05-08', stage: 'Negotiation' },
    ]),
  )

  assert.equal(summary.topInsight.id, 'b')
  assert.equal(summary.forecastAmount, 126000)
  assert.equal(summary.atRiskCount, 1)
})

test('getOpportunityGrade maps score bands', () => {
  assert.equal(getOpportunityGrade(90), 'A')
  assert.equal(getOpportunityGrade(70), 'B')
  assert.equal(getOpportunityGrade(50), 'C')
  assert.equal(getOpportunityGrade(30), 'D')
})
