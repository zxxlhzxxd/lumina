// Electron main process.
// Responsibilities: spawn the local FastAPI backend, discover its port from
// stdout (`LUMINA_PORT=<n>`), create the window, expose IPC to the renderer,
// and tear the backend down on exit.
const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;

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

function resolveBackendCommand() {
  if (isDev) {
    const backendDir = path.resolve(__dirname, "..", "..", "backend");
    return {
      command: resolvePython(backendDir),
      args: ["-m", "app.main"],
      cwd: backendDir,
    };
  }

  const backendRoot = path.join(process.resourcesPath, "backend", "lumina-backend");
  const executable = process.platform === "win32" ? "lumina-backend.exe" : "lumina-backend";
  return {
    command: path.join(backendRoot, executable),
    args: [],
    cwd: backendRoot,
  };
}

function isBackendRunning() {
  return (
    backendProcess &&
    !backendProcess.killed &&
    backendProcess.exitCode === null &&
    backendProcess.signalCode === null
  );
}

function clearBackendState(processRef) {
  if (processRef && backendProcess !== processRef) return;
  backendProcess = null;
  backendPort = null;
  backendReady = null;
}

function startBackend() {
  if (backendReady && isBackendRunning()) return backendReady;

  const backend = resolveBackendCommand();

  backendReady = new Promise((resolve, reject) => {
    const child = spawn(backend.command, backend.args, {
      cwd: backend.cwd,
      env: { ...process.env, LUMINA_PORT: "0", LUMINA_HOST: "127.0.0.1" },
      windowsHide: true,
    });
    backendProcess = child;

    let resolved = false;
    let rejected = false;
    let startupTimeout = null;

    const rejectStartup = (err) => {
      if (resolved || rejected) return;
      rejected = true;
      if (startupTimeout) clearTimeout(startupTimeout);
      clearBackendState(child);
      reject(err);
    };

    const onData = (buf) => {
      const text = buf.toString();
      process.stdout.write(`[backend] ${text}`);
      const match = text.match(/LUMINA_PORT=(\d+)/);
      if (match && !resolved && !rejected) {
        resolved = true;
        if (startupTimeout) clearTimeout(startupTimeout);
        backendPort = parseInt(match[1], 10);
        resolve(backendPort);
      }
    };
    child.stdout.on("data", onData);
    child.stderr.on("data", onData);

    child.on("error", (err) => {
      rejectStartup(err);
    });
    child.on("exit", (code, signal) => {
      const reason = signal ? `signal ${signal}` : `code ${code}`;
      process.stdout.write(`[backend] exited with ${reason}\n`);
      if (!resolved) {
        rejectStartup(new Error(`backend exited (${reason})`));
        return;
      }
      clearBackendState(child);
    });

    startupTimeout = setTimeout(() => {
      if (!resolved) {
        if (!child.killed) child.kill();
        rejectStartup(new Error("backend startup timed out"));
      }
    }, 30000);
  });

  return backendReady;
}

function ensureBackend() {
  if (backendReady && isBackendRunning()) return backendReady;
  return startBackend();
}

function stopBackend() {
  const child = backendProcess;
  clearBackendState(child);
  if (child && !child.killed && child.exitCode === null) {
    child.kill();
  }
}

function createWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
    return mainWindow;
  }

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

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  if (isDev) {
    mainWindow.loadURL("http://127.0.0.1:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  return mainWindow;
}

ipcMain.handle("backend:info", async () => {
  const port = await ensureBackend();
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

const mediaFilterMap = {
  image: {
    name: "图片",
    extensions: ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
  },
  audio: { name: "音频", extensions: ["mp3", "wav"] },
  video: { name: "视频", extensions: ["mp4", "mov", "m4v", "webm"] },
};

function mediaFilters(kind) {
  return mediaFilterMap[kind]
    ? [mediaFilterMap[kind]]
    : [
      {
        name: "媒体文件",
        extensions: [
          "jpg", "jpeg", "png", "gif", "bmp", "webp",
          "mp3", "wav", "mp4", "mov", "m4v", "webm",
        ],
      },
    ];
}

ipcMain.handle("dialog:pickMedia", async (_evt, kind) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "选择媒体文件",
    properties: ["openFile"],
    filters: mediaFilters(kind),
  });
  return result.canceled || !result.filePaths.length ? null : result.filePaths[0];
});

ipcMain.handle("dialog:pickMediaFiles", async (_evt, kind) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "批量选择媒体文件",
    properties: ["openFile", "multiSelections"],
    filters: mediaFilters(kind),
  });
  return result.canceled ? [] : result.filePaths;
});

ipcMain.handle("dialog:exportTemplate", async (_evt, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: "导出流程模板",
    defaultPath: defaultName || "流程模板.lumina",
    filters: [{ name: "Lumina 模板", extensions: ["lumina", "lumina-template"] }],
  });
  return result.canceled ? null : result.filePath;
});

ipcMain.handle("dialog:importTemplate", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "导入流程模板",
    properties: ["openFile"],
    filters: [{ name: "Lumina 模板", extensions: ["lumina", "lumina-template"] }],
  });
  return result.canceled || !result.filePaths.length ? null : result.filePaths[0];
});

ipcMain.handle("dialog:exportHymnLibrary", async (_evt, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: "导出歌词库",
    defaultPath: defaultName || "歌词库.lumina-hymn",
    filters: [{ name: "Lumina 歌词库", extensions: ["lumina-hymn"] }],
  });
  return result.canceled ? null : result.filePath;
});

ipcMain.handle("dialog:importHymnLibrary", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "导入歌词库",
    properties: ["openFile"],
    filters: [{ name: "Lumina 歌词库", extensions: ["lumina-hymn"] }],
  });
  return result.canceled || !result.filePaths.length ? null : result.filePaths[0];
});

ipcMain.handle("dialog:exportLiturgyLibrary", async (_evt, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: "导出礼文库",
    defaultPath: defaultName || "礼文库.lumina-liturgy",
    filters: [{ name: "Lumina 礼文库", extensions: ["lumina-liturgy"] }],
  });
  return result.canceled ? null : result.filePath;
});

ipcMain.handle("dialog:importLiturgyLibrary", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "导入礼文库",
    properties: ["openFile"],
    filters: [{ name: "Lumina 礼文库", extensions: ["lumina-liturgy"] }],
  });
  return result.canceled || !result.filePaths.length ? null : result.filePaths[0];
});

app.whenReady().then(async () => {
  try {
    await ensureBackend();
  } catch (err) {
    process.stdout.write(`[backend] failed to start: ${err}\n`);
  }
  createWindow();

  app.on("activate", async () => {
    try {
      await ensureBackend();
    } catch (err) {
      process.stdout.write(`[backend] failed to start: ${err}\n`);
    }
    createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", stopBackend);
process.on("exit", stopBackend);
