(function(){

/////////////////////////////////////////////////////////////////////////////
//                                                                         //
// packages/npm-bcrypt/wrapper.js                                          //
//                                                                         //
/////////////////////////////////////////////////////////////////////////////
                                                                           //
var assert = require("assert");                                            // 1
                                                                           // 2
// The bcryptjs package has a slightly larger API than the native bcrypt   // 3
// package, so we stick to the smaller API for consistency.                // 4
var methods = {                                                            // 5
  compare: true,                                                           // 6
  compareSync: true,                                                       // 7
  genSalt: true,                                                           // 8
  genSaltSync: true,                                                       // 9
  getRounds: true,                                                         // 10
  hash: true,                                                              // 11
  hashSync: true                                                           // 12
};                                                                         // 13
                                                                           // 14
try {                                                                      // 15
  // If you really need the native `bcrypt` package, then you should       // 16
  // `meteor npm install --save bcrypt` into the node_modules directory in
  // the root of your application.                                         // 18
  var bcrypt = require("bcrypt");                                          // 19
} catch (e) {                                                              // 20
  bcrypt = require("bcryptjs");                                            // 21
  console.warn([                                                           // 22
    "Note: you are using a pure-JavaScript implementation of bcrypt.",     // 23
    "While this implementation will work correctly, it is known to be",    // 24
    "approximately three times slower than the native implementation.",    // 25
    "In order to use the native implementation instead, run",              // 26
    "",                                                                    // 27
    "  meteor npm install --save bcrypt",                                  // 28
    "",                                                                    // 29
    "in the root directory of your application."                           // 30
  ].join("\n"));                                                           // 31
}                                                                          // 32
                                                                           // 33
exports.NpmModuleBcrypt = {};                                              // 34
Object.keys(methods).forEach(function (key) {                              // 35
  assert.strictEqual(typeof bcrypt[key], "function");                      // 36
  exports.NpmModuleBcrypt[key] = bcrypt[key];                              // 37
});                                                                        // 38
                                                                           // 39
/////////////////////////////////////////////////////////////////////////////

}).call(this);
