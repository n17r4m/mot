module.export({
  TEST_FILENAME_REGEXPS: () => TEST_FILENAME_REGEXPS,
  APP_TEST_FILENAME_REGEXPS: () => APP_TEST_FILENAME_REGEXPS,
  isTestFilePath: () => isTestFilePath
});

let _;

module.watch(require("underscore"), {
  default(v) {
    _ = v;
  }

}, 0);
let pathSep;
module.watch(require("../fs/files"), {
  pathSep(v) {
    pathSep = v;
  }

}, 1);
const TEST_FILENAME_REGEXPS = [// "*.test[s].*" or "*.spec[s].*"
/\.tests?./, /\.specs?./];
const APP_TEST_FILENAME_REGEXPS = [// "*.app-tests.*" or "*.app-specs.*"
/\.app-tests?./, /\.app-specs?./];

function isTestFilePath(path) {
  const splitPath = path.split(pathSep); // Does the filename match one of the test filename forms?

  return _.any([...TEST_FILENAME_REGEXPS, ...APP_TEST_FILENAME_REGEXPS], regexp => regexp.test(_.last(splitPath)));
}
//# sourceMappingURL=test-files.js.map