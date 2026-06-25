import { chromium } from 'playwright'

const DEFAULT_FRONTEND_URL = 'http://127.0.0.1:5173'
const DEFAULT_API_URL = 'http://127.0.0.1:8000'
const DEFAULT_ACCOUNT = 'demo@smart-crm.local'
const DEFAULT_PASSWORD = 'SmartCRM@2026'

class SmokeFailure extends Error {}

function parseArgs(argv) {
  const args = {
    frontendUrl: process.env.SMART_CRM_UI_SMOKE_FRONTEND_URL || DEFAULT_FRONTEND_URL,
    apiUrl: process.env.SMART_CRM_UI_SMOKE_API_URL || DEFAULT_API_URL,
    account: process.env.SMART_CRM_UI_SMOKE_ACCOUNT || DEFAULT_ACCOUNT,
    password: process.env.SMART_CRM_UI_SMOKE_PASSWORD || DEFAULT_PASSWORD,
    channel: process.env.SMART_CRM_UI_SMOKE_CHANNEL || 'chrome',
    timeout: Number(process.env.SMART_CRM_UI_SMOKE_TIMEOUT || 15000),
    headed: false,
    includeAiPage: false,
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
    } else if (key === '--include-ai-page') {
      args.includeAiPage = true
    } else if (key === '--help' || key === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new SmokeFailure(`Unknown argument: ${key}`)
    }
  }

  args.frontendUrl = args.frontendUrl.replace(/\/$/, '')
  args.apiUrl = args.apiUrl.replace(/\/$/, '')
  if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
    throw new SmokeFailure('--timeout must be a positive number.')
  }
  return args
}

function printHelp() {
  console.log(`Run Smart CRM browser UI smoke checks.

Usage:
  npm run smoke:ui -- --frontend-url http://127.0.0.1:5173 --api-url http://127.0.0.1:8000

Options:
  --frontend-url URL     Running Vite frontend URL. Default: ${DEFAULT_FRONTEND_URL}
  --api-url URL          Running FastAPI backend URL. Default: ${DEFAULT_API_URL}
  --account EMAIL        Login account. Default: ${DEFAULT_ACCOUNT}
  --password PASSWORD    Login password. Defaults to the demo password.
  --channel NAME         Playwright browser channel. Default: chrome
  --timeout MS           Per-action timeout. Default: 15000
  --headed               Show the browser window.
  --include-ai-page      Also visit /copilot. This may trigger LLM-backed reads/writes.
`)
}

function expect(condition, message) {
  if (!condition) {
    throw new SmokeFailure(message)
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
      throw new SmokeFailure(`/api/health timed out after ${timeout}ms.`)
    }
    if (error instanceof SmokeFailure) {
      throw error
    }
    throw new SmokeFailure(`/api/health failed: ${error.message}`)
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
      console.warn(`UI SMOKE WARNING: browser channel "${args.channel}" failed: ${error.message}`)
    }
  }
  return chromium.launch(options)
}

async function expectVisible(locator, label) {
  await locator.waitFor({ state: 'visible' }).catch((error) => {
    throw new SmokeFailure(`${label} was not visible: ${error.message}`)
  })
}

async function assertNoHorizontalOverflow(page, label) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
  expect(!overflow, `${label} has horizontal overflow.`)
}

async function assertRoute(page, path, headingPattern, label) {
  await page.goto(path)
  await expectVisible(page.getByRole('heading', { name: headingPattern }).first(), `${label} heading`)
  await assertNoHorizontalOverflow(page, label)
}

async function runUiSmoke(args) {
  const passed = []
  const health = await assertHealth(args.apiUrl, args.timeout)
  passed.push(`readiness:${health.status}`)

  const browser = await launchBrowser(args)
  const context = await browser.newContext({
    baseURL: args.frontendUrl,
    viewport: { width: 1440, height: 1000 },
  })
  context.setDefaultTimeout(args.timeout)
  const page = await context.newPage()
  const nativeDialogs = []
  const pageErrors = []
  const consoleErrors = []

  page.on('dialog', async (dialog) => {
    nativeDialogs.push(dialog.type())
    await dialog.dismiss()
  })
  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  try {
    await page.goto('/login')
    await expectVisible(page.locator('.crm-brand-mark').first(), 'brand emblem')
    const authPanelRadius = await page.locator('.crm-auth-panel').first().evaluate((node) => getComputedStyle(node).borderRadius)
    expect(authPanelRadius === '8px', `Login panel radius should be 8px, got ${authPanelRadius}.`)
    await assertNoHorizontalOverflow(page, 'login')
    passed.push('login-style')

    await page.locator('input[autocomplete="username"]').fill(args.account)
    await page.locator('input[autocomplete="current-password"]').fill(args.password)
    await page.getByRole('button', { name: /^登录/ }).click()
    await page.waitForURL('**/org')
    await expectVisible(page.getByRole('heading', { name: /选择一个组织/ }).first(), 'organization heading')
    await page.locator('.crm-org-card').first().click()
    await page.waitForURL('**/dashboard')
    passed.push('login-and-org')

    await expectVisible(page.getByRole('heading', { name: /演示工作台/ }).first(), 'dashboard heading')
    await expectVisible(page.locator('.crm-data-overview-card').first(), 'dashboard data overview card')
    const metricCount = await page.locator('.crm-data-overview-card').count()
    expect(metricCount >= 4, `Dashboard should render at least 4 data overview cards, got ${metricCount}.`)
    await assertNoHorizontalOverflow(page, 'dashboard')
    passed.push('dashboard')

    await assertRoute(page, '/accounts', /客户/, 'accounts')
    await expectVisible(page.locator('.crm-table tbody tr').first(), 'accounts first row')
    const rowsBefore = await page.locator('.crm-table tbody tr').count()
    expect(rowsBefore > 0, 'Accounts table should render at least one row.')
    await page.getByRole('button', { name: '删除记录' }).first().click()
    await expectVisible(page.locator('.crm-confirm-modal'), 'delete confirm dialog')
    const confirmRadius = await page.locator('.crm-confirm-modal').evaluate((node) => getComputedStyle(node).borderRadius)
    expect(confirmRadius === '8px', `Confirm dialog radius should be 8px, got ${confirmRadius}.`)
    await page.getByRole('button', { name: '取消' }).click()
    await page.locator('.crm-confirm-modal').waitFor({ state: 'detached' })
    const rowsAfterCancel = await page.locator('.crm-table tbody tr').count()
    expect(rowsAfterCancel === rowsBefore, `Canceling delete changed row count from ${rowsBefore} to ${rowsAfterCancel}.`)
    passed.push('delete-confirm-cancel')

    await assertRoute(page, '/reports', /销售报表/, 'reports')
    passed.push('reports')
    await assertRoute(page, '/orders', /订单中心/, 'orders')
    passed.push('orders')

    if (args.includeAiPage) {
      await assertRoute(page, '/copilot', /AI 销售副驾|AI 副驾/, 'copilot')
      passed.push('copilot-page')
    }

    expect(nativeDialogs.length === 0, `Native browser dialogs were triggered: ${nativeDialogs.join(', ')}`)
    expect(pageErrors.length === 0, `Page errors were triggered: ${pageErrors.join(' | ')}`)
    expect(consoleErrors.length === 0, `Console errors were triggered: ${consoleErrors.join(' | ')}`)
    passed.push('no-native-dialogs-or-errors')

    await page.goto('/profile')
    await page.getByRole('button', { name: /退出登录/ }).click()
    await page.waitForURL('**/login')
    passed.push('logout')
  } finally {
    await context.close()
    await browser.close()
  }

  return passed
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const passed = await runUiSmoke(args)
  console.log(`Smart CRM UI smoke passed against ${args.frontendUrl}.`)
  for (const label of passed) {
    console.log(`- ${label}`)
  }
}

main().catch((error) => {
  const message = error instanceof SmokeFailure ? error.message : error.stack || error.message
  console.error(`UI SMOKE FAILED: ${message}`)
  process.exit(1)
})
