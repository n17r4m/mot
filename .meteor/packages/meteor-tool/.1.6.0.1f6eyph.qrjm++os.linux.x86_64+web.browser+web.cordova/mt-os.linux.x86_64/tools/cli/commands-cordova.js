let _;

module.watch(require("underscore"), {
  default(v) {
    _ = v;
  }

}, 0);
let main;
module.watch(require("./main.js"), {
  default(v) {
    main = v;
  }

}, 1);
let Console;
module.watch(require("../console/console.js"), {
  Console(v) {
    Console = v;
  }

}, 2);
let catalog;
module.watch(require("../packaging/catalog/catalog.js"), {
  default(v) {
    catalog = v;
  }

}, 3);
let buildmessage;
module.watch(require("../utils/buildmessage.js"), {
  default(v) {
    buildmessage = v;
  }

}, 4);
let files;
module.watch(require("../fs/files.js"), {
  default(v) {
    files = v;
  }

}, 5);
let CORDOVA_PLATFORMS, ensureDevBundleDependencies, filterPlatforms;
module.watch(require("../cordova"), {
  CORDOVA_PLATFORMS(v) {
    CORDOVA_PLATFORMS = v;
  },

  ensureDevBundleDependencies(v) {
    ensureDevBundleDependencies = v;
  },

  filterPlatforms(v) {
    filterPlatforms = v;
  }

}, 6);

function createProjectContext(appDir) {
  let ProjectContext;
  module.watch(require("../project-context.js"), {
    ProjectContext(v) {
      ProjectContext = v;
    }

  }, 7);
  const projectContext = new ProjectContext({
    projectDir: appDir
  });
  main.captureAndExit('=> Errors while initializing project:', () => {
    // We're just reading metadata here; we don't need to resolve constraints.
    projectContext.readProjectMetadata();
  });
  return projectContext;
}

function doAddPlatform(options) {
  let CordovaProject;
  module.watch(require("../cordova/project.js"), {
    CordovaProject(v) {
      CordovaProject = v;
    }

  }, 8);
  Console.setVerbose(!!options.verbose);
  const projectContext = createProjectContext(options.appDir);
  const platformsToAdd = options.args;
  let installedPlatforms = projectContext.platformList.getPlatforms();
  main.captureAndExit('', 'adding platforms', () => {
    for (platform of platformsToAdd) {
      if (_.contains(installedPlatforms, platform)) {
        buildmessage.error(`${platform}: platform is already added`);
      } else if (!_.contains(CORDOVA_PLATFORMS, platform)) {
        buildmessage.error(`${platform}: no such platform`);
      }
    }

    if (buildmessage.jobHasMessages()) {
      return;
    }

    const cordovaProject = new CordovaProject(projectContext);
    if (buildmessage.jobHasMessages()) return;
    installedPlatforms = installedPlatforms.concat(platformsToAdd);
    const cordovaPlatforms = filterPlatforms(installedPlatforms);
    cordovaProject.ensurePlatformsAreSynchronized(cordovaPlatforms);

    if (buildmessage.jobHasMessages()) {
      return;
    } // Only write the new platform list when we have succesfully synchronized


    projectContext.platformList.write(installedPlatforms);

    for (platform of platformsToAdd) {
      Console.info(`${platform}: added platform`);

      if (_.contains(cordovaPlatforms, platform)) {
        cordovaProject.checkPlatformRequirements(platform);
      }
    }
  });
}

function doRemovePlatform(options) {
  let CordovaProject;
  module.watch(require("../cordova/project.js"), {
    CordovaProject(v) {
      CordovaProject = v;
    }

  }, 9);
  let PlatformList;
  module.watch(require("../project-context.js"), {
    PlatformList(v) {
      PlatformList = v;
    }

  }, 10);
  const projectContext = createProjectContext(options.appDir);
  const platformsToRemove = options.args;
  let installedPlatforms = projectContext.platformList.getPlatforms();
  main.captureAndExit('', 'removing platforms', () => {
    for (platform of platformsToRemove) {
      // Explain why we can't remove server or browser platforms
      if (_.contains(PlatformList.DEFAULT_PLATFORMS, platform)) {
        buildmessage.error(`${platform}: cannot remove platform in this \
version of Meteor`);
      } else if (!_.contains(installedPlatforms, platform)) {
        buildmessage.error(`${platform}: platform is not in this project`);
      }
    }

    if (buildmessage.jobHasMessages()) {
      return;
    }

    installedPlatforms = _.without(installedPlatforms, ...platformsToRemove);
    projectContext.platformList.write(installedPlatforms);

    for (platform of platformsToRemove) {
      Console.info(`${platform}: removed platform`);
    }

    if (process.platform !== 'win32') {
      const cordovaProject = new CordovaProject(projectContext);
      if (buildmessage.jobHasMessages()) return;
      const cordovaPlatforms = filterPlatforms(installedPlatforms);
      cordovaProject.ensurePlatformsAreSynchronized(cordovaPlatforms);
    }
  });
} // Add one or more Cordova platforms


main.registerCommand({
  name: 'add-platform',
  options: {
    verbose: {
      type: Boolean,
      short: "v"
    }
  },
  minArgs: 1,
  maxArgs: Infinity,
  requiresApp: true,
  catalogRefresh: new catalog.Refresh.Never(),
  notOnWindows: false
}, function (options) {
  ensureDevBundleDependencies();
  doAddPlatform(options);
}); // Remove one or more Cordova platforms

main.registerCommand({
  name: 'remove-platform',
  minArgs: 1,
  maxArgs: Infinity,
  requiresApp: true,
  catalogRefresh: new catalog.Refresh.Never()
}, function (options) {
  ensureDevBundleDependencies();
  doRemovePlatform(options);
});
main.registerCommand({
  name: 'list-platforms',
  requiresApp: true,
  catalogRefresh: new catalog.Refresh.Never()
}, function (options) {
  const projectContext = createProjectContext(options.appDir);
  const installedPlatforms = projectContext.platformList.getPlatforms();
  Console.rawInfo(installedPlatforms.join('\n') + '\n');
});
main.registerCommand({
  name: 'install-sdk',
  options: {
    verbose: {
      type: Boolean,
      short: "v"
    }
  },
  minArgs: 0,
  maxArgs: Infinity,
  catalogRefresh: new catalog.Refresh.Never(),
  hidden: true,
  notOnWindows: true
}, function (options) {
  Console.setVerbose(!!options.verbose);
  Console.info("Please follow the installation instructions in the mobile guide:");
  Console.info(Console.url("http://guide.meteor.com/mobile.html#installing-prerequisites"));
  return 0;
});
main.registerCommand({
  name: 'configure-android',
  options: {
    verbose: {
      type: Boolean,
      short: "v"
    }
  },
  minArgs: 0,
  maxArgs: Infinity,
  catalogRefresh: new catalog.Refresh.Never(),
  hidden: true,
  notOnWindows: true
}, function (options) {
  Console.setVerbose(!!options.verbose);
  Console.info(`You can launch the Android SDK Manager from within Android \
Studio.
See`, Console.url("http://developer.android.com/tools/help/sdk-manager.html"), `
Alternatively, you can launch it by running the 'android' command.
(This requires that you have set ANDROID_HOME and added ANDROID_HOME/tools \
to your PATH.)`);
  return 0;
});
//# sourceMappingURL=commands-cordova.js.map