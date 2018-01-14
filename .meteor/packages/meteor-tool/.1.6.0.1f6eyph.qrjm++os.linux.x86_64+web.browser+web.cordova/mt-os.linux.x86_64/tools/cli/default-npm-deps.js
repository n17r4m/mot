module.export({
  install: () => install
});
let buildmessage;
module.watch(require("../utils/buildmessage.js"), {
  default(v) {
    buildmessage = v;
  }

}, 0);
let pathJoin, statOrNull, writeFile, unlink;
module.watch(require("../fs/files.js"), {
  pathJoin(v) {
    pathJoin = v;
  },

  statOrNull(v) {
    statOrNull = v;
  },

  writeFile(v) {
    writeFile = v;
  },

  unlink(v) {
    unlink = v;
  }

}, 1);
const INSTALL_JOB_MESSAGE = "installing npm dependencies";

function install(appDir) {
  const packageJsonPath = pathJoin(appDir, "package.json");
  const needTempPackageJson = !statOrNull(packageJsonPath);

  if (needTempPackageJson) {
    const {
      dependencies
    } = require("../static-assets/skel/package.json"); // Write a minimial package.json with the same dependencies as the
    // default new-app package.json file.


    writeFile(packageJsonPath, JSON.stringify({
      dependencies
    }, null, 2) + "\n", "utf8");
  }

  const ok = buildmessage.enterJob(INSTALL_JOB_MESSAGE, function () {
    const {
      runNpmCommand
    } = require("../isobuild/meteor-npm.js");

    const installResult = runNpmCommand(["install"], appDir);

    if (!installResult.success) {
      buildmessage.error("Could not install npm dependencies for test-packages: " + installResult.error);
      return false;
    }

    return true;
  });

  if (needTempPackageJson) {
    // Clean up the temporary package.json file created above.
    unlink(packageJsonPath);
  }

  return ok;
}
//# sourceMappingURL=default-npm-deps.js.map