(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var global = Package.meteor.global;
var meteorEnv = Package.meteor.meteorEnv;
var meteorInstall = Package.modules.meteorInstall;
var Buffer = Package.modules.Buffer;
var process = Package.modules.process;
var Promise = Package.promise.Promise;

/* Package-scope variables */
var Symbol, Map, Set;

var require = meteorInstall({"node_modules":{"meteor":{"ecmascript-runtime":{"runtime.js":["meteor-ecmascript-runtime",function(require,exports,module){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/ecmascript-runtime/runtime.js                            //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
// TODO Allow just api.mainModule("meteor-ecmascript-runtime");
module.exports = require("meteor-ecmascript-runtime");

///////////////////////////////////////////////////////////////////////

}],"node_modules":{"meteor-ecmascript-runtime":{"package.json":function(require,exports){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// ../../.0.2.11_1.xqwcr4++os+web.browser+web.cordova/npm/node_modul //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
exports.name = "meteor-ecmascript-runtime";
exports.version = "0.2.6";
exports.main = "server.js";

///////////////////////////////////////////////////////////////////////

},"server.js":function(require,exports){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// node_modules/meteor/ecmascript-runtime/node_modules/meteor-ecmasc //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
require("core-js/es6/object");
require("core-js/es6/array");
require("core-js/es6/string");
require("core-js/es6/function");

Symbol = exports.Symbol = require("core-js/es6/symbol");
Map = exports.Map = require("core-js/es6/map");
Set = exports.Set = require("core-js/es6/set");

///////////////////////////////////////////////////////////////////////

}}}}}}},{"extensions":[".js",".json"]});
var exports = require("./node_modules/meteor/ecmascript-runtime/runtime.js");

/* Exports */
if (typeof Package === 'undefined') Package = {};
(function (pkg, symbols) {
  for (var s in symbols)
    (s in pkg) || (pkg[s] = symbols[s]);
})(Package['ecmascript-runtime'] = exports, {
  Symbol: Symbol,
  Map: Map,
  Set: Set
});

})();
