const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  createAppSettings,
  SETTINGS_FILE_NAME,
} = require("../app-settings.cjs");

function makeTemporaryDirectory(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "lumina-settings-"));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  return directory;
}

test("persists the last PPTX directory across settings instances", (t) => {
  const userDataDirectory = makeTemporaryDirectory(t);
  const exportDirectory = path.join(userDataDirectory, "exports");

  const firstInstance = createAppSettings(userDataDirectory);
  assert.equal(firstInstance.getLastPptxExportDirectory(), null);
  assert.equal(firstInstance.setLastPptxExportDirectory(exportDirectory), true);

  const restartedInstance = createAppSettings(userDataDirectory);
  assert.equal(
    restartedInstance.getLastPptxExportDirectory(),
    exportDirectory
  );
});

test("preserves unrelated application settings", (t) => {
  const userDataDirectory = makeTemporaryDirectory(t);
  const settingsPath = path.join(userDataDirectory, SETTINGS_FILE_NAME);
  fs.writeFileSync(settingsPath, JSON.stringify({ theme: "dark" }), "utf8");

  createAppSettings(userDataDirectory).setLastPptxExportDirectory("/exports");

  assert.deepEqual(JSON.parse(fs.readFileSync(settingsPath, "utf8")), {
    theme: "dark",
    lastPptxExportDirectory: "/exports",
  });
});

test("recovers from malformed settings and contains write failures", (t) => {
  const userDataDirectory = makeTemporaryDirectory(t);
  const settingsPath = path.join(userDataDirectory, SETTINGS_FILE_NAME);
  fs.writeFileSync(settingsPath, "not json", "utf8");

  const settings = createAppSettings(userDataDirectory);
  assert.equal(settings.getLastPptxExportDirectory(), null);
  assert.equal(settings.setLastPptxExportDirectory("/exports"), true);

  const failingFileSystem = {
    ...fs,
    writeFileSync() {
      throw new Error("disk unavailable");
    },
  };
  assert.equal(
    createAppSettings(userDataDirectory, failingFileSystem)
      .setLastPptxExportDirectory("/other"),
    false
  );
});
