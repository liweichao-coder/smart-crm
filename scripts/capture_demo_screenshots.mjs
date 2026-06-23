import { mkdir, readdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const DEFAULT_FRONTEND_URL = 'http://127.0.0.1:5173'
const DEFAULT_API_URL = 'http://127.0.0.1:8000'
const DEFAULT_ACCOUNT = 'demo@smart-crm.local'
const DEFAULT_PASSWORD = 'SmartCRM@2026'
const AUTH_STORAGE_KEY = 'smart-crm:auth-session'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(scriptDir, '..')
const defaultOutputDir = path.resolve(repoRoot, '..', '报告文档', 'v2-最终高分版', '正式文档', '截图')

class CaptureFailure extends Error {}

function parseArgs(argv) {
  const args = {
    frontendUrl: process.env.SMART_CRM_CAPTURE_FRONTEND_URL || DEFAULT_FRONTEND_URL,
    apiUrl: process.env.SMART_CRM_CAPTURE_API_URL || DEFAULT_API_URL,
    outputDir: process.env.SMART_CRM_CAPTURE_OUTPUT_DIR || defaultOutputDir,
    account: process.env.SMART_CRM_CAPTURE_ACCOUNT || DEFAULT_ACCOUNT,
    password: process.env.SMART_CRM_CAPTURE_PASSWORD || DEFAULT_PASSWORD,
    channel: process.env.SMART_CRM_CAPTURE_CHANNEL || 'chrome',
    timeout: Number(process.env.SMART_CRM_CAPTURE_TIMEOUT || 20000),
    headed: false,
    clearOutput: false,
    includeAi: false,
  }

  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index]
    const next = argv[index + 1]
    if (key === '--frontend-url' && next) {
      args.frontendUrl = next
      index += 1
    } else if (key === '--api-url' && next) {
      args.apiUrl = next
      index += 1
    } else if (key === '--output-dir' && next) {
      args.outputDir = next
      index += 1
    } else if (key === '--account' && next) {
      args.account = next
      index += 1
    } else if (key === '--password' && next) {
      args.password = next
      index += 1
    } else if (key === '--channel' && next !== undefined) {
      args.channel = next
      index += 1
    } else if (key === '--timeout' && next) {
      args.timeout = Number(next)
      index += 1
    } else if (key === '--headed') {
      args.headed = true
    } else if (key === '--clear-output') {
      args.clearOutput = true
    } else if (key === '--include-ai') {
      args.includeAi = true
    } else if (key === '--help' || key === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new CaptureFailure(`Unknown argument: ${key}`)
    }
  }

  args.frontendUrl = args.frontendUrl.replace(/\/$/, '')
  args.apiUrl = args.apiUrl.replace(/\/$/, '')
  args.outputDir = path.resolve(args.outputDir)
  if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
    throw new CaptureFailure('--timeout must be a positive number.')
  }
  return args
}

function printHelp() {
  console.log(`Capture Smart CRM demo screenshots from a running frontend/backend.

Usage:
  npm run screenshots:demo -- --frontend-url http://127.0.0.1:5173 --api-url http://127.0.0.1:8000 --clear-output --include-ai

Options:
  --frontend-url URL     Running Vite frontend URL. Default: ${DEFAULT_FRONTEND_URL}
  --api-url URL          Running FastAPI backend URL. Default: ${DEFAULT_API_URL}
  --output-dir DIR       Screenshot output directory. Default: ${defaultOutputDir}
  --account EMAIL        Login account. Default: ${DEFAULT_ACCOUNT}
  --password PASSWORD    Login password. Defaults to the demo password.
  --channel NAME         Playwright browser channel. Default: chrome
  --timeout MS           Per-action timeout. Default: 20000
  --headed               Show the browser window.
  --clear-output         Remove existing .png and screenshot index files in the output directory first.
  --include-ai           Also capture AI Copilot and AI audit pages. This may trigger LLM/recommendation writes.
`)
}

function expect(condition, message) {
  if (!condition) {
    throw new CaptureFailure(message)
  }
}

async function assertHealth(apiUrl, timeout) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(`${apiUrl}/api/health`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    expect(response.ok, `/api/health returned ${response.status}.`)
    const health = await response.json()
    expect(health.status === 'ok', `/api/health status is ${health.status}.`)
    expect(health.database?.connected === true, 'Database readiness is not connected.')
    expect(health.consistency?.issue_count === 0, 'Consistency readiness has issues.')
    expect(!JSON.stringify(health).includes('sk-'), '/api/health leaked an API-key-like token.')
    return health
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new CaptureFailure(`/api/health timed out after ${timeout}ms.`)
    }
    if (error instanceof CaptureFailure) {
      throw error
    }
    throw new CaptureFailure(`/api/health failed: ${error.message}`)
  } finally {
    clearTimeout(timer)
  }
}

async function launchBrowser(args) {
  const options = { headless: !args.headed }
  if (args.channel) {
    try {
      return await chromium.launch({ ...options, channel: args.channel })
    } catch (error) {
      console.warn(`SCREENSHOT WARNING: browser channel "${args.channel}" failed: ${error.message}`)
    }
  }
  return chromium.launch(options)
}

async function prepareOutputDir(outputDir, clearOutput) {
  await mkdir(outputDir, { recursive: true })
  if (!clearOutput) {
    return
  }
  const entries = await readdir(outputDir, { withFileTypes: true })
  await Promise.all(entries
    .filter((entry) => entry.isFile() && (entry.name.toLowerCase().endsWith('.png') || entry.name === '00_screenshot_index.md'))
    .map((entry) => rm(path.join(outputDir, entry.name), { force: true })))
}

async function expectVisible(locator, label) {
  await locator.waitFor({ state: 'visible' }).catch((error) => {
    throw new CaptureFailure(`${label} was not visible: ${error.message}`)
  })
}

async function waitForShellIdle(page) {
  await page.waitForLoadState('networkidle').catch(() => undefined)
  await page.waitForTimeout(400)
}

async function capture(page, outputDir, fileName, label, records) {
  await waitForShellIdle(page)
  const filePath = path.join(outputDir, fileName)
  await page.screenshot({ path: filePath, fullPage: false })
  records.push({ fileName, label, url: page.url() })
  return filePath
}

async function getAuthToken(page) {
  const raw = await page.evaluate((key) => window.localStorage.getItem(key), AUTH_STORAGE_KEY)
  if (!raw) {
    throw new CaptureFailure('Auth session is missing from localStorage.')
  }
  const session = JSON.parse(raw)
  if (!session?.token) {
    throw new CaptureFailure('Auth session token is missing.')
  }
  return session.token
}

function payloadItems(payload) {
  if (Array.isArray(payload)) {
    return payload
  }
  if (Array.isArray(payload?.items)) {
    return payload.items
  }
  return []
}

async function apiGet(apiUrl, token, pathName) {
  const response = await fetch(`${apiUrl}${pathName}`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new CaptureFailure(`GET ${pathName} returned ${response.status}: ${detail}`)
  }
  return response.json()
}

async function firstCustomerId(apiUrl, token) {
  const payload = await apiGet(apiUrl, token, '/api/customers?page=1&per_page=1')
  const [customer] = payloadItems(payload)
  if (!customer?.id) {
    throw new CaptureFailure('No customer was available for Customer 360 screenshot.')
  }
  return customer.id
}

async function runCapture(args) {
  await prepareOutputDir(args.outputDir, args.clearOutput)
  await assertHealth(args.apiUrl, args.timeout)

  const browser = await launchBrowser(args)
  const context = await browser.newContext({
    baseURL: args.frontendUrl,
    viewport: { width: 1440, height: 1000 },
  })
  context.setDefaultTimeout(args.timeout)
  const page = await context.newPage()
  const records = []

  try {
    await page.goto('/login')
    await expectVisible(page.locator('.crm-auth-panel').first(), 'login panel')
    await capture(page, args.outputDir, '01_login.png', '登录页：深大徽标与浅色认证入口', records)

    await page.locator('input[autocomplete="username"]').fill(args.account)
    await page.locator('input[autocomplete="current-password"]').fill(args.password)
    await page.getByRole('button', { name: /^登录/ }).click()
    await page.waitForURL('**/org')
    await expectVisible(page.getByRole('heading', { name: /选择一个组织/ }).first(), 'organization page')
    await capture(page, args.outputDir, '02_organization.png', '组织选择页：后端组织和角色', records)

    await page.locator('.crm-org-card').first().click()
    await page.waitForURL('**/dashboard')
    await expectVisible(page.getByRole('heading', { name: /仪表盘/ }).first(), 'dashboard page')
    await capture(page, args.outputDir, '03_dashboard.png', '仪表盘：真实 KPI、阶段和任务聚合', records)

    await page.getByRole('button', { name: '通知' }).click()
    await expectVisible(page.locator('.crm-notification-panel'), 'notification center')
    await capture(page, args.outputDir, '04_notifications.png', '通知中心：任务、库存、审批和 AI 提醒', records)

    await page.goto('/accounts')
    await expectVisible(page.getByRole('heading', { name: /客户/ }).first(), 'accounts page')
    await expectVisible(page.locator('.crm-table tbody tr').first(), 'accounts first row')
    await capture(page, args.outputDir, '05_accounts.png', '客户列表：真实客户主数据和操作入口', records)

    const token = await getAuthToken(page)
    const customerId = await firstCustomerId(args.apiUrl, token)
    await page.goto(`/accounts/${customerId}`)
    await expectVisible(page.getByText('客户健康画像').first(), 'customer health profile')
    await capture(page, args.outputDir, '06_customer_360.png', '客户 360：健康画像、经营计划和时间线', records)

    await page.goto('/orders')
    await expectVisible(page.getByRole('heading', { name: /订单中心/ }).first(), 'orders page')
    await capture(page, args.outputDir, '07_orders.png', '订单中心：订单、审批、库存和流水', records)

    await page.goto('/reports')
    await expectVisible(page.getByRole('heading', { name: /销售报表/ }).first(), 'reports page')
    await capture(page, args.outputDir, '08_reports.png', '销售报表：真实聚合与快照历史', records)

    await page.goto('/permissions')
    await expectVisible(page.getByRole('heading', { name: /权限矩阵/ }).first(), 'permission matrix page')
    await capture(page, args.outputDir, '09_permissions.png', '权限矩阵：RBAC 和数据范围', records)

    await page.goto('/business-audit')
    await expectVisible(page.getByRole('heading', { name: /操作审计/ }).first(), 'business audit page')
    await capture(page, args.outputDir, '10_business_audit.png', '操作审计：写库动作和一致性巡检', records)

    if (args.includeAi) {
      await page.goto('/copilot')
      await expectVisible(page.getByRole('heading', { name: /AI 副驾/ }).first(), 'copilot page')
      await capture(page, args.outputDir, '11_ai_copilot.png', 'AI 副驾：评分、话术、推荐历史和反馈', records)

      await page.goto('/ai-audit')
      await expectVisible(page.getByRole('heading', { name: /AI 审计/ }).first(), 'ai audit page')
      await capture(page, args.outputDir, '12_ai_audit.png', 'AI 审计：模型调用、质量指标和兜底记录', records)
    }

    await page.goto('/profile')
    await expectVisible(page.getByRole('heading', { name: /个人主页|李伟超|演示管理员/ }).first(), 'profile page')
    await capture(page, args.outputDir, '13_profile_sessions.png', '个人主页：资料维护和登录会话管理', records)

    await writeIndex(args.outputDir, records, args)
  } finally {
    await context.close()
    await browser.close()
  }

  return records
}

async function writeIndex(outputDir, records, args) {
  const lines = [
    '# Smart CRM Demo Screenshots',
    '',
    `- Captured at: ${new Date().toISOString()}`,
    `- Frontend: ${args.frontendUrl}`,
    `- API: ${args.apiUrl}`,
    `- Include AI pages: ${args.includeAi ? 'yes' : 'no'}`,
    '',
    '| File | Purpose | URL |',
    '|---|---|---|',
    ...records.map((record) => `| ${record.fileName} | ${record.label} | ${record.url} |`),
    '',
  ]
  await writeFile(path.join(outputDir, '00_screenshot_index.md'), lines.join('\n'), 'utf8')
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const records = await runCapture(args)
  console.log(`Captured ${records.length} Smart CRM screenshots into ${args.outputDir}.`)
  for (const record of records) {
    console.log(`- ${record.fileName}: ${record.label}`)
  }
}

main().catch((error) => {
  const message = error instanceof CaptureFailure ? error.message : error.stack || error.message
  console.error(`SCREENSHOT CAPTURE FAILED: ${message}`)
  process.exit(1)
})
