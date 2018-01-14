(function(){

//////////////////////////////////////////////////////////////////////////////////
//                                                                              //
// packages/browser-policy-framing/browser-policy-framing.js                    //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////
                                                                                //
// By adding this package, you get a default policy where only web pages on the
// same origin as your app can frame your app.                                  // 2
//                                                                              // 3
// For controlling which origins can frame this app,                            // 4
// BrowserPolicy.framing.disallow()                                             // 5
// BrowserPolicy.framing.restrictToOrigin(origin)                               // 6
// BrowserPolicy.framing.allowByAnyOrigin()                                     // 7
                                                                                // 8
var defaultXFrameOptions = "SAMEORIGIN";                                        // 9
var xFrameOptions = defaultXFrameOptions;                                       // 10
                                                                                // 11
const BrowserPolicy = require("meteor/browser-policy-common").BrowserPolicy;    // 12
BrowserPolicy.framing = {};                                                     // 13
                                                                                // 14
_.extend(BrowserPolicy.framing, {                                               // 15
  // Exported for tests and browser-policy-common.                              // 16
  _constructXFrameOptions: function () {                                        // 17
    return xFrameOptions;                                                       // 18
  },                                                                            // 19
  _reset: function () {                                                         // 20
    xFrameOptions = defaultXFrameOptions;                                       // 21
  },                                                                            // 22
                                                                                // 23
  disallow: function () {                                                       // 24
    xFrameOptions = "DENY";                                                     // 25
  },                                                                            // 26
  // ALLOW-FROM not supported in Chrome or Safari.                              // 27
  restrictToOrigin: function (origin) {                                         // 28
    // Trying to specify two allow-from throws to prevent users from            // 29
    // accidentally overwriting an allow-from origin when they think they are   // 30
    // adding multiple origins.                                                 // 31
    if (xFrameOptions && xFrameOptions.indexOf("ALLOW-FROM") === 0)             // 32
      throw new Error("You can only specify one origin that is allowed to" +    // 33
                      " frame this app.");                                      // 34
    xFrameOptions = "ALLOW-FROM " + origin;                                     // 35
  },                                                                            // 36
  allowAll: function () {                                                       // 37
    xFrameOptions = null;                                                       // 38
  }                                                                             // 39
});                                                                             // 40
                                                                                // 41
exports.BrowserPolicy = BrowserPolicy;                                          // 42
                                                                                // 43
//////////////////////////////////////////////////////////////////////////////////

}).call(this);
