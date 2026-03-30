import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test('loads and displays the main heading', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toHaveText('Get started')
  })

  test('counter button increments on click', async ({ page }) => {
    await page.goto('/')
    const counter = page.locator('button.counter')
    await expect(counter).toContainText('Count is 0')
    await counter.click()
    await expect(counter).toContainText('Count is 1')
  })

  test('screenshot of homepage', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/homepage.png', fullPage: true })
  })
})
