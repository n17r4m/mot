module.export({
  CORDOVA_ARCH: () => CORDOVA_ARCH,
  CORDOVA_PLATFORMS: () => CORDOVA_PLATFORMS,
  CORDOVA_DEV_BUNDLE_VERSIONS: () => CORDOVA_DEV_BUNDLE_VERSIONS,
  CORDOVA_PLATFORM_VERSIONS: () => CORDOVA_PLATFORM_VERSIONS,
  ensureDevBundleDependencies: () => ensureDevBundleDependencies,
  displayNameForPlatform: () => displayNameForPlatform,
  displayNamesForPlatforms: () => displayNamesForPlatforms,
  filterPlatforms: () => filterPlatforms,
  splitPluginsAndPackages: () => splitPluginsAndPackages,
  pluginVersionsFromStarManifest: () => pluginVersionsFromStarManifest,
  newPluginId: () => newPluginId,
  convertPluginVersions: () => convertPluginVersions,
  convertToGitUrl: () => convertToGitUrl
});

let _;

module.watch(require("underscore"), {
  default(v) {
    _ = v;
  }

}, 0);
let assert;
module.watch(require("assert"), {
  default(v) {
    assert = v;
  }

}, 1);
let utils;
module.watch(require("../utils/utils.js"), {
  default(v) {
    utils = v;
  }

}, 2);
let buildmessage;
module.watch(require("../utils/buildmessage.js"), {
  default(v) {
    buildmessage = v;
  }

}, 3);
const CORDOVA_ARCH = "web.cordova";
const CORDOVA_PLATFORMS = ['ios', 'android'];
const CORDOVA_DEV_BUNDLE_VERSIONS = {
  'cordova-lib': '7.0.1',
  'cordova-common': '1.5.1',
  'cordova-registry-mapper': '1.1.15'
};
const CORDOVA_PLATFORM_VERSIONS = {
  'android': '6.2.3',
  'ios': '4.5.1'
};
const PLATFORM_TO_DISPLAY_NAME_MAP = {
  'ios': 'iOS',
  'android': 'Android'
};

function ensureDevBundleDependencies() {
  buildmessage.enterJob({
    title: 'Installing Cordova in Meteor tool'
  }, () => {
    require("../cli/dev-bundle-helpers.js").ensureDependencies(CORDOVA_DEV_BUNDLE_VERSIONS);
  });
}

function displayNameForPlatform(platform) {
  return PLATFORM_TO_DISPLAY_NAME_MAP[platform] || platform;
}

;

function displayNamesForPlatforms(platforms) {
  return platforms.map(platform => displayNameForPlatform(platform)).join(', ');
}

function filterPlatforms(platforms) {
  return _.intersection(platforms, CORDOVA_PLATFORMS);
}

function splitPluginsAndPackages(packages) {
  let result = {
    plugins: [],
    packages: []
  };

  for (let pkg of packages) {
    const [namespace, ...rest] = pkg.split(':');

    if (namespace === 'cordova') {
      const name = rest.join(':');
      result.plugins.push(name);
    } else {
      result.packages.push(pkg);
    }
  }

  return result;
}

function pluginVersionsFromStarManifest(star) {
  var cordovaProgram = _.findWhere(star.programs, {
    arch: CORDOVA_ARCH
  });

  return cordovaProgram ? cordovaProgram.cordovaDependencies : {};
}

function newPluginId(id) {
  let oldToNewPluginIds;
  module.watch(require("cordova-registry-mapper"), {
    oldToNew(v) {
      oldToNewPluginIds = v;
    }

  }, 4);
  return oldToNewPluginIds[id];
}

function convertPluginVersions(pluginVersions) {
  assert(pluginVersions);
  buildmessage.assertInJob();
  let newPluginVersions = {};

  _.each(pluginVersions, (version, id) => {
    if (utils.isUrlWithSha(version)) {
      version = convertToGitUrl(version);

      if (!version) {
        // convertToGitUrl will add an error to buildmessage messages
        return;
      }
    }

    const newId = newPluginId(id);

    if (newId) {
      // If the plugin has already been added using the new ID, we do not
      // overwrite the version.
      if (!_.has(pluginVersions, newId)) {
        newPluginVersions[newId] = version;
      }
    } else {
      newPluginVersions[id] = version;
    }
  });

  return newPluginVersions;
}

function convertToGitUrl(url) {
  buildmessage.assertInJob(); // Matches GitHub tarball URLs, like:
  // https://github.com/meteor/com.meteor.cordova-update/tarball/92fe99b7248075318f6446b288995d4381d24cd2

  const match = url.match(/^https?:\/\/github.com\/(.+?)\/(.+?)\/tarball\/([0-9a-f]{40})/);

  if (match) {
    const [, organization, repository, sha] = match; // Convert them to a Git URL

    return `https://github.com/${organization}/${repository}.git#${sha}`; // We only support Git URLs with a SHA reference to guarantee repeatability
    // of builds
  } else if (/\.git#[0-9a-f]{40}/.test(url)) {
    return url;
  } else {
    buildmessage.error(`Meteor no longer supports installing Cordova plugins \
from arbitrary tarball URLs. You can either add a plugin from a Git URL with \
a SHA reference, or from a local path. (Attempting to install from ${url}.)`);
    return null;
  }
}

function displayNameForHostPlatform(platform = process.platform) {
  switch (platform) {
    case 'darwin':
      return "Mac";

    case 'linux':
      return "Linux";

    case 'win32':
      return "Windows";
  }
}
//# sourceMappingURL=index.js.map