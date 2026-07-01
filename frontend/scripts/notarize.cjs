const path = require("path");

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

  console.log(`Notarizing macOS app bundle at ${appPath}.`);
  await notarize(options);
  console.log("macOS notarization completed.");
};
