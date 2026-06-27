// Exposes a minimal, stable bridge to the renderer.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("lumina", {
  getBackendInfo: () => ipcRenderer.invoke("backend:info"),
  savePptxDialog: (defaultName) => ipcRenderer.invoke("dialog:savePptx", defaultName),
  pickMediaDialog: (kind) => ipcRenderer.invoke("dialog:pickMedia", kind),
  exportTemplateDialog: (defaultName) =>
    ipcRenderer.invoke("dialog:exportTemplate", defaultName),
  importTemplateDialog: () => ipcRenderer.invoke("dialog:importTemplate"),
  exportHymnLibraryDialog: (defaultName) =>
    ipcRenderer.invoke("dialog:exportHymnLibrary", defaultName),
  importHymnLibraryDialog: () => ipcRenderer.invoke("dialog:importHymnLibrary"),
  exportLiturgyLibraryDialog: (defaultName) =>
    ipcRenderer.invoke("dialog:exportLiturgyLibrary", defaultName),
  importLiturgyLibraryDialog: () =>
    ipcRenderer.invoke("dialog:importLiturgyLibrary"),
});
