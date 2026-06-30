const path = require("path");

const RETRY_DELAYS_MS = [15000, 30000, 60000];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableNotarizationError(error) {
  const message = String(error?.message || error || "");
  return (
    /HTTP status code:\s*(429|5\d\d)/i.test(message) ||
    /Internal Server Error/i.test(message) ||
    /Please try again at a later time/i.test(message) ||
    /ECONNRESET|ETIMEDOUT|ENOTFOUND|EAI_AGAIN/i.test(message)
  );
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

  const { notarize } = require("@electron/notarize");
  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(context.appOutDir, `${appName}.app`);

  const options = {
    appBundleId: context.packager.appInfo.appId,
    appPath,
    appleId: APPLE_ID,
    appleIdPassword: APPLE_APP_SPECIFIC_PASSWORD,
    teamId: APPLE_TEAM_ID,
  };

  for (let attempt = 1; attempt <= RETRY_DELAYS_MS.length + 1; attempt += 1) {
    try {
      await notarize(options);
      return;
    } catch (error) {
      if (attempt > RETRY_DELAYS_MS.length || !isRetryableNotarizationError(error)) {
        throw error;
      }
      const delay = RETRY_DELAYS_MS[attempt - 1];
      console.log(
        `macOS notarization failed with a transient error; retrying in ${delay / 1000}s ` +
          `(attempt ${attempt + 1}/${RETRY_DELAYS_MS.length + 1}).`
      );
      await sleep(delay);
    }
  }
};
