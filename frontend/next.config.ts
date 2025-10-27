import type { NextConfig } from "next";
import fs from "node:fs";
import path from "node:path";
import { withSentryConfig } from "@sentry/nextjs";

function loadEnvFile(filePath: string, override = false) {
  if (!fs.existsSync(filePath)) return;

  try {
    const contents = fs.readFileSync(filePath, "utf8");
    const lines = contents.split(/\r?\n/);

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line || line.startsWith("#")) {
        continue;
      }

      const separatorIndex = line.indexOf("=");
      if (separatorIndex === -1) {
        continue;
      }

      const key = line.slice(0, separatorIndex).trim();
      if (!key) {
        continue;
      }

      let value = line.slice(separatorIndex + 1).trim();
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }

      if (!override && process.env[key] !== undefined) {
        continue;
      }

      process.env[key] = value;
    }
  } catch (error) {
    console.warn(`Failed to load environment file at ${filePath}:`, error);
  }
}

const projectRoot = path.resolve(__dirname, "..", "..");
const rootEnv = path.join(projectRoot, ".env");
const rootLocalEnv = path.join(projectRoot, ".env.local");

loadEnvFile(rootEnv);
loadEnvFile(rootLocalEnv, true);

const nextConfig: NextConfig = {
  /* config options here */
};

export default withSentryConfig(
  nextConfig,
  {
    // For all available options, see: https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Transpiles SDK to be compatible with IE11 (increases bundle size)
    transpileClientSDK: true,

    // Routes browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers (increases server load)
    tunnelRoute: "/monitoring-tunnel",

    // Hides source maps from generated client bundles
    hideSourceMaps: true,

    // Automatically tree-shake client-side only code in server bundles
    disableLogger: true,

    // For all available options, see: https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/
  },
  {
    // For all available options, see: https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Suppresses source map uploading logs during build time
    silent: true,

    // For all available options, see: https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/
  }
);
