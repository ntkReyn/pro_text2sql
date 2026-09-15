import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = path.resolve(webRoot, "..", "..");
const pythonCommand = process.env.PYTHON_COMMAND || "python";
const apiHost = "127.0.0.1";
const apiPort = process.env.DEV_API_PORT || "8000";
const webPort = process.env.DEV_WEB_PORT || "3000";
const apiBaseUrl = `http://${apiHost}:${apiPort}`;
const children = new Set();
let shuttingDown = false;

function start(command, args, options) {
  const child = spawn(command, args, {
    stdio: "inherit",
    windowsHide: true,
    ...options,
  });
  children.add(child);
  child.once("error", (error) => {
    console.error(`[dev] Không thể chạy ${command}: ${error.message}`);
    shutdown(1);
  });
  return child;
}

function shutdown(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (child.exitCode === null && !child.killed) child.kill();
  }
  setTimeout(() => process.exit(exitCode), 300).unref();
}

async function waitForCurrentApi(backend) {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    if (backend.exitCode !== null) {
      throw new Error(`FastAPI đã dừng với mã ${backend.exitCode}.`);
    }
    try {
      const response = await fetch(`${apiBaseUrl}/openapi.json`, { cache: "no-store" });
      if (response.ok) {
        const openapi = await response.json();
        if (openapi.paths?.["/api/v1/query/baseline"]?.post) return;
        throw new Error(
          `Cổng ${apiPort} đang phục vụ API cũ, chưa có /api/v1/query/baseline.`,
        );
      }
    } catch (error) {
      if (error instanceof Error && error.message.includes("API cũ")) throw error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`FastAPI không sẵn sàng tại ${apiBaseUrl} sau 20 giây.`);
}

process.once("SIGINT", () => shutdown(0));
process.once("SIGTERM", () => shutdown(0));

console.log(`[dev] Khởi động FastAPI mới tại ${apiBaseUrl}`);
const backend = start(
  pythonCommand,
  [
    "-m", "uvicorn", "apps.api.main:app",
    "--reload",
    "--reload-dir", "apps/api",
    "--reload-dir", "packages",
    "--host", apiHost,
    "--port", apiPort,
  ],
  { cwd: repositoryRoot, env: { ...process.env, API_HOST: apiHost, API_PORT: apiPort } },
);

try {
  await waitForCurrentApi(backend);
} catch (error) {
  console.error(`[dev] ${error instanceof Error ? error.message : String(error)}`);
  shutdown(1);
  await new Promise(() => {});
}

console.log(`[dev] FastAPI sẵn sàng. Khởi động Next.js tại http://localhost:${webPort}`);
const nextBin = path.join(webRoot, "node_modules", "next", "dist", "bin", "next");
const frontend = start(
  process.execPath,
  [nextBin, "dev", "--hostname", "0.0.0.0", "--port", webPort],
  {
    cwd: webRoot,
    env: { ...process.env, ANALYTICS_API_BASE_URL: apiBaseUrl },
  },
);

backend.once("exit", (code) => {
  children.delete(backend);
  if (!shuttingDown) {
    console.error(`[dev] FastAPI đã dừng${code === null ? "" : ` với mã ${code}`}.`);
    shutdown(code || 1);
  }
});

frontend.once("exit", (code) => {
  children.delete(frontend);
  if (!shuttingDown) shutdown(code || 0);
});
