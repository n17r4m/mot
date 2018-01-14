(function(){

///////////////////////////////////////////////////////////////////////////
//                                                                       //
// packages/promise/client.js                                            //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
                                                                         //
require("meteor-promise").makeCompatible(                                // 1
  exports.Promise = require("./common.js").Promise                       // 2
);                                                                       // 3
                                                                         // 4
///////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////
//                                                                       //
// packages/promise/common.js                                            //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
                                                                         //
var global = this;                                                       // 1
                                                                         // 2
if (typeof global.Promise === "function") {                              // 3
  exports.Promise = global.Promise;                                      // 4
} else {                                                                 // 5
  exports.Promise = require("promise/lib/es6-extensions");               // 6
}                                                                        // 7
                                                                         // 8
exports.Promise.prototype.done = function (onFulfilled, onRejected) {    // 9
  var self = this;                                                       // 10
                                                                         // 11
  if (arguments.length > 0) {                                            // 12
    self = this.then.apply(this, arguments);                             // 13
  }                                                                      // 14
                                                                         // 15
  self.then(null, function (err) {                                       // 16
    Meteor._setImmediate(function () {                                   // 17
      throw err;                                                         // 18
    });                                                                  // 19
  });                                                                    // 20
};                                                                       // 21
                                                                         // 22
///////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////
//                                                                       //
// packages/promise/promise-tests.js                                     //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
                                                                         //
Tinytest.addAsync("meteor-promise - sanity", function (test, done) {     // 1
  var expectedError = new Error("expected");                             // 2
  Promise.resolve("working").then(function (result) {                    // 3
    test.equal(result, "working");                                       // 4
    throw expectedError;                                                 // 5
  }).catch(function (error) {                                            // 6
    test.equal(error, expectedError);                                    // 7
    if (Meteor.isServer) {                                               // 8
      var Fiber = require("fibers");                                     // 9
      // Make sure the Promise polyfill runs callbacks in a Fiber.       // 10
      test.instanceOf(Fiber.current, Fiber);                             // 11
    }                                                                    // 12
  }).then(done, function (error) {                                       // 13
    test.exception(error);                                               // 14
  });                                                                    // 15
});                                                                      // 16
                                                                         // 17
///////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////
//                                                                       //
// packages/promise/server.js                                            //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
                                                                         //
require("meteor-promise").makeCompatible(                                // 1
  exports.Promise = require("./common.js").Promise,                      // 2
  // Allow every Promise callback to run in a Fiber drawn from a pool of
  // reusable Fibers.                                                    // 4
  require("fibers")                                                      // 5
);                                                                       // 6
                                                                         // 7
///////////////////////////////////////////////////////////////////////////

}).call(this);
