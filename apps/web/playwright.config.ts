import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Configuration
 * Purpose: Real API → ViewModel → UI E2E tests (Example 1-4)
 *
 * Constitutional Compliance:
 * - Real API only (NO mocking/MSW)
 * - Deterministic (same query → same ViewModel)
 * - Fact-only validation (forbidden phrases check)
 */

export default defineConfig({
  testDir: './e2e',

  // Test configuration
  fullyParallel: false, // Run serially to avoid API conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker to avoid port conflicts

  // Reporter
  reporter: 'html',

  use: {
    // Base URL
    baseURL: 'http://localhost:3000',

    // Screenshots and videos
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Timeout
    actionTimeout: 10000,
  },

  // Configure projects
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Web Server Configuration (Auto-start frontend)
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
    timeout: 120000, // 2 minutes for dev server startup
  },
});
