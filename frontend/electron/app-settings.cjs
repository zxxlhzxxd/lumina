const fs = require("fs");
const path = require("path");

const SETTINGS_FILE_NAME = "settings.json";

function isSettingsObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function createAppSettings(userDataDirectory, fileSystem = fs) {
  const settingsPath = path.join(userDataDirectory, SETTINGS_FILE_NAME);

  function readSettings() {
    try {
      const parsed = JSON.parse(fileSystem.readFileSync(settingsPath, "utf8"));
      return isSettingsObject(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }

  function writeSettings(settings) {
    try {
      fileSystem.mkdirSync(userDataDirectory, { recursive: true });
      fileSystem.writeFileSync(
        settingsPath,
        `${JSON.stringify(settings, null, 2)}\n`,
        "utf8"
      );
      return true;
    } catch {
      return false;
    }
  }

  return {
    getLastPptxExportDirectory() {
      const value = readSettings().lastPptxExportDirectory;
      return typeof value === "string" && value.length > 0 ? value : null;
    },

    setLastPptxExportDirectory(directory) {
      if (typeof directory !== "string" || directory.length === 0) return false;
      return writeSettings({
        ...readSettings(),
        lastPptxExportDirectory: directory,
      });
    },
  };
}

module.exports = { createAppSettings, SETTINGS_FILE_NAME };
