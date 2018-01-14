(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/client.js                                             //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
require("./install-packages.js");                                         // 1
require("./stubs.js");                                                    // 2
require("./process.js");                                                  // 3
require("./reify.js");                                                    // 4
                                                                          // 5
exports.addStyles = require("./css").addStyles;                           // 6
                                                                          // 7
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/css.js                                                //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
var doc = document;                                                       // 1
var head = doc.getElementsByTagName("head").item(0);                      // 2
                                                                          // 3
exports.addStyles = function (css) {                                      // 4
  var style = doc.createElement("style");                                 // 5
                                                                          // 6
  style.setAttribute("type", "text/css");                                 // 7
                                                                          // 8
  // https://msdn.microsoft.com/en-us/library/ms535871(v=vs.85).aspx      // 9
  var internetExplorerSheetObject =                                       // 10
    style.sheet || // Edge/IE11.                                          // 11
    style.styleSheet; // Older IEs.                                       // 12
                                                                          // 13
  if (internetExplorerSheetObject) {                                      // 14
    internetExplorerSheetObject.cssText = css;                            // 15
  } else {                                                                // 16
    style.appendChild(doc.createTextNode(css));                           // 17
  }                                                                       // 18
                                                                          // 19
  return head.appendChild(style);                                         // 20
};                                                                        // 21
                                                                          // 22
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/install-packages.js                                   //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
function install(name, mainModule) {                                      // 1
  var meteorDir = {};                                                     // 2
                                                                          // 3
  // Given a package name <name>, install a stub module in the            // 4
  // /node_modules/meteor directory called <name>.js, so that             // 5
  // require.resolve("meteor/<name>") will always return                  // 6
  // /node_modules/meteor/<name>.js instead of something like             // 7
  // /node_modules/meteor/<name>/index.js, in the rare but possible event
  // that the package contains a file called index.js (#6590).            // 9
                                                                          // 10
  if (typeof mainModule === "string") {                                   // 11
    // Set up an alias from /node_modules/meteor/<package>.js to the main
    // module, e.g. meteor/<package>/index.js.                            // 13
    meteorDir[name + ".js"] = mainModule;                                 // 14
  } else {                                                                // 15
    // back compat with old Meteor packages                               // 16
    meteorDir[name + ".js"] = function (r, e, module) {                   // 17
      module.exports = Package[name];                                     // 18
    };                                                                    // 19
  }                                                                       // 20
                                                                          // 21
  meteorInstall({                                                         // 22
    node_modules: {                                                       // 23
      meteor: meteorDir                                                   // 24
    }                                                                     // 25
  });                                                                     // 26
}                                                                         // 27
                                                                          // 28
// This file will be modified during computeJsOutputFilesMap to include   // 29
// install(<name>) calls for every Meteor package.                        // 30
                                                                          // 31
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/process.js                                            //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
if (! global.process) {                                                   // 1
  try {                                                                   // 2
    // The application can run `npm install process` to provide its own   // 3
    // process stub; otherwise this module will provide a partial stub.   // 4
    global.process = require("process");                                  // 5
  } catch (missing) {                                                     // 6
    global.process = {};                                                  // 7
  }                                                                       // 8
}                                                                         // 9
                                                                          // 10
var proc = global.process;                                                // 11
                                                                          // 12
if (Meteor.isServer) {                                                    // 13
  // Make require("process") work on the server in all versions of Node.  // 14
  meteorInstall({                                                         // 15
    node_modules: {                                                       // 16
      "process.js": function (r, e, module) {                             // 17
        module.exports = proc;                                            // 18
      }                                                                   // 19
    }                                                                     // 20
  });                                                                     // 21
} else {                                                                  // 22
  proc.platform = "browser";                                              // 23
  proc.nextTick = proc.nextTick || Meteor._setImmediate;                  // 24
}                                                                         // 25
                                                                          // 26
if (typeof proc.env !== "object") {                                       // 27
  proc.env = {};                                                          // 28
}                                                                         // 29
                                                                          // 30
var hasOwn = Object.prototype.hasOwnProperty;                             // 31
for (var key in meteorEnv) {                                              // 32
  if (hasOwn.call(meteorEnv, key)) {                                      // 33
    proc.env[key] = meteorEnv[key];                                       // 34
  }                                                                       // 35
}                                                                         // 36
                                                                          // 37
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/reify.js                                              //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
var Module = module.constructor;                                          // 1
var Mp = Module.prototype;                                                // 2
require("reify/lib/runtime").enable(Mp);                                  // 3
Mp.importSync = Mp.importSync || Mp.import;                               // 4
Mp.import = Mp.import || Mp.importSync;                                   // 5
                                                                          // 6
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/server.js                                             //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
require("./install-packages.js");                                         // 1
require("./process.js");                                                  // 2
require("./reify.js");                                                    // 3
                                                                          // 4
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/modules/stubs.js                                              //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
var haveStubs = false;                                                    // 1
try {                                                                     // 2
  require.resolve("meteor-node-stubs");                                   // 3
  haveStubs = true;                                                       // 4
} catch (noStubs) {}                                                      // 5
                                                                          // 6
if (haveStubs) {                                                          // 7
  // When meteor-node-stubs is installed in the application's root        // 8
  // node_modules directory, requiring it here installs aliases for stubs
  // for all Node built-in modules, such as fs, util, and http.           // 10
  require("meteor-node-stubs");                                           // 11
}                                                                         // 12
                                                                          // 13
////////////////////////////////////////////////////////////////////////////

}).call(this);
