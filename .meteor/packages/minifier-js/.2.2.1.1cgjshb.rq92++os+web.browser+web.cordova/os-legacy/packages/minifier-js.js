(function(){

///////////////////////////////////////////////////////////////////////////
//                                                                       //
// packages/minifier-js/minifier.js                                      //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
                                                                         //
var uglify;                                                              // 1
                                                                         // 2
meteorJsMinify = function (source) {                                     // 3
  var result = {};                                                       // 4
  var NODE_ENV = process.env.NODE_ENV || "development";                  // 5
                                                                         // 6
  uglify = uglify || Npm.require("uglify-es");                           // 7
                                                                         // 8
  try {                                                                  // 9
    var uglifyResult = uglify.minify(source, {                           // 10
      compress: {                                                        // 11
        drop_debugger: false,                                            // 12
        unused: false,                                                   // 13
        dead_code: true,                                                 // 14
        global_defs: {                                                   // 15
          "process.env.NODE_ENV": NODE_ENV                               // 16
        }                                                                // 17
      }                                                                  // 18
    });                                                                  // 19
                                                                         // 20
    if (typeof uglifyResult.code === "string") {                         // 21
      result.code = uglifyResult.code;                                   // 22
    } else {                                                             // 23
      throw uglifyResult.error ||                                        // 24
        new Error("unknown uglify.minify failure");                      // 25
    }                                                                    // 26
                                                                         // 27
  } catch (e) {                                                          // 28
    // Although Babel.minify can handle a wider variety of ECMAScript    // 29
    // 2015+ syntax, it is substantially slower than UglifyJS, so we use
    // it only as a fallback.                                            // 31
    if (Babel.getMinifierOptions) {                                      // 32
      var options = Babel.getMinifierOptions({                           // 33
        inlineNodeEnv: NODE_ENV                                          // 34
      });                                                                // 35
      result.code = Babel.minify(source, options).code;                  // 36
    } else {                                                             // 37
      result.code = Babel.minify(source).code;                           // 38
    }                                                                    // 39
  }                                                                      // 40
                                                                         // 41
  return result;                                                         // 42
};                                                                       // 43
                                                                         // 44
///////////////////////////////////////////////////////////////////////////

}).call(this);
