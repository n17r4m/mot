(function(){

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// packages/babel-runtime/babel-runtime.js                                         //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////
                                                                                   //
exports.meteorBabelHelpers = require("meteor-babel-helpers");                      // 1
                                                                                   // 2
// Returns true if a given absolute identifier will be provided at runtime         // 3
// by the babel-runtime package.                                                   // 4
exports.checkHelper = function checkHelper(id) {                                   // 5
  // There used to be more complicated logic here, when the babel-runtime          // 6
  // package provided helper implementations of its own, but now this              // 7
  // function exists just for backwards compatibility.                             // 8
  return false;                                                                    // 9
};                                                                                 // 10
                                                                                   // 11
try {                                                                              // 12
  var babelRuntimeVersion = require("babel-runtime/package.json").version;         // 13
  var regeneratorRuntime = require("babel-runtime/regenerator");                   // 14
} catch (e) {                                                                      // 15
  throw new Error([                                                                // 16
    "The babel-runtime npm package could not be found in your node_modules ",      // 17
    "directory. Please run the following command to install it:",                  // 18
    "",                                                                            // 19
    "  meteor npm install --save babel-runtime",                                   // 20
    ""                                                                             // 21
  ].join("\n"));                                                                   // 22
}                                                                                  // 23
                                                                                   // 24
if (parseInt(babelRuntimeVersion, 10) < 6) {                                       // 25
  throw new Error([                                                                // 26
    "The version of babel-runtime installed in your node_modules directory ",      // 27
    "(" + babelRuntimeVersion + ") is out of date. Please upgrade it by running ",
    "",                                                                            // 29
    "  meteor npm install --save babel-runtime",                                   // 30
    "",                                                                            // 31
    "in your application directory.",                                              // 32
    ""                                                                             // 33
  ].join("\n"));                                                                   // 34
}                                                                                  // 35
                                                                                   // 36
if (regeneratorRuntime &&                                                          // 37
    typeof Promise === "function" &&                                               // 38
    typeof Promise.asyncApply === "function") {                                    // 39
  // If Promise.asyncApply is defined, use it to wrap calls to                     // 40
  // runtime.async so that the entire async function will run in its own           // 41
  // Fiber, not just the code that comes after the first await.                    // 42
  var realAsync = regeneratorRuntime.async;                                        // 43
  regeneratorRuntime.async = function () {                                         // 44
    return Promise.asyncApply(realAsync, regeneratorRuntime, arguments);           // 45
  };                                                                               // 46
}                                                                                  // 47
                                                                                   // 48
/////////////////////////////////////////////////////////////////////////////////////

}).call(this);
