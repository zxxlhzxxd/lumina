// Electron main process.
// Responsibilities: spawn the local FastAPI backend, discover its port from
// stdout (`LUMINA_PORT=<n>`), create the window, expose IPC to the renderer,
// and tear the backend down on exit.
const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const isDev = process.env.NODE_ENV === "development";

let backendProcess = null;
let backendPort = null;
let backendReady = null; // Promise resolving to the port
let mainWindow = null;

function resolvePython(backendDir) {
  const venvPython =
    process.platform === "win32"
      ? path.join(backendDir, ".venv", "Scripts", "python.exe")
      : path.join(backendDir, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return process.platform === "win32" ? "python" : "python3";
}

function startBackend() {
  const backendDir = path.resolve(__dirname, "..", "..", "backend");
  const python = resolvePython(backendDir);

  backendReady = new Promise((resolve, reject) => {
    backendProcess = spawn(python, ["-m", "app.main"], {
      cwd: backendDir,
      env: { ...process.env, LUMINA_PORT: "0", LUMINA_HOST: "127.0.0.1" },
    });

    let resolved = false;
    const onData = (buf) => {
      const text = buf.toString();
      process.stdout.write(`[backend] ${text}`);
      const match = text.match(/LUMINA_PORT=(\d+)/);
      if (match && !resolved) {
        resolved = true;
        backendPort = parseInt(match[1], 10);
        resolve(backendPort);
      }
    };
    backendProcess.stdout.on("data", onData);
    backendProcess.stderr.on("data", onData);

    backendProcess.on("error", (err) => {
      if (!resolved) reject(err);
    });
    backendProcess.on("exit", (code) => {
      process.stdout.write(`[backend] exited with code ${code}\n`);
      if (!resolved) reject(new Error(`backend exited (code ${code})`));
    });

    setTimeout(() => {
      if (!resolved) reject(new Error("backend startup timed out"));
    }, 30000);
  });

  return backendReady;
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    title: "Lumina",
    backgroundColor: "#141414",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL("http://127.0.0.1:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

ipcMain.handle("backend:info", async () => {
  const port = await backendReady;
  return { port, baseUrl: `http://127.0.0.1:${port}/api/v1` };
});

ipcMain.handle("dialog:savePptx", async (_evt, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: "导出 PowerPoint",
    defaultPath: defaultName || "礼拜.pptx",
    filters: [{ name: "PowerPoint", extensions: ["pptx"] }],
  });
  return result.canceled ? null : result.filePath;
});

app.whenReady().then(async () => {
  try {
    await startBackend();
  } catch (err) {
    process.stdout.write(`[backend] failed to start: ${err}\n`);
  }
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", stopBackend);
process.on("exit", stopBackend);
