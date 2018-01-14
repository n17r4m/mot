(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/es5-shim/server.js                                            //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
require("./import_globals.js");                                           // 1
require("es5-shim/es5-shim.js");                                          // 2
require("./export_globals.js");                                           // 3
                                                                          // 4
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/es5-shim/client.js                                            //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
require("./import_globals.js");                                           // 1
require("es5-shim/es5-shim.js");                                          // 2
require("es5-shim/es5-sham.js");                                          // 3
require("./console.js");                                                  // 4
require("./export_globals.js");                                           // 5
                                                                          // 6
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/es5-shim/console.js                                           //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
var hasOwn = Object.prototype.hasOwnProperty;                             // 1
                                                                          // 2
function wrap(method) {                                                   // 3
  var original = console[method];                                         // 4
  if (original && typeof original === "object") {                         // 5
    // Turn callable console method objects into actual functions.        // 6
    console[method] = function () {                                       // 7
      return Function.prototype.apply.call(                               // 8
        original, console, arguments                                      // 9
      );                                                                  // 10
    };                                                                    // 11
  }                                                                       // 12
}                                                                         // 13
                                                                          // 14
if (typeof console === "object" &&                                        // 15
    // In older Internet Explorers, methods like console.log are actually
    // callable objects rather than functions.                            // 17
    typeof console.log === "object") {                                    // 18
  for (var method in console) {                                           // 19
    // In most browsers, this hasOwn check will fail for all console      // 20
    // methods anyway, but fortunately in IE8 the method objects we care  // 21
    // about are own properties.                                          // 22
    if (hasOwn.call(console, method)) {                                   // 23
      wrap(method);                                                       // 24
    }                                                                     // 25
  }                                                                       // 26
}                                                                         // 27
                                                                          // 28
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/es5-shim/export_globals.js                                    //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
if (global.Date !== Date) {                                               // 1
  global.Date = Date;                                                     // 2
}                                                                         // 3
                                                                          // 4
if (global.parseInt !== parseInt) {                                       // 5
  global.parseInt = parseInt;                                             // 6
}                                                                         // 7
                                                                          // 8
if (global.parseFloat !== parseFloat) {                                   // 9
  global.parseFloat = parseFloat;                                         // 10
}                                                                         // 11
                                                                          // 12
var Sp = String.prototype;                                                // 13
if (Sp.replace !== originalStringReplace) {                               // 14
  // Restore the original value of String#replace, because the es5-shim   // 15
  // reimplementation is buggy. See also import_globals.js.               // 16
  Sp.replace = originalStringReplace;                                     // 17
}                                                                         // 18
                                                                          // 19
////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////
//                                                                        //
// packages/es5-shim/import_globals.js                                    //
//                                                                        //
////////////////////////////////////////////////////////////////////////////
                                                                          //
// Because the es5-{shim,sham}.js code assigns to Date and parseInt,      // 1
// Meteor treats them as package variables, and so declares them as       // 2
// variables in package scope, which causes some references to Date and   // 3
// parseInt in the shim/sham code to refer to those undefined package     // 4
// variables. The simplest solution seems to be to initialize the package
// variables to their appropriate global values.                          // 6
Date = global.Date;                                                       // 7
parseInt = global.parseInt;                                               // 8
parseFloat = global.parseFloat;                                           // 9
                                                                          // 10
// Save the original String#replace method, because es5-shim's            // 11
// reimplementation of it causes problems in markdown/showdown.js.        // 12
// This original method will be restored in export_globals.js.            // 13
originalStringReplace = String.prototype.replace;                         // 14
                                                                          // 15
////////////////////////////////////////////////////////////////////////////

}).call(this);
