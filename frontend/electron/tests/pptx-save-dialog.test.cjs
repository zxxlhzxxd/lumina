const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  buildDefaultPptxPath,
  showPptxSaveDialog,
} = require("../pptx-save-dialog.cjs");

function makeTemporaryDirectory(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "lumina-pptx-"));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  return directory;
}

function createSettings(lastDirectory = null) {
  const updates = [];
  return {
    updates,
    getLastPptxExportDirectory: () => lastDirectory,
    setLastPptxExportDirectory: (directory) => updates.push(directory),
  };
}

test("uses Documents and the project name on first export", (t) => {
  const documentsDirectory = makeTemporaryDirectory(t);
  assert.equal(
    buildDefaultPptxPath({
      defaultName: "主日礼拜.pptx",
      lastExportDirectory: null,
      documentsDirectory,
    }),
    path.join(documentsDirectory, "主日礼拜.pptx")
  );
});

test("uses a valid remembered directory instead of Documents", (t) => {
  const root = makeTemporaryDirectory(t);
  const rememberedDirectory = path.join(root, "remembered");
  const documentsDirectory = path.join(root, "documents");
  fs.mkdirSync(rememberedDirectory);
  fs.mkdirSync(documentsDirectory);

  assert.equal(
    buildDefaultPptxPath({
      defaultName: "晚礼拜.pptx",
      lastExportDirectory: rememberedDirectory,
      documentsDirectory,
    }),
    path.join(rememberedDirectory, "晚礼拜.pptx")
  );
});

test("falls back when the remembered directory is missing or inaccessible", (t) => {
  const root = makeTemporaryDirectory(t);
  const missingDirectory = path.join(root, "deleted");
  const documentsDirectory = path.join(root, "documents");
  fs.mkdirSync(documentsDirectory);

  assert.equal(
    buildDefaultPptxPath({
      defaultName: "礼拜.pptx",
      lastExportDirectory: missingDirectory,
      documentsDirectory,
    }),
    path.join(documentsDirectory, "礼拜.pptx")
  );

  const inaccessibleFileSystem = {
    ...fs,
    accessSync(directory, mode) {
      if (directory === root) throw new Error("permission denied");
      return fs.accessSync(directory, mode);
    },
  };
  assert.equal(
    buildDefaultPptxPath({
      defaultName: "礼拜.pptx",
      lastExportDirectory: root,
      documentsDirectory,
      fileSystem: inaccessibleFileSystem,
    }),
    path.join(documentsDirectory, "礼拜.pptx")
  );
});

test("uses only the filename when no candidate directory is usable", (t) => {
  const root = makeTemporaryDirectory(t);
  assert.equal(
    buildDefaultPptxPath({
      defaultName: "礼拜.pptx",
      lastExportDirectory: path.join(root, "missing-last"),
      documentsDirectory: path.join(root, "missing-documents"),
    }),
    "礼拜.pptx"
  );
});

test("updates settings only after the user selects a path", async (t) => {
  const root = makeTemporaryDirectory(t);
  const documentsDirectory = path.join(root, "documents");
  const selectedDirectory = path.join(root, "selected");
  const selectedPath = path.join(selectedDirectory, "礼拜.pptx");
  fs.mkdirSync(documentsDirectory);
  const settings = createSettings();
  let options = null;
  const dialog = {
    async showSaveDialog(_window, receivedOptions) {
      options = receivedOptions;
      return { canceled: false, filePath: selectedPath };
    },
  };

  assert.equal(
    await showPptxSaveDialog({
      dialog,
      browserWindow: {},
      settings,
      documentsDirectory,
      defaultName: "礼拜.pptx",
    }),
    selectedPath
  );
  assert.equal(options.defaultPath, path.join(documentsDirectory, "礼拜.pptx"));
  assert.deepEqual(settings.updates, [selectedDirectory]);
});

test("does not update settings when the save dialog is canceled", async (t) => {
  const documentsDirectory = makeTemporaryDirectory(t);
  const settings = createSettings("/previous/export/directory");
  const dialog = {
    async showSaveDialog() {
      return { canceled: true };
    },
  };

  assert.equal(
    await showPptxSaveDialog({
      dialog,
      browserWindow: {},
      settings,
      documentsDirectory,
      defaultName: "礼拜.pptx",
    }),
    null
  );
  assert.deepEqual(settings.updates, []);
});

test("returns the selected path even when settings cannot be updated", async (t) => {
  const documentsDirectory = makeTemporaryDirectory(t);
  const selectedPath = path.join(documentsDirectory, "礼拜.pptx");
  const settings = {
    getLastPptxExportDirectory: () => null,
    setLastPptxExportDirectory() {
      throw new Error("settings unavailable");
    },
  };
  const dialog = {
    async showSaveDialog() {
      return { canceled: false, filePath: selectedPath };
    },
  };

  assert.equal(
    await showPptxSaveDialog({
      dialog,
      browserWindow: {},
      settings,
      documentsDirectory,
      defaultName: "礼拜.pptx",
    }),
    selectedPath
  );
});
