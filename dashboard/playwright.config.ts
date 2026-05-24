import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./src/tests",
  testMatch: "**/*.spec.ts",
  use: {
    baseURL: "http://localhost:4321",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:4321",
    reuseExistingServer: !process.env.CI,
    env: {
      PUBLIC_DASHBOARD_USER_HASH: process.env.PUBLIC_DASHBOARD_USER_HASH ?? "",
      PUBLIC_DASHBOARD_PASSWORD_HASH:
        process.env.PUBLIC_DASHBOARD_PASSWORD_HASH ?? "",
    },
  },
});
