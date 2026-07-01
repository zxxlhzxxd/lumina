const path = require("path");
const { execFile } = require("child_process");
const fs = require("fs/promises");

const NOTARYTOOL_TIMEOUT = "10m";
const NOTARYTOOL_PROCESS_TIMEOUT_MS = 11 * 60 * 1000;
const COMMAND_MAX_BUFFER = 10 * 1024 * 1024;

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    execFile(
      command,
      args,
      {
        maxBuffer: COMMAND_MAX_BUFFER,
        ...options,
      },
      (error, stdout, stderr) => {
        const output = `${stdout || ""}${stderr || ""}`;
        if (error) {
          const message = [
            `${command} failed with code ${error.code ?? "unknown"}`,
            error.signal ? `signal ${error.signal}` : "",
            error.killed ? "process was killed" : "",
            output.trim(),
          ]
            .filter(Boolean)
            .join("\n");
          reject(new Error(message));
          return;
        }
        resolve({ stdout, stderr, output });
      }
    );
  });
}

function authArgs({ appleId, appleIdPassword, teamId }) {
  return [
    "--apple-id",
    appleId,
    "--password",
    appleIdPassword,
    "--team-id",
    teamId,
  ];
}

exports.default = async function notarizeMac(context) {
  if (process.platform !== "darwin" || context.electronPlatformName !== "darwin") {
    return;
  }

  const { APPLE_ID, APPLE_APP_SPECIFIC_PASSWORD, APPLE_TEAM_ID } = process.env;
  if (!APPLE_ID || !APPLE_APP_SPECIFIC_PASSWORD || !APPLE_TEAM_ID) {
    console.log("Skipping macOS notarization: Apple credentials are not configured.");
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(context.appOutDir, `${appName}.app`);
  const zipPath = path.join(
    context.outDir,
    `${appName}-notarization-${Date.now()}.zip`
  );

  const credentials = {
    appleId: APPLE_ID,
    appleIdPassword: APPLE_APP_SPECIFIC_PASSWORD,
    teamId: APPLE_TEAM_ID,
  };

  try {
    console.log(`Creating macOS notarization archive at ${zipPath}.`);
    await run("ditto", [
      "-c",
      "-k",
      "--sequesterRsrc",
      "--keepParent",
      path.basename(appPath),
      zipPath,
    ], {
      cwd: path.dirname(appPath),
    });

    console.log(
      `Submitting macOS app for notarization with a ${NOTARYTOOL_TIMEOUT} timeout.`
    );
    const result = await run("xcrun", [
      "notarytool",
      "submit",
      zipPath,
      ...authArgs(credentials),
      "--wait",
      "--timeout",
      NOTARYTOOL_TIMEOUT,
      "--output-format",
      "json",
    ], {
      timeout: NOTARYTOOL_PROCESS_TIMEOUT_MS,
    });

    const rawOutput = result.output.trim();
    let parsed;
    try {
      parsed = JSON.parse(rawOutput);
    } catch (error) {
      throw new Error(`Failed to parse notarytool output:\n${rawOutput}`);
    }

    if (parsed.status !== "Accepted") {
      throw new Error(`macOS notarization failed:\n${rawOutput}`);
    }

    console.log(`Stapling macOS notarization ticket for ${appPath}.`);
    await run("xcrun", ["stapler", "staple", "-v", path.basename(appPath)], {
      cwd: path.dirname(appPath),
      timeout: 2 * 60 * 1000,
    });
    console.log("macOS notarization completed.");
  } finally {
    await fs.rm(zipPath, { force: true });
  }
};
