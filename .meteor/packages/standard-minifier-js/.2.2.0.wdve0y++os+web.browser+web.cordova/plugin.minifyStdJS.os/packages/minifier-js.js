(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var global = Package.meteor.global;
var meteorEnv = Package.meteor.meteorEnv;
var Babel = Package['babel-compiler'].Babel;
var BabelCompiler = Package['babel-compiler'].BabelCompiler;

/* Package-scope variables */
var meteorJsMinify;

(function(){

///////////////////////////////////////////////////////////////////////////
//                                                                       //
// packages/minifier-js/minifier.js                                      //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
                                                                         //
var uglify;

meteorJsMinify = function (source) {
  var result = {};
  var NODE_ENV = process.env.NODE_ENV || "development";

  uglify = uglify || Npm.require("uglify-es");

  try {
    var uglifyResult = uglify.minify(source, {
      compress: {
        drop_debugger: false,
        unused: false,
        dead_code: false,
        global_defs: {
          "process.env.NODE_ENV": NODE_ENV
        }
      }
    });

    if (typeof uglifyResult.code === "string") {
      result.code = uglifyResult.code;
    } else {
      throw uglifyResult.error ||
        new Error("unknown uglify.minify failure");
    }

  } catch (e) {
    // Although Babel.minify can handle a wider variety of ECMAScript
    // 2015+ syntax, it is substantially slower than UglifyJS, so we use
    // it only as a fallback.
    if (Babel.getMinifierOptions) {
      var options = Babel.getMinifierOptions({
        inlineNodeEnv: NODE_ENV
      });
      result.code = Babel.minify(source, options).code;
    } else {
      result.code = Babel.minify(source).code;
    }
  }

  return result;
};

///////////////////////////////////////////////////////////////////////////

}).call(this);


/* Exports */
if (typeof Package === 'undefined') Package = {};
(function (pkg, symbols) {
  for (var s in symbols)
    (s in pkg) || (pkg[s] = symbols[s]);
})(Package['minifier-js'] = {}, {
  meteorJsMinify: meteorJsMinify
});

})();
