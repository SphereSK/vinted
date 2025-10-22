const path = require("node:path");
const fs = require("node:fs");

const envPath = path.join(__dirname, ".env");
if (fs.existsSync(envPath)) {
  try {
    const envContent = fs.readFileSync(envPath, "utf8");
    for (const rawLine of envContent.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith("#")) {
        continue;
      }
      const index = line.indexOf("=");
      if (index === -1) {
        continue;
      }
      const key = line.slice(0, index).trim();
      if (!key) {
        continue;
      }
      let value = line.slice(index + 1).trim();
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }
      if (process.env[key] === undefined) {
        process.env[key] = value;
      }
    }
  } catch (error) {
    console.warn("Failed to load .env for PM2:", error);
  }
}

module.exports = {
  apps: [
    {
      name: "vinted-fastapi",
      cwd: "/home/datament/project/vinted",
      script: "/home/datament/project/vinted/.venv/bin/uvicorn",
      args: "fastAPI.main:app --host 0.0.0.0 --port 8933",
      interpreter: "/home/datament/project/vinted/.venv/bin/python",
      env: {
        FASTAPI_HOST: process.env.FASTAPI_HOST || "0.0.0.0",
        FASTAPI_PORT: process.env.FASTAPI_PORT || "8933",
        FASTAPI_API_KEY: process.env.FASTAPI_API_KEY || "change_me_api_key",
        FASTAPI_API_KEY_HEADER:
          process.env.FASTAPI_API_KEY_HEADER || "X-API-Key",
      },
    },
    {
      name: "vinted-nextjs",
      cwd: "/home/datament/project/vinted/frontend",
      script: "/home/datament/.nvm/versions/node/v22.15.0/bin/npm",
      args: "run dev -- --hostname 0.0.0.0 --port 8934",
      env: {
        NODE_ENV: process.env.NODE_ENV || "production",
        PORT: process.env.PORT || "8934",
        NEXT_PUBLIC_API_BASE_URL:
          process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8933",
        NEXT_PUBLIC_API_KEY:
          process.env.NEXT_PUBLIC_API_KEY || "change_me_api_key",
        NEXT_PUBLIC_API_KEY_HEADER:
          process.env.NEXT_PUBLIC_API_KEY_HEADER || "X-API-Key",
        FASTAPI_INTERNAL_URL:
          process.env.FASTAPI_INTERNAL_URL || "http://127.0.0.1:8933",
        FASTAPI_API_KEY: process.env.FASTAPI_API_KEY || "change_me_api_key",
        FASTAPI_API_KEY_HEADER:
          process.env.FASTAPI_API_KEY_HEADER || "X-API-Key",
      },
    },
  ],
};
