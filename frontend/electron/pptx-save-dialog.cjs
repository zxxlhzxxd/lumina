const fs = require("fs");
const path = require("path");

const FALLBACK_PPTX_NAME = "礼拜.pptx";

function isUsableDirectory(directory, fileSystem = fs) {
  if (typeof directory !== "string" || directory.length === 0) return false;
  try {
    if (!fileSystem.statSync(directory).isDirectory()) return false;
    fileSystem.accessSync(
      directory,
      fileSystem.constants.R_OK | fileSystem.constants.W_OK
    );
    return true;
  } catch {
    return false;
  }
}

function buildDefaultPptxPath({
  defaultName,
  lastExportDirectory,
  documentsDirectory,
  fileSystem = fs,
  pathModule = path,
}) {
  const requestedName =
    typeof defaultName === "string" && defaultName.length > 0
      ? defaultName
      : FALLBACK_PPTX_NAME;
  const fileName = pathModule.basename(requestedName);
  const directory = isUsableDirectory(lastExportDirectory, fileSystem)
    ? lastExportDirectory
    : isUsableDirectory(documentsDirectory, fileSystem)
      ? documentsDirectory
      : null;
  return directory ? pathModule.join(directory, fileName) : fileName;
}

async function showPptxSaveDialog({
  dialog,
  browserWindow,
  settings,
  documentsDirectory,
  defaultName,
  fileSystem = fs,
  pathModule = path,
}) {
  const defaultPath = buildDefaultPptxPath({
    defaultName,
    lastExportDirectory: settings.getLastPptxExportDirectory(),
    documentsDirectory,
    fileSystem,
    pathModule,
  });
  const result = await dialog.showSaveDialog(browserWindow, {
    title: "导出 PowerPoint",
    defaultPath,
    filters: [{ name: "PowerPoint", extensions: ["pptx"] }],
  });

  if (result.canceled || !result.filePath) return null;

  try {
    settings.setLastPptxExportDirectory(pathModule.dirname(result.filePath));
  } catch {
    // A settings failure must not prevent exporting to the selected path.
  }
  return result.filePath;
}

module.exports = {
  FALLBACK_PPTX_NAME,
  buildDefaultPptxPath,
  isUsableDirectory,
  showPptxSaveDialog,
};
