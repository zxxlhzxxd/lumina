// Exposes a minimal, stable bridge to the renderer.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("lumina", {
  getBackendInfo: () => ipcRenderer.invoke("backend:info"),
  savePptxDialog: (defaultName) => ipcRenderer.invoke("dialog:savePptx", defaultName),
});
